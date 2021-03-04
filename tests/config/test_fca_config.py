import yaml
from cerberus import Validator
from src.config.fca_config import FcaConfig


def test_fca_config_should_populate_all_fields():
    fca_config_json = generate_valid_config_data("fooAPIKey")
    config_data = FcaConfig(**fca_config_json)
    assert config_data == fca_config_json


def test_fca_config_on_valid_api_key_input_should_return_raw_api_key():
    fca_config_json = generate_valid_config_data("fooAPIKey")
    config_data = FcaConfig(**fca_config_json)
    assert config_data.raw_api_key is not None and config_data.raw_api_key is not ""


def generate_valid_config_data(api_key):
    return {
        "base_url": "fooBaseURL",
        "api_key": api_key,
        "raw_api_key": api_key,
        "dynamo_table_name": "fooTable",
        "dynamo_supplement_table_name": "fooSupplementTable",
        "bcall_data_url": "fooBcallURL",
        "terminate_bcall_url": "fooTerminateURL",
        "max_retries": 3,
        "delay_for_each_retry": 1,
        "max_ani_length": 11,
        "api_gateway_base_path": "foopath",
        "root_cert": "fooCERT",
    }


def generate_fca_yaml_file_schema():
    return {
        "base_url": {
            "required": True,
            "type": "string",
        },
        "dynamo_table_name": {
            "required": True,
            "type": "string",
        },
        "dynamo_supplement_table_name": {
            "required": True,
            "type": "string",
        },
        "api_key": {
            "required": True,
            "nullable": True,
        },
        "bcall_data_url": {
            "required": True,
            "type": "string",
        },
        "terminate_bcall_url": {
            "required": True,
            "type": "string",
        },
        "max_retries": {
            "required": True,
            "type": "number",
        },
        "delay_for_each_retry": {
            "required": True,
            "type": "number",
        },
        "max_ani_length": {
            "required": True,
            "type": "number",
        },
        "api_gateway_base_path": {
            "required": True,
            "type": "string",
        },
        "root_cert": {
            "required": True,
            "type": "string",
        },
    }


def load_Production_yaml():
    with open("config/config.Production.yml", "r") as f:
        return yaml.load(f.read())["fca"]


def load_QualityAssurance_yaml():
    with open("config/config.QualityAssurance.yml", "r") as f:
        return yaml.load(f.read())["fca"]


def load_Staging_yaml():
    with open("config/config.Staging.yml", "r") as f:
        return yaml.load(f.read())["fca"]


def test_fca_config():
    fca_yaml_file_schema = generate_fca_yaml_file_schema()
    v = Validator(fca_yaml_file_schema)
    assert v.validate(load_Production_yaml(), fca_yaml_file_schema) == True
    assert v.validate(load_QualityAssurance_yaml(), fca_yaml_file_schema) == True
    assert v.validate(load_Staging_yaml(), fca_yaml_file_schema) == True
