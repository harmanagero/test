import yaml
from cerberus import Validator
from src.config.tmna_config import TmnaConfig


def test_tmna_config_should_populate_all_fields():
    tmna_config_json = generate_valid_config_data()
    config_data = TmnaConfig(**tmna_config_json)
    assert config_data == tmna_config_json


def generate_valid_config_data():
    return {
        "base_url": "fooBaseURL",
        "terminate_url": "terminate_url",
        "root_cert": "root_cert",
    }


def generate_tmna_yaml_file_schema():
    return {
        "base_url": {"required": True, "type": "string"},
        "terminate_url": {"required": True, "type": "string"},
        "root_cert": {"required": True, "type": "string"},
    }


def load_Production_yaml():
    with open("config/config.Production.yml", "r") as f:
        return yaml.load(f.read())["tmna"]

def load_QualityAssurance_yaml():
    with open("config/config.QualityAssurance.yml", "r") as f:
        return yaml.load(f.read())["tmna"]

def load_Staging_yaml():
    with open("config/config.Staging.yml", "r") as f:
        return yaml.load(f.read())["tmna"]


def test_tmna_config():
    tmna_yaml_file_schema = generate_tmna_yaml_file_schema()
    v = Validator(tmna_yaml_file_schema)
    assert v.validate(load_Production_yaml(), tmna_yaml_file_schema) == True
    assert v.validate(load_QualityAssurance_yaml(), tmna_yaml_file_schema) == True
    assert v.validate(load_Staging_yaml(), tmna_yaml_file_schema) == True
