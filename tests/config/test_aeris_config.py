import yaml
from cerberus import Validator
from src.config.aeris_config import AerisConfig


def test_aeris_config_should_populate_all_fields():
    aeris_config_json = generate_valid_config_data()
    config_data = AerisConfig(**aeris_config_json)
    assert config_data == aeris_config_json


def generate_valid_config_data():
    return {
        "base_url": "fooBaseURL",
        "root_cert": "fooCERT",
        "dynamo_table_name": "fooTable",
        "dynamodb_check_enable": False,
        "dynamodb_check_timelimit": 0,
    }


def generate_aeris_yaml_file_schema():
    return {
        "base_url": {"required": True, "type": "string"},
        "dynamo_table_name": {"required": True, "type": "string"},
        "root_cert": {"required": True, "type": "string"},
        "dynamodb_check_enable": {"required": True, "type": "boolean"},
        "dynamodb_check_timelimit": {"required": True, "type": "integer"},
    }


def load_Production_yaml():
    with open("config/config.Production.yml", "r") as f:
        return yaml.load(f.read())["aeris"]


def load_QualityAssurance_yaml():
    with open("config/config.QualityAssurance.yml", "r") as f:
        return yaml.load(f.read())["aeris"]


def load_Staging_yaml():
    with open("config/config.Staging.yml", "r") as f:
        return yaml.load(f.read())["aeris"]


def test_aeris_config():
    aeris_yaml_file_schema = generate_aeris_yaml_file_schema()
    v = Validator(aeris_yaml_file_schema)
    assert v.validate(load_Production_yaml(), aeris_yaml_file_schema) == True
    assert v.validate(load_QualityAssurance_yaml(), aeris_yaml_file_schema) == True
    assert v.validate(load_Staging_yaml(), aeris_yaml_file_schema) == True
