import logging
from os import getenv
from fastapi import APIRouter, FastAPI
from fastapi.params import Body
from src import __version__
from src.config.configuration_manager import setup_config_manager
from src.config.logger_config import LoggerConfig
from src.middlewares.requestid_middleware import setup_middleware
from src.models.commands.create_agentassignment import CreateAgentAssignmentCommand
from src.models.commands.create_terminate import CreateTerminateCommand
from src.models.commands.get_vehicledata_command import GetVehicleDataCommand
from src.models.domain.enums.internal_status_type import InternalStatusType
from src.models.enums.ctsversion_type import CtsVersion
from src.models.enums.programcode_type import ProgramCode
from src.models.enums.status_type import Status
from src.models.json_api.error_response import JSONApiErrorResponse
from src.models.json_api.success_response import JSONApiSuccessResponse
from src.models.json_api.validation_error import InputValidationError
from src.models.responses.create_agentassignment_response import (
    CreateAgentAssignmentResponse,
)
from src.models.responses.create_save_vehicledata_response import (
    CreateSaveVehicleDataResponse,
)
from src.models.responses.create_terminate_response import CreateTerminateResponse
from src.models.responses.create_vehiclehex_response import CreateVehicleHexData
from src.models.responses.get_vehicledata_response import (
    Brand,
    GetVehicleDataResponse,
    Header,
    Location,
    Vehicle,
)
from src.models.responses.health_check_response import HealthCheckResponse
from src.services.service_manager import setup_service_manager
from src.siriusxm.models.domain.agentassignment import AgentAssignment
from src.siriusxm.models.domain.terminate import Terminate
from src.utilities.errorhandlers.error_responsestatus import handle_error_responsestatus
from src.utilities.errorhandlers.exception_handlers import register_exception_handlers
from src.utilities.logging import LoggerFactory, setup_root_logger
from src.utilities.openapi.open_api import create_custom_openapi_function
from src.vodafone.services.vodafone_service import reformat_msisdn
from starlette.status import HTTP_201_CREATED

app = FastAPI(
    title="ConnectedVehicleAPI",
    version=__version__,
    docs_url=getenv("CUSTOM_DOMAIN_BASE_PATH", "") + "/docs",
)
register_exception_handlers(app)
base_router = APIRouter()
config_manager = setup_config_manager()


logger = logging.getLogger(__name__)
setup_root_logger()
logger_factory = LoggerFactory(config=config_manager.retrieve_config(LoggerConfig))
logger_factory.setup_logger()
setup_middleware(app)


@base_router.get("/health", response_model=JSONApiSuccessResponse[HealthCheckResponse])
async def health():
    """
    Performs a health check of the CV Gateway API
    """
    return JSONApiSuccessResponse[HealthCheckResponse](
        data=HealthCheckResponse(success=True, responsemessage="HealthCheck passed")
    )


@base_router.get(
    "/health/programcode/{programcode}/ctsversion/{ctsversion}",
    response_model=JSONApiSuccessResponse[HealthCheckResponse],
)
async def health(programcode: ProgramCode, ctsversion: CtsVersion):
    """
    Performs a health check of an external service based on programcode and ctsversion
    """
    logger.info(
        "Health: Programcode {}, cts-version {} received for performing the healthcheck".format(
            programcode, ctsversion
        ),
        extra={
            "programcode": programcode,
            "cts-version": ctsversion,
            "action": "Health",
        },
    )

    service_manager = setup_service_manager(programcode, ctsversion)

    dataresponse = service_manager.client_service.health(programcode, ctsversion)

    if dataresponse.status == InternalStatusType.SUCCESS:
        logger.info(
            "Health: Success for programcode:{} cts-version:{}".format(
                programcode, ctsversion
            ),
            extra={
                "programcode": programcode,
                "cts-version": ctsversion,
                "status-code": dataresponse.status,
                "action": "Health",
            },
        )

        return JSONApiSuccessResponse[HealthCheckResponse](
            data=HealthCheckResponse(
                success=True, responsemessage=dataresponse.responsemessage
            )
        )
    else:
        exceptiontype = handle_error_responsestatus(dataresponse.status)
        logger.error(
            "Health: Failed for programcode:{} cts-version:{}, reason:{}".format(
                programcode, ctsversion, dataresponse.responsemessage
            ),
            extra={
                "programcode": programcode,
                "cts-version": ctsversion,
                "status-code": exceptiontype().status_code,
                "action": "Health",
            },
        )
        raise exceptiontype(dataresponse.responsemessage)


