import yaml
from cerberus import Validator
from src.config.wirelesscar_config import WirelessCarConfig


def test_wirelesscar_config_should_populate_all_fields():
    wirelesscar_config_json = generate_valid_config_data("fooAPIKey")
    config_data = WirelessCarConfig(**wirelesscar_config_json)
    assert config_data == wirelesscar_config_json


def test_wirelesscar_config_on_valid_api_key_input_should_return_wirelesscar_raw_api_key():
    wirelesscar_config_json = generate_valid_config_data("fooAPIKey")
    config_data = WirelessCarConfig(**wirelesscar_config_json)
    assert config_data.wirelesscar_raw_api_key is not None and config_data.wirelesscar_raw_api_key is not ""


def generate_valid_config_data(api_key):
    return {
        "base_url": "fooBaseURL",
        "wirelesscar_api_key": api_key,
        "wirelesscar_raw_api_key": api_key,
        "callcenter_id": "1000",
        "program_id": "2142",
    }



def generate_wirelesscar_yaml_file_schema():
    return {
        "base_url": {"required": True, "type": "string"},
        "wirelesscar_api_key": {"required": True, "nullable": True},
        "callcenter_id": {"required": True, "type": "number"},
        "program_id": {"required": True, "type": "number"},
    }


def load_Production_yaml():
    with open("config/config.Production.yml", "r") as f:
        return yaml.load(f.read())["wirelesscar"]

def load_QualityAssurance_yaml():
    with open("config/config.QualityAssurance.yml", "r") as f:
        return yaml.load(f.read())["wirelesscar"]

def load_Staging_yaml():
    with open("config/config.Staging.yml", "r") as f:
        return yaml.load(f.read())["wirelesscar"]

def test_wirelesscar_config():
    wirelesscar_yaml_file_schema = generate_wirelesscar_yaml_file_schema()
    v = Validator(wirelesscar_yaml_file_schema)
    assert v.validate(load_Production_yaml(), wirelesscar_yaml_file_schema) == True
    assert v.validate(load_QualityAssurance_yaml(), wirelesscar_yaml_file_schema) == True
    assert v.validate(load_Staging_yaml(), wirelesscar_yaml_file_schema) == True 
