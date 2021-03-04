from src.fca.models.domain.vehicle_data import VehicleData


def test_vehicle_data_maserati_brand_assist_should_populate_all_fields():
    save_vehicledata_request_json = generate_valid_brand_assist_maserati_vehicle_data()
    vehicle_data = VehicleData(**save_vehicledata_request_json)
    assert vehicle_data.EventID == save_vehicledata_request_json["EventID"]
    assert (
        vehicle_data.Data.bcallType
        == save_vehicledata_request_json["Data"]["bcallType"]
    )
    assert (
        vehicle_data.Data.customExtension.device
        == save_vehicledata_request_json["Data"]["customExtension"]["device"]
    )
    assert (
        vehicle_data.Data.customExtension.vehicleInfo
        == save_vehicledata_request_json["Data"]["customExtension"]["vehicleInfo"]
    )


def test_vehicle_data_maserati_roadside_assist_should_populate_all_fields():
    save_vehicledata_request_json = (
        generate_valid_roadside_assist_maserati_vehicle_data()
    )
    vehicle_data = VehicleData(**save_vehicledata_request_json)
    assert vehicle_data.EventID == save_vehicledata_request_json["EventID"]
    assert (
        vehicle_data.Data.bcallType
        == save_vehicledata_request_json["Data"]["bcallType"]
    )
    assert (
        vehicle_data.Data.customExtension.vehicleDataUpload.device
        == save_vehicledata_request_json["Data"]["customExtension"][
            "vehicleDataUpload"
        ]["device"]
    )
    assert (
        vehicle_data.Data.customExtension.vehicleDataUpload.vehicleInfo
        == save_vehicledata_request_json["Data"]["customExtension"][
            "vehicleDataUpload"
        ]["vehicleInfo"]
    )


def generate_valid_brand_assist_maserati_vehicle_data():
    return {
        "EventID": "BcallData",
        "Version": "1.0",
        "Timestamp": 1605801545525,
        "Data": {
            "callCenterNumber": "+18449232959",
            "bcallType": "BRAND_ASSIST",
            "callTrigger": "MANUAL",
            "callReason": "DEFAULT",
            "language": "en_US",
            "latitude": 42.53224182128906,
            "longitude": -83.28421020507813,
            "fuelRemaining": 0.0,
            "engineStatus": "STARTED",
            "customExtension": {
                "callCenterNumber": "+18449232959",
                "CallReasonEnum": "DEFAULT",
                "callTriggerEnum": "MANUAL",
                "calltype": "BRAND",
                "daysRemainingForNextService": 0,
                "device": {
                    "deviceType": "ENUM",
                    "deviceOS": "QNX",
                    "headUnitType": "",
                    "manufacturerName": "",
                    "region": "NAFTA",
                    "screenSize": "Five",
                    "tbmSerialNum": "",
                    "tbmPartNum": "",
                    "tbmHardwareVersion": "",
                    "tbmSoftwareVersion": "",
                    "simIccid": "89011704272516122319",
                    "simImsi": "",
                    "simMsisdn": "13234826699",
                    "nadImei": "015395000488103",
                    "nadHardwareVersion": "",
                    "nadSoftwareVersion": "",
                    "nadSerialNum": "",
                    "nadPartNum": "",
                    "wifiMac": "",
                    "huSerialNum": "",
                    "huPartNum": "",
                    "huHardwareVersion": "",
                    "huSoftwareVersion": "",
                    "isHUNavigationPresent": True,
                },
                "distanceRemainingForNextService": 0,
                "errorTellTale": None,
                "fuelRemaining": 0.0,
                "stateofCharge": 0.0,
                "tirePressure": None,
                "vehicleInfo": {
                    "vehicleLocation": {
                        "positionLatitude": 42.53224182128906,
                        "positionLongitude": -83.28421020507813,
                        "estimatedPositionError": 0,
                        "positionAltitude": 0.0,
                        "gpsFixTypeEnum": "ID_FIX_NO_POS",
                        "isGPSFixNotAvailable": False,
                        "estimatedAltitudeError": 0,
                        "positionDirection": 0.0,
                    },
                    "vehicleSpeed": 0.0,
                    "odometer": 0,
                    "engineStatusEnum": "RUN",
                    "language": "en_US",
                    "country": "US",
                    "vehicleType": "PASSENGER_CLASSM1",
                    "vin": "ZN661XUAXMX1007HT",
                    "brand": "MASERATI",
                    "model": "",
                    "year": "",
                },
            },
        },
    }