@base_router.post("/data", status_code=HTTP_201_CREATED)
async def save_vehicledata(
    request: dict = Body(...),
):  # Get the request as dict object in body
    """
    Saves the Vehicle Data and Return the Hex Data Response back for OCCAS.
    """
    logger.info(
        "Payload received: {}".format(request),
        extra={
            "programcode": request["programcode"] if "programcode" in request else None,
            "cts-version": None,
            "referenceid": request["referenceid"] if "referenceid" in request else None,
            "action": "SaveVehicleData",
        },
    )

    if "programcode" not in request or "referenceid" not in request:
        exceptiontype = handle_error_responsestatus(InternalStatusType.BADREQUEST)
        logger.error(
            "SaveVehicleData: Json payload: {} is invalid".format(
                request,
            ),
            exc_info=True,
            stack_info=True,
            extra={
                "programcode": request["programcode"]
                if "programcode" in request
                else None,
                "cts-version": None,
                "payload": request,
                "referenceid": request["referenceid"]
                if "referenceid" in request
                else None,
                "status-code": exceptiontype().status_code,
                "action": "SaveVehicleData",
            },
        )
        raise exceptiontype(
            "SaveVehicleData: Json payload is invalid. Payload requires programcode and referenceid"
        )

    # service manager should pick service e.g. SiriusXm, FCA correctly.
    service_manager = setup_service_manager(request["programcode"])

    saveresponse = service_manager.client_service.save_vehicledata(request)
    if saveresponse.status == InternalStatusType.SUCCESS:
        # For OCCAS save data, we need to return very simple HEX data response back.
        hexdata = saveresponse.hexvehicledata
        hexdataviewmodel = CreateVehicleHexData(
            VarName=hexdata.VarName, Value=hexdata.Value
        )
        logger.info(
            "SaveVehicleData: Success for Referenceid: {} programcode: {}".format(
                request["referenceid"], request["programcode"]
            ),
            extra={
                "programcode": request["programcode"],
                "cts-version": None,
                "payload": request,
                "referenceid": request["referenceid"],
                "status-code": saveresponse.status,
                "action": "SaveVehicleData",
            },
        )
        return [hexdataviewmodel]
    else:
        exceptiontype = handle_error_responsestatus(saveresponse.status)
        logger.error(
            "SaveVehicleData::Failed for Referenceid:{} status:{} reason:{} programcode:{}".format(
                saveresponse.referenceid,
                saveresponse.status,
                saveresponse.responsemessage,
                saveresponse.programcode,
            ),
            extra={
                "programcode": saveresponse.programcode,
                "cts-version": None,
                "payload": request,
                "referenceid": saveresponse.referenceid,
                "status-code": exceptiontype().status_code,
                "action": "SaveVehicleData",
            },
        )
        raise exceptiontype(saveresponse.responsemessage)


@base_router.post(
    "/agentassignment",
    response_model=JSONApiSuccessResponse[CreateAgentAssignmentResponse],
    status_code=HTTP_201_CREATED,
)
async def create_agentAssignment(agentassignment_input: CreateAgentAssignmentCommand):
    logger.info(
        "AgentAssignment: Payload received for Referenceid: {} programcode: {}".format(
            agentassignment_input.referenceid, agentassignment_input.programcode
        ),
        extra={
            "programcode": agentassignment_input.programcode,
            "referenceid": agentassignment_input.referenceid,
            "action": "AgentAssignment",
        },
    )

    # Model creation.
    agentassignment = AgentAssignment(
        referenceid=agentassignment_input.referenceid,
        isassigned=agentassignment_input.isassigned,
        programcode=agentassignment_input.programcode,
    )

    service_manager = setup_service_manager(agentassignment.programcode)

    # service manager should pick service e.g. SiriusXm, FCA correctly.
    if service_manager.client_service.assign_agent(agentassignment):
        mappedresponse = CreateAgentAssignmentResponse(
            reference_id=agentassignment.response_referenceid,
            agent_assigned=agentassignment.isassigned,
            status=Status.CREATED,
        )

        logger.info(
            "AgentAssignment: Success for Referenceid:{} and programcode:{}".format(
                agentassignment.referenceid, agentassignment.programcode
            ),
            extra={
                "programcode": agentassignment.programcode,
                "referenceid": agentassignment.referenceid,
                "status-code": mappedresponse.status,
                "action": "AgentAssignment",
            },
        )
        return JSONApiSuccessResponse[CreateAgentAssignmentResponse](
            data=mappedresponse
        )
    else:
        exceptiontype = handle_error_responsestatus(agentassignment.responsestatus)
        logger.error(
            "Agentassignment:Failed for Referenceid:{} status:{} reason:{} programcode:{}".format(
                agentassignment.referenceid,
                agentassignment.responsestatus,
                agentassignment.responsemessage,
                agentassignment.programcode,
            ),
            extra={
                "programcode": agentassignment.programcode,
                "referenceid": agentassignment.referenceid,
                "status-code": exceptiontype().status_code,
                "action": "AgentAssignment",
            },
        )
        raise exceptiontype(agentassignment.responsemessage)


