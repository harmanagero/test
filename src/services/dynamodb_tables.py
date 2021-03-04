from typing import Type

from pynamodb.attributes import NumberAttribute
from pynamodb.attributes import UnicodeAttribute
from pynamodb.attributes import BooleanAttribute
from pynamodb.attributes import JSONAttribute
from pynamodb.attributes import UTCDateTimeAttribute
from pynamodb.models import Model
from src.config.dynamo_config import DynamoConfig


class ConnectedVehicleTable(Model):
    class Meta:
        region = "us-east-1"

    request_key = UnicodeAttribute(hash_key=True)
    event_datetime = NumberAttribute(range_key=True)
    programcode = UnicodeAttribute()
    timestamp = UTCDateTimeAttribute()
    referenceid = UnicodeAttribute(default="0")
    vin = UnicodeAttribute(null=True)
    latitude = NumberAttribute(null=True)
    longitude = NumberAttribute(null=True)
    language = UnicodeAttribute(null=True)
    msisdn = UnicodeAttribute(null=True)
    activationtype = UnicodeAttribute(null=True)
    brand = UnicodeAttribute(null=True)
    modelname = UnicodeAttribute(null=True)
    modelyear = UnicodeAttribute(null=True)
    modelcode = UnicodeAttribute(null=True)
    modeldesc = UnicodeAttribute(null=True)
    market = UnicodeAttribute(null=True)
    odometer = NumberAttribute(null=True)
    odometerscale = UnicodeAttribute(null=True)
    headingdirection = UnicodeAttribute(null=True)
    countrycode = UnicodeAttribute(null=True)
    eventid = UnicodeAttribute(null=True)
    servicetype = UnicodeAttribute(null=True)
    altitude = UnicodeAttribute(null=True)
    vehicletype = UnicodeAttribute(null=True)
    enginestatus = UnicodeAttribute(null=True)
    positiondirection = UnicodeAttribute(null=True)
    vehiclespeed = NumberAttribute(null=True)
    callreason = UnicodeAttribute(null=True)
    calltrigger = UnicodeAttribute(null=True)
    mileage = NumberAttribute(null=True)
    mileageunit = UnicodeAttribute(null=True)
    calltype = UnicodeAttribute(null=True)
    flowid = UnicodeAttribute(null=True)
    correlationid = UnicodeAttribute(null=True)
    calldate = UnicodeAttribute(null=True)
    calltime = UnicodeAttribute(null=True)
    phonenumber = UnicodeAttribute(null=True)
    customerfirstname = UnicodeAttribute(null=True)
    customerlastname = UnicodeAttribute(null=True)
    modelcolor = UnicodeAttribute(null=True)
    srnumber = UnicodeAttribute(null=True)
    locationaddress = UnicodeAttribute(null=True)
    locationcity = UnicodeAttribute(null=True)
    locationstate = UnicodeAttribute(null=True)
    locationpostalcode = UnicodeAttribute(null=True)
    locationconfidence = UnicodeAttribute(null=True)
    locationtrueness = UnicodeAttribute(null=True)
    cruisingrange = UnicodeAttribute(null=True)
    ismoving = BooleanAttribute(null=True)
    JSONData = JSONAttribute(null=True)