def generate_valid_roadside_assist_maserati_vehicle_data():
    return {
        "EventID": "BcallData",
        "Version": "1.0",
        "Timestamp": 1606849518918,
        "Data": {
            "callCenterNumber": "+18449232959",
            "bcallType": "ROADSIDE_ASSIST",
            "callTrigger": "MANUAL",
            "callReason": "DEFAULT",
            "language": "en_US",
            "latitude": 42.53224182128906,
            "longitude": -83.28421020507812,
            "fuelRemaining": 0.0,
            "engineStatus": "STARTED",
            "customExtension": {
                "vehicleDataUpload": {
                    "callCenterNumber": "+18449232959",
                    "CallReasonEnum": "DEFAULT",
                    "callTriggerEnum": "MANUAL",
                    "calltype": "BRAND",
                    "daysRemainingForNextService": 0,
                    "device": {
                        "deviceType": "ENUM",
                        "deviceOS": "QNX",
                        "headUnitType": "",
                        "manufacturerName": "",
                        "region": "NAFTA",
                        "screenSize": "Five",
                        "tbmSerialNum": "",
                        "tbmPartNum": "",
                        "tbmHardwareVersion": "",
                        "tbmSoftwareVersion": "",
                        "simIccid": "89011704272519496322",
                        "simImsi": "",
                        "simMsisdn": "13234826699",
                        "nadImei": "015395000737897",
                        "nadHardwareVersion": "",
                        "nadSoftwareVersion": "",
                        "nadSerialNum": "",
                        "nadPartNum": "",
                        "wifiMac": "",
                        "huSerialNum": "",
                        "huPartNum": "",
                        "huHardwareVersion": "",
                        "huSoftwareVersion": "",
                        "isHUNavigationPresent": False,
                    },
                    "distanceRemainingForNextService": 0,
                    "errorTellTale": None,
                    "fuelRemaining": 0.0,
                    "stateofCharge": 0.0,
                    "tirePressure": None,
                    "vehicleInfo": {
                        "vehicleLocation": {
                            "positionLatitude": 42.53224182128906,
                            "positionLongitude": -83.28421020507812,
                            "estimatedPositionError": 0,
                            "positionAltitude": 0.0,
                            "gpsFixTypeEnum": "ID_FIX_NO_POS",
                            "isGPSFixNotAvailable": False,
                            "estimatedAltitudeError": 0,
                            "positionDirection": 0.0,
                        },
                        "vehicleSpeed": 0.0,
                        "odometer": 0,
                        "engineStatusEnum": "RUN",
                        "language": "en_US",
                        "country": "US",
                        "vehicleType": "PASSENGER_CLASSM1",
                        "vin": "ZN661XUAXMX1007HT",
                        "brand": "MASERATI",
                        "model": "",
                        "year": "",
                    },
                }
            },
        },
    }


def test_vehicle_data_jeep_brand_assist_should_populate_all_fields():
    save_vehicledata_request_json = generate_valid_brand_assist_jeep_vehicle_data()
    vehicle_data = VehicleData(**save_vehicledata_request_json)
    assert vehicle_data.EventID == save_vehicledata_request_json["EventID"]
    assert (
        vehicle_data.Data.bcallType
        == save_vehicledata_request_json["Data"]["bcallType"]
    )
    assert (
        vehicle_data.Data.customExtension.device
        == save_vehicledata_request_json["Data"]["customExtension"]["device"]
    )
    assert (
        vehicle_data.Data.customExtension.vehicleInfo
        == save_vehicledata_request_json["Data"]["customExtension"]["vehicleInfo"]
    )