@base_router.post(
    "/terminate",
    response_model=JSONApiSuccessResponse[CreateTerminateResponse],
    status_code=HTTP_201_CREATED,
)
async def create_terminate(terminate_input: CreateTerminateCommand):
    logger.info(
        "Terminate: Payload received for Referenceid:{} and programcode:{}".format(
            terminate_input.referenceid, terminate_input.programcode
        ),
        extra={
            "programcode": terminate_input.programcode,
            "referenceid": terminate_input.referenceid,
            "action": "Terminate",
        },
    )
    # model creation.
    terminate = Terminate(
        referenceid=terminate_input.referenceid,
        reasoncode=terminate_input.reasoncode,
        programcode=terminate_input.programcode,
    )

    service_manager = setup_service_manager(terminate.programcode)
    if service_manager.client_service.terminate(terminate):
        mappedresponse = CreateTerminateResponse(
            reference_id=terminate.response_referenceid, status=Status.CREATED
        )
        logger.info(
            "Terminate: Success for Referenceid:{} programcode:{}".format(
                terminate.response_referenceid, terminate.programcode
            ),
            extra={
                "programcode": terminate.programcode,
                "referenceid": terminate.referenceid,
                "status-code": mappedresponse.status,
                "action": "Terminate",
            },
        )
        return JSONApiSuccessResponse[CreateTerminateResponse](data=mappedresponse)
    else:
        exceptiontype = handle_error_responsestatus(terminate.status)
        logger.error(
            "Terminate: Failed for Referenceid:{} status:{} reason:{} programcode:{}".format(
                terminate.referenceid,
                terminate.status,
                terminate.responsemessage,
                terminate.programcode,
            ),
            extra={
                "programcode": terminate.programcode,
                "referenceid": terminate.referenceid,
                "status-code": exceptiontype().status_code,
                "action": "Terminate",
            },
        )
        raise exceptiontype(terminate.responsemessage)


@base_router.get(
    "/data/{id}/programcode/{programcode}",
    response_model=JSONApiSuccessResponse[GetVehicleDataResponse],
)
async def get_vehicledata(id: str, programcode: ProgramCode):
    """
    Get Vehicle  Data end point will return basic vehicle data.
    """
    logger.info(
        "GetVehicleData: Payload received for Id:{} ".format(id, programcode),
        extra={"programcode": programcode, "id": id, "action": "GetVehicleData"},
    )

    # service manager should pick service e.g. SiriusXm, FCA correctly.
    service_manager = setup_service_manager(programcode)
    dataresponse = service_manager.client_service.get_vehicledata(id, programcode)

    if dataresponse.status == InternalStatusType.SUCCESS:
        logger.info(
            "GetVehicleData: Success for Id:{} programcode:{}".format(id, programcode),
            extra={
                "programcode": programcode,
                "id": id,
                "status-code": dataresponse.status,
                "action": "GetVehicleData",
            },
        )

        mappedresponse = GetVehicleDataResponse(
            status=Status.SUCCESS,
            responsemessage="Successfully retrieved",
            header=Header(
                language=dataresponse.language,
                programcode=dataresponse.programcode,
                referenceid=dataresponse.referenceid,
                calldate=dataresponse.calldate,
                calltime=dataresponse.calltime,
                timestamp=dataresponse.timestamp,
            ),
            location=Location(
                latitude=dataresponse.latitude, longitude=dataresponse.longitude
            ),
            vehicle=Vehicle(vin=dataresponse.vin),
        )
        return JSONApiSuccessResponse[GetVehicleDataResponse](data=mappedresponse)
    else:
        exceptiontype = handle_error_responsestatus(dataresponse.status)
        logger.error(
            "GetVehicleData::Failed for id:{} status:{} reason:{} programcode:{}".format(
                id, dataresponse.status, dataresponse.responsemessage, programcode
            ),
            extra={
                "programcode": programcode,
                "id": id,
                "status-code": exceptiontype().status_code,
                "action": "GetVehicleData",
            },
        )
        raise exceptiontype(dataresponse.responsemessage)


