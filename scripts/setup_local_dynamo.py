import sys

from agero_python_configuration import ConfigManager

sys.path.append("..")

from src.config.dynamo_config import DynamoConfig  # noqa
from src.services.dynamodb_tables import get_main_table, get_supplement_table  # noqa

config_manager = ConfigManager(config_environment="local")
config_manager.register_config(DynamoConfig, "dynamo")
dynamo_config = config_manager.retrieve_config(DynamoConfig)
ConnectedVehicleTable = get_main_table(dynamo_config)
ConnectedVehicleSupplementTable = get_supplement_table(dynamo_config)

if not ConnectedVehicleTable.exists():
    ConnectedVehicleTable.create_table(
        read_capacity_units=1,
        write_capacity_units=1,
        billing_mode="PAY_PER_REQUEST",
        wait=True,
    )

print(ConnectedVehicleTable.describe_table())

if not ConnectedVehicleSupplementTable.exists():
    ConnectedVehicleSupplementTable.create_table(
        read_capacity_units=1,
        write_capacity_units=1,
        billing_mode="PAY_PER_REQUEST",
        wait=True,
    )

print(ConnectedVehicleSupplementTable.describe_table())