def test_vehicle_data_jeep_roadside_assist_should_populate_all_fields():
    save_vehicledata_request_json = (
        generate_valid_roadside_assist_jeep_vehicle_data()
    )
    vehicle_data = VehicleData(**save_vehicledata_request_json)
    assert vehicle_data.EventID == save_vehicledata_request_json["EventID"]
    assert (
        vehicle_data.Data.bcallType
        == save_vehicledata_request_json["Data"]["bcallType"]
    )
    assert (
        vehicle_data.Data.customExtension.vehicleDataUpload.device
        == save_vehicledata_request_json["Data"]["customExtension"][
            "vehicleDataUpload"
        ]["device"]
    )
    assert (
        vehicle_data.Data.customExtension.vehicleDataUpload.vehicleInfo
        == save_vehicledata_request_json["Data"]["customExtension"][
            "vehicleDataUpload"
        ]["vehicleInfo"]
    )
    assert (
        vehicle_data.Data.customExtension.vehicleDataUpload.errorTellTale
        == save_vehicledata_request_json["Data"]["customExtension"][
            "vehicleDataUpload"
        ]["errorTellTale"]
    )
    assert (
        vehicle_data.Data.customExtension.vehicleDataUpload.tirePressure
        == save_vehicledata_request_json["Data"]["customExtension"][
            "vehicleDataUpload"
        ]["tirePressure"]
    )


def generate_valid_brand_assist_jeep_vehicle_data():
    return {
        "EventID": "BcallData",
        "Version": "1.0",
        "Timestamp": 1606764386353,
        "Data": {
            "callCenterNumber": "+18449232963",
            "bcallType": "BRAND_ASSIST",
            "callTrigger": "MANUAL",
            "callReason": "DEFAULT",
            "language": "en_US",
            "latitude": 42.6812744140625,
            "longitude": -83.21455383300781,
            "fuelRemaining": 0.0,
            "engineStatus": "STARTED",
            "customExtension": {
                "callCenterNumber": "+18449232963",
                "CallReasonEnum": "DEFAULT",
                "callTriggerEnum": "MANUAL",
                "calltype": "BRAND",
                "daysRemainingForNextService": 0,
                "device": {
                    "deviceType": "ENUM",
                    "deviceOS": "QNX",
                    "headUnitType": "",
                    "manufacturerName": "",
                    "region": "NAFTA",
                    "screenSize": "Five",
                    "tbmSerialNum": "",
                    "tbmPartNum": "",
                    "tbmHardwareVersion": "",
                    "tbmSoftwareVersion": "",
                    "simIccid": "89011704272514889067",
                    "simImsi": "",
                    "simMsisdn": "12482026960",
                    "nadImei": "860871040000484",
                    "nadHardwareVersion": "",
                    "nadSoftwareVersion": "",
                    "nadSerialNum": "",
                    "nadPartNum": "",
                    "wifiMac": "",
                    "huSerialNum": "",
                    "huPartNum": "",
                    "huHardwareVersion": "",
                    "huSoftwareVersion": "",
                    "isHUNavigationPresent": False,
                },
                "distanceRemainingForNextService": 0,
                "errorTellTale": None,
                "fuelRemaining": 0.0,
                "stateofCharge": 0.0,
                "tirePressure": None,
                "vehicleInfo": {
                    "vehicleLocation": {
                        "positionLatitude": 42.6812744140625,
                        "positionLongitude": -83.21455383300781,
                        "estimatedPositionError": 0,
                        "positionAltitude": 0.0,
                        "gpsFixTypeEnum": "ID_FIX_NO_POS",
                        "isGPSFixNotAvailable": False,
                        "estimatedAltitudeError": 0,
                        "positionDirection": 0.0,
                    },
                    "vehicleSpeed": 0.0,
                    "odometer": 0,
                    "engineStatusEnum": "RUN",
                    "language": "en_US",
                    "country": "US",
                    "vehicleType": "PASSENGER_CLASSM1",
                    "vin": "1C4RJKBG4M81030HT",
                    "brand": "JEEP",
                    "model": "",
                    "year": "",
                },
            },
        },
    }