@base_router.get(
    "/data/{msisdn}/programcode/{programcode}/ctsversion/{ctsversion}",
    response_model=JSONApiSuccessResponse[GetVehicleDataResponse],
)
async def getvehicledata(msisdn: str, programcode: ProgramCode, ctsversion: CtsVersion):
    """
    Get vehicle data with ctsversion picks a service based on client telemtics version and returns vehicle data for msisdn.
    """
    getvehicle_input = GetVehicleDataCommand(
        msisdn=msisdn, programcode=programcode, ctsversion=ctsversion
    )
    logger.info(
        "GetVehicleData: Payload received for msisdn:{}".format(
            getvehicle_input.msisdn
        ),
        extra={
            "msisdn": getvehicle_input.msisdn,
            "programcode": getvehicle_input.programcode,
            "cts-version": getvehicle_input.ctsversion,
            "action": "GetVehicleData",
        },
    )

    service_manager = setup_service_manager(
        getvehicle_input.programcode, getvehicle_input.ctsversion
    )
    dataresponse = service_manager.client_service.get_vehicledata(
        getvehicle_input.msisdn, getvehicle_input.programcode
    )
    if dataresponse.status == InternalStatusType.SUCCESS:
        logger.info(
            "GetVehicleData: Success for msisdn:{} status:{}".format(
                getvehicle_input.msisdn, dataresponse.status
            ),
            extra={
                "msisdn": getvehicle_input.msisdn,
                "programcode": getvehicle_input.programcode,
                "cts-version": getvehicle_input.ctsversion,
                "status-code": dataresponse.status,
                "action": "GetVehicleData",
            },
        )
        mappedresponse = GetVehicleDataResponse(
            status=Status.SUCCESS,
            responsemessage="Successfully retrieved",
            header=Header(
                msisdn=dataresponse.msisdn,
                programcode=dataresponse.programcode,
                version=getvehicle_input.ctsversion,
                calldate=dataresponse.calldate,
                calltime=dataresponse.calltime,
                timestamp=dataresponse.timestamp,
                odometer=dataresponse.odometer,
                odometerscale=dataresponse.odometerscale,
                countrycode=dataresponse.countrycode,
            ),
            location=Location(
                latitude=dataresponse.latitude,
                longitude=dataresponse.longitude,
                headingdirection=dataresponse.headingdirection,
            ),
            vehicle=Vehicle(
                vin=dataresponse.vin,
                brand=Brand(
                    brandname=dataresponse.brand,
                    modelname=dataresponse.modelname,
                    modelyear=dataresponse.modelyear,
                    modelcode=dataresponse.modelcode,
                    modeldesc=dataresponse.modeldesc,
                ),
                mileage=dataresponse.mileage,
                mileageunit=dataresponse.mileageunit,
            ),
        )
        return JSONApiSuccessResponse[GetVehicleDataResponse](data=mappedresponse)
    else:
        exceptiontype = handle_error_responsestatus(dataresponse.status)
        logger.error(
            "GetVehicleData::Failed for msisdn: {} status: {} reason: {}".format(
                getvehicle_input.msisdn,
                dataresponse.status,
                dataresponse.responsemessage,
            ),
            extra={
                "msisdn": getvehicle_input.msisdn,
                "programcode": getvehicle_input.programcode,
                "cts-version": getvehicle_input.ctsversion,
                "status-code": exceptiontype().status_code,
                "action": "GetVehicleData",
            },
        )

        raise exceptiontype(dataresponse.responsemessage)


