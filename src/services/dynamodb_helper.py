from datetime import datetime, timedelta
from src.models.enums.ctsversion_type import CtsVersion
from src.models.enums.programcode_type import ProgramCode
from src.utilities.extensions.datetime_extension import (
    convert_utc_timestamp_to_epoch,
    get_utc_epoch,
)
from src.utilities.extensions.string_extension import isnotnull_whitespaceorempty


def get_vehicledata_for_config_enabled_client_only(
    self, id: str, programcode: ProgramCode, ctsversion: CtsVersion
):
    try:
        self._logger.info(
            "GetVehicleData: Read Vehicle data from DynamoDB for id: {} programcode: {}".format(
                id, programcode
            ),
            extra={
                "programcode": programcode,
                "id": id,
                "action": "GetVehicleData",
                "cts-version": ctsversion,
            },
        )
        dynamodb_check_timelimit = (
            self._config.dynamodb_check_timelimit
            if isnotnull_whitespaceorempty(self._config.dynamodb_check_timelimit)
            else 0
        )
        if (
            self._config.dynamodb_check_enable
            and dynamodb_check_timelimit > 0
            and isnotnull_whitespaceorempty(id)
        ):
            # Query for Items Matching current timestamp within given time limit and Partition/Sort Key in descending order
            for dataresponse in self._Table.query(
                hash_key=programcode + "-" + id,
                range_key_condition=self._Table.event_datetime.between(
                    convert_utc_timestamp_to_epoch(
                        datetime.utcnow() - timedelta(minutes=dynamodb_check_timelimit)
                    ),
                    get_utc_epoch(),
                ),
                scan_index_forward=False,
                limit=1,
            ):
                if dataresponse:
                    self._logger.info(
                        "GetVehicleData: Successfully retrieved vehicle data from DynamoDB for id: {} programcode: {}".format(
                            id, programcode
                        ),
                        extra={
                            "programcode": programcode,
                            "id": id,
                            "action": "GetVehicleData",
                            "cts-version": ctsversion,
                        },
                    )
                    return dataresponse
                else:
                    return None
            return None
        return None
    except Exception as e:
        self._logger.error(
            "GetVehicleData: Error retrieving data from DynamoDB for id:{} e:{}".format(
                id, e
            ),
            exc_info=True,
            stack_info=True,
            extra={
                "id": id,
                "programcode": programcode,
                "cts-version": ctsversion,
                "action": "GetVehicleData",
            },
        )
        return None