def generate_valid_roadside_assist_jeep_vehicle_data():
    return {
        "EventID": "BcallData",
        "Version": "1.0",
        "Timestamp": 1607067376879,
        "Data": {
            "callCenterNumber": "+18449232963",
            "bcallType": "ROADSIDE_ASSIST",
            "callTrigger": "MANUAL",
            "callReason": "DEFAULT",
            "language": "English",
            "latitude": 42.6838677,
            "longitude": -83.2289213,
            "fuelRemaining": 11.636523,
            "engineStatus": "CUSTOM_EXTENSION",
            "customExtension": {
                "vehicleDataUpload": {
                    "callCenterNumber": "+18449232963",
                    "CallReasonEnum": "DEFAULT",
                    "callTriggerEnum": "MANUAL",
                    "calltype": "ASSIST3",
                    "daysRemainingForNextService": 48,
                    "device": {
                        "deviceType": "ENUM",
                        "deviceOS": "QNX",
                        "headUnitType": "",
                        "manufacturerName": "",
                        "region": "NAFTA",
                        "screenSize": "Five",
                        "tbmSerialNum": "",
                        "tbmPartNum": "",
                        "tbmHardwareVersion": "",
                        "tbmSoftwareVersion": "",
                        "simIccid": "698987456963",
                        "simImsi": "",
                        "simMsisdn": "9999954321",
                        "nadImei": "84977388935689",
                        "nadHardwareVersion": "",
                        "nadSoftwareVersion": "",
                        "nadSerialNum": "",
                        "nadPartNum": "",
                        "wifiMac": "",
                        "huSerialNum": "",
                        "huPartNum": "",
                        "huHardwareVersion": "",
                        "huSoftwareVersion": "",
                        "isHUNavigationPresent": False,
                    },
                    "distanceRemainingForNextService": 38057,
                    "errorTellTale": {"isOilPressure": True},
                    "fuelRemaining": 11.636523,
                    "stateofCharge": 66.69174194335938,
                    "tirePressure": {
                        "flTirePressure": 17.227015,
                        "flTireSts": "NORMAL",
                        "frTirePressure": 16.568317,
                        "frTireSts": "NORMAL",
                        "rlTirePressure": 39.452736,
                        "rlTireSts": "NORMAL",
                        "rrTirePressure": 30.417278,
                        "rrTireSts": "NORMAL",
                        "rl2TirePressure": 0.0,
                        "rr2TirePressure": 0.0,
                    },
                    "vehicleInfo": {
                        "vehicleLocation": {
                            "positionLatitude": 42.6838677,
                            "positionLongitude": -83.2289213,
                            "estimatedPositionError": 0,
                            "positionAltitude": 0.0,
                            "gpsFixTypeEnum": "ID_FIX_NO_POS",
                            "isGPSFixNotAvailable": False,
                            "estimatedAltitudeError": 0,
                            "positionDirection": 0.0,
                        },
                        "vehicleSpeed": 0.0,
                        "odometer": 0,
                        "engineStatusEnum": "REQUESTSTART",
                        "language": "English",
                        "country": "GB",
                        "vehicleType": "PASSENGER_CLASSM1",
                        "vin": "3D7KA28CX4G228689",
                        "brand": "Jeep",
                        "model": "",
                        "year": "",
                    },
                }
            },
        },
    }