@base_router.post(
    "/terminate/{msisdn}/programcode/{programcode}/ctsversion/{ctsversion}",
    response_model=JSONApiSuccessResponse[CreateTerminateResponse],
    status_code=HTTP_201_CREATED,
)
async def terminate(
    msisdn: str,
    programcode: ProgramCode,
    ctsversion: CtsVersion,
    request: dict = Body(...),
):
    """
    Terminate msisdn with ctsversion picks a service based on client telematics version and terminate the call associated with msisdn.
    """
    logger.info(
        "Terminate: Payload received for msisdn:{}".format(msisdn),
        extra={
            "msisdn": msisdn,
            "programcode": programcode,
            "cts-version": ctsversion,
            "payload": request,
            "action": "Terminate",
        },
    )

    service_manager = setup_service_manager(programcode, ctsversion)
    dataresponse = service_manager.client_service.terminate(
        msisdn, programcode, request
    )
    if dataresponse.status == InternalStatusType.SUCCESS:
        mappedresponse = CreateTerminateResponse(msisdn=msisdn, status=Status.CREATED)
        logger.info(
            "Terminate: Success for msisdn:{}".format(msisdn),
            extra={
                "msisdn": msisdn,
                "programcode": programcode,
                "cts-version": ctsversion,
                "payload": request,
                "status-code": mappedresponse.status,
                "action": "Terminate",
            },
        )
        return JSONApiSuccessResponse[CreateTerminateResponse](data=mappedresponse)
    else:
        exceptiontype = handle_error_responsestatus(dataresponse.status)
        logger.error(
            "Terminate: Failed for msisdn:{} status:{} reason:{}".format(
                msisdn, dataresponse.status, dataresponse.responsemessage
            ),
            extra={
                "msisdn": msisdn,
                "programcode": programcode,
                "cts-version": ctsversion,
                "payload": request,
                "status-code": exceptiontype().status_code,
                "action": "Terminate",
            },
        )
        raise exceptiontype(dataresponse.responsemessage)


@base_router.post(
    "/data/{msisdn}/programcode/{programcode}/ctsversion/{ctsversion}",
    response_model=JSONApiSuccessResponse[CreateSaveVehicleDataResponse],
    status_code=HTTP_201_CREATED,
)
async def save_vehicledata(
    msisdn: str,
    programcode: ProgramCode,
    ctsversion: CtsVersion,
    request: dict = Body(...),
):
    """
    Save_VehicleData msisdn with ctsversion picks a service based on client telematics version and saves the vehicle data.
    """
    logger.info(
        "SaveVehicleData: Payload received for msisdn:{} data:{}".format(
            msisdn, request
        ),
        extra={
            "msisdn": msisdn,
            "programcode": programcode,
            "cts-version": ctsversion,
            "action": "SaveVehicleData",
        },
    )

    service_manager = setup_service_manager(programcode, ctsversion)

    saveresponse = service_manager.client_service.save_vehicledata(
        msisdn, programcode, request
    )
    if saveresponse.status == InternalStatusType.SUCCESS:
        mappedresponse = CreateSaveVehicleDataResponse(
            msisdn=msisdn,
            status=Status.CREATED,
            responsemessage=saveresponse.responsemessage,
        )
        logger.info(
            "SaveVehicleData: Success for msisdn:{}".format(msisdn),
            extra={
                "msisdn": msisdn,
                "programcode": programcode,
                "cts-version": ctsversion,
                "status-code": mappedresponse.status,
                "action": "SaveVehicleData",
            },
        )
        return JSONApiSuccessResponse[CreateSaveVehicleDataResponse](
            data=mappedresponse
        )
    else:
        raise save_msisdn_error(
            saveresponse.status,
            saveresponse.responsemessage,
            msisdn,
            programcode,
            ctsversion,
        )


