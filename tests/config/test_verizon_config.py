import yaml
from cerberus import Validator
from src.config.verizon_config import VerizonConfig


def test_verizon_config_should_populate_all_fields():
    verizon_config_json = generate_valid_config_data()
    config_data = VerizonConfig(**verizon_config_json)
    assert config_data == verizon_config_json


def generate_valid_config_data():
    return {
        "base_url": "fooBaseURL",
        "root_cert": "fooCERT",
        "wsdl": "fooWSDL",
        "dynamo_table_name": "fooTable",
        "dynamo_supplement_table_name": "fooSupplementTable",
        "dynamodb_check_enable": False,
        "dynamodb_check_timelimit": 0,
    }


def generate_verizon_yaml_file_schema():
    return {
        "base_url": {"required": True, "type": "string"},
        "dynamo_table_name": {"required": True, "type": "string"},
        "root_cert": {"required": True, "type": "string"},
        "dynamodb_check_enable": {"required": True, "type": "boolean"},
        "dynamodb_check_timelimit": {"required": True, "type": "integer"},
    }


def load_Production_yaml():
    with open("config/config.Production.yml", "r") as f:
        return yaml.load(f.read())["verizon"]


def load_QualityAssurance_yaml():
    with open("config/config.QualityAssurance.yml", "r") as f:
        return yaml.load(f.read())["verizon"]


def load_Staging_yaml():
    with open("config/config.Staging.yml", "r") as f:
        return yaml.load(f.read())["verizon"]


def test_verizon_config():
    verizon_yaml_file_schema = generate_verizon_yaml_file_schema()
    v = Validator(verizon_yaml_file_schema)
    assert v.validate(load_Production_yaml(), verizon_yaml_file_schema) == True
    assert v.validate(load_QualityAssurance_yaml(), verizon_yaml_file_schema) == True
    assert v.validate(load_Staging_yaml(), verizon_yaml_file_schema) == True