class ConnectedVehicleSupplementTable(Model):
    class Meta:
        region = "us-east-1"

    request_key = UnicodeAttribute(hash_key=True)
    event_datetime = NumberAttribute(range_key=True)
    programcode = UnicodeAttribute()
    timestamp = UTCDateTimeAttribute()
    callcenternumber = UnicodeAttribute(default="0")
    devicetype = UnicodeAttribute(null=True)
    deviceos = UnicodeAttribute(null=True)
    headunittype = UnicodeAttribute(null=True)
    manufacturername = UnicodeAttribute(null=True)
    region = UnicodeAttribute(null=True)
    screensize = UnicodeAttribute(null=True)
    tbmserialnum = UnicodeAttribute(null=True)
    tbmpartnum = UnicodeAttribute(null=True)
    tbmhardwareversion = UnicodeAttribute(null=True)
    tbmsoftwareversion = UnicodeAttribute(null=True)
    simiccid = NumberAttribute(null=True)
    msisdn = UnicodeAttribute(null=True)
    nadimei = UnicodeAttribute(null=True)
    simimsi = UnicodeAttribute(null=True)
    nadhardwareversion = UnicodeAttribute(null=True)
    nadsoftwareversion = UnicodeAttribute(null=True)
    nadserialnum = UnicodeAttribute(null=True)
    nadpartnum = UnicodeAttribute(null=True)
    wifimac = UnicodeAttribute(null=True)
    huserialnum = UnicodeAttribute(null=True)
    hupartnum = UnicodeAttribute(null=True)
    huhardwareversion = UnicodeAttribute(null=True)
    husoftwareversion = UnicodeAttribute(null=True)
    ishunavigationpresent = BooleanAttribute(null=True)
    distanceremainingfornextservice = NumberAttribute(null=True)
    estimatedpositionerror = NumberAttribute(null=True)
    estimatedaltitudeerror = NumberAttribute(null=True)
    isgpsfixnotavailable = BooleanAttribute(null=True)
    gpsfixtype = UnicodeAttribute(null=True)
    errortelltale = UnicodeAttribute(null=True)
    isoilpressure = BooleanAttribute(null=True)
    fuelremaining = NumberAttribute(null=True)
    stateofcharge = NumberAttribute(null=True)
    tirepressure = NumberAttribute(null=True)
    fltirepressure = NumberAttribute(null=True)
    frtirepressure = NumberAttribute(null=True)
    rltirepressure = NumberAttribute(null=True)
    rrtirepressure = NumberAttribute(null=True)
    rl2tirepressure = NumberAttribute(null=True)
    rr2tirepressure = NumberAttribute(null=True)
    fltirests = UnicodeAttribute(null=True)
    frtirests = UnicodeAttribute(null=True)
    rltirests = UnicodeAttribute(null=True)
    rrtirests = UnicodeAttribute(null=True)
    daysremainingfornextservice = NumberAttribute(null=True)
    registrationnumber = UnicodeAttribute(null=True)
    registrationstatecode = UnicodeAttribute(null=True)
    registrationcountrycode = UnicodeAttribute(null=True)
    crankinhibition = NumberAttribute(null=True)
    ignitionkey = UnicodeAttribute(null=True)
    evbatterypercentage = UnicodeAttribute(null=True)
    fuellevelpercentage = NumberAttribute(null=True)
    range = NumberAttribute(null=True)
    rangeunit = UnicodeAttribute(null=True)
    tirepressureunit = UnicodeAttribute(null=True)
    tirepressurefrontleft = NumberAttribute(null=True)
    tirepressurefrontright = NumberAttribute(null=True)
    tirepressurerearleft = NumberAttribute(null=True)
    tirepressurerearright = NumberAttribute(null=True)


def get_main_table(config: DynamoConfig) -> Type[ConnectedVehicleTable]:
    ConnectedVehicleTable.Meta.table_name = config.table_name
    ConnectedVehicleTable.Meta.host = config.endpoint

    # Create the table
    if not ConnectedVehicleTable.exists():
        ConnectedVehicleTable.create_table(
            read_capacity_units=1,
            write_capacity_units=1,
            billing_mode="PAY_PER_REQUEST",
            wait=True,
        )
    return ConnectedVehicleTable


def get_supplement_table(config: DynamoConfig) -> Type[ConnectedVehicleSupplementTable]:
    ConnectedVehicleSupplementTable.Meta.table_name = config.supplement_table_name
    ConnectedVehicleSupplementTable.Meta.host = config.endpoint

    # Create the table
    if not ConnectedVehicleSupplementTable.exists():
        ConnectedVehicleSupplementTable.create_table(
            read_capacity_units=1,
            write_capacity_units=1,
            billing_mode="PAY_PER_REQUEST",
            wait=True,
        )
    return ConnectedVehicleSupplementTable