# THIS POST METHOHD IS DEDICATED FOR PORSCHE : NGPCV-396, DONOT RE-PURPOSE IT
@base_router.post(
    "/vehicleinfo", response_model=JSONApiSuccessResponse[CreateSaveVehicleDataResponse]
)
async def save_vehicleinfo(request: dict = Body(...)):
    """
    Save_VehicleData for PORSCHE picks vodafone service based on extracted msisdn and client telematics version from the payload, and saves the vehicle data.
    """
    if (
        "userData" not in request
        or "phoneContact" not in request["userData"]
        or request["userData"]["phoneContact"] is None
    ):
        raise save_msisdn_error(
            InternalStatusType.BADREQUEST,
            "Missing PhoneContact/Msisdn",
            "NotAvailable",
            ProgramCode.PORSCHE,
            CtsVersion.ONE_DOT_ZERO,
        )

    getvehicle_input = GetVehicleDataCommand(
        msisdn=request["userData"]["phoneContact"],
        programcode=ProgramCode.PORSCHE,
        ctsversion=CtsVersion.ONE_DOT_ZERO,
    )

    getvehicle_input.msisdn = reformat_msisdn(getvehicle_input.msisdn)

    logger.info(
        "SaveVehicleData: Payload received for msisdn:{} data:{}".format(
            getvehicle_input.msisdn, request
        ),
        extra={
            "msisdn": getvehicle_input.msisdn,
            "programcode": getvehicle_input.programcode,
            "cts-version": getvehicle_input.ctsversion,
            "action": "SaveVehicleData",
        },
    )

    service_manager = setup_service_manager(
        getvehicle_input.programcode, getvehicle_input.ctsversion
    )

    saveresponse = service_manager.client_service.save_vehicledata(
        getvehicle_input.msisdn, getvehicle_input.programcode, request
    )
    if saveresponse.status == InternalStatusType.SUCCESS:
        mappedresponse = CreateSaveVehicleDataResponse(
            msisdn=getvehicle_input.msisdn,
            status=Status.SUCCESS,
            responsemessage=saveresponse.responsemessage,
        )
        logger.info(
            "SaveVehicleData: Success for msisdn:{}".format(getvehicle_input.msisdn),
            extra={
                "msisdn": getvehicle_input.msisdn,
                "programcode": getvehicle_input.programcode,
                "cts-version": getvehicle_input.ctsversion,
                "status-code": mappedresponse.status,
                "action": "SaveVehicleData",
            },
        )
        return JSONApiSuccessResponse[CreateSaveVehicleDataResponse](
            data=mappedresponse
        )
    else:
        raise save_msisdn_error(
            saveresponse.status,
            saveresponse.responsemessage,
            getvehicle_input.msisdn,
            getvehicle_input.programcode,
            getvehicle_input.ctsversion,
        )


# THIS GET METHOHD IS DEDICATED FOR PORSCHE : NGPCV-530, DONOT RE-PURPOSE IT
@base_router.get(
    "/vehicleinfo",
    response_model=dict,
)
async def getvehicleinfo(phonecontact:str):
    """
    Get vehicle data with ctsversion picks a service based on client telemtics version and returns vehicle data for msisdn.
    """
    getvehicle_input = GetVehicleDataCommand(
        msisdn=phonecontact,
        programcode=ProgramCode.PORSCHE,
        ctsversion=CtsVersion.ONE_DOT_ZERO,
    )
    logger.info(
        "GetVehicleInfo: Payload received for msisdn:{}".format(
            getvehicle_input.msisdn
        ),
        extra={
            "programcode": getvehicle_input.programcode,
            "cts-version": getvehicle_input.ctsversion,
            "action": "GetVehicleInfo",
        },
    )

    service_manager = setup_service_manager(
        getvehicle_input.programcode, getvehicle_input.ctsversion
    )
    dataresponse = service_manager.client_service.get_vehicleinfo(
        getvehicle_input.msisdn
    )
    if dataresponse.status == InternalStatusType.SUCCESS:
        logger.info(
            "GetVehicleInfo: Success for msisdn:{} status:{}".format(
                getvehicle_input.msisdn, dataresponse.status
            ),
            extra={
                "programcode": getvehicle_input.programcode,
                "cts-version": getvehicle_input.ctsversion,
                "status-code": dataresponse.status,
                "action": "GetVehicleInfo",
            },
        )
        
        return dataresponse.JSONData
    else:
        exceptiontype = handle_error_responsestatus(dataresponse.status)
        logger.error(
            "GetVehicleInfo::Failed for msisdn:{} status:{} reason:{}".format(
                getvehicle_input.msisdn,
                dataresponse.status,
                dataresponse.responsemessage,
            ),
            extra={
                "programcode": getvehicle_input.programcode,
                "cts-version": getvehicle_input.ctsversion,
                "status-code": exceptiontype().status_code,
                "action": "GetVehicleInfo",
            },
        )
        raise exceptiontype(dataresponse.responsemessage)


def save_msisdn_error(status, responsemessage, msisdn, programcode, ctsversion):
    exceptiontype = handle_error_responsestatus(status)
    logger.error(
        "SaveVehicleData: Failed for msisdn:{} status:{} reason:{}".format(
            msisdn, status, responsemessage
        ),
        extra={
            "msisdn": msisdn,
            "programcode": programcode,
            "cts-version": ctsversion,
            "status-code": exceptiontype().status_code,
            "action": "SaveVehicleData",
        },
    )
    return exceptiontype(responsemessage)


app.include_router(
    base_router,
    prefix=getenv("CUSTOM_DOMAIN_BASE_PATH", ""),
    responses={
        400: {
            "model": JSONApiErrorResponse[InputValidationError],
            "description": "Invalid Request",
        }
    },
)

app.openapi = create_custom_openapi_function(app)
