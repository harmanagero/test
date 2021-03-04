import yaml
from cerberus import Validator
from src.config.siriusxm_config import SiriusXmConfig


def test_siriusxm_config_should_populate_all_fields():
    siriusxm_config_json = generate_valid_config_data()
    config_data = SiriusXmConfig(**siriusxm_config_json)
    assert config_data == siriusxm_config_json


def generate_valid_config_data():
    return {
        "base_url": "fooBaseURL",
        "root_cert": "fooCERT",
        "wsdl": "fooWSDL",
        "api_key":"abc",
        "raw_apikey":"cde",
    }



def generate_siriusxm_yaml_file_schema():
    return {
        "base_url": {"required": True, "type": "string"},
        "root_cert": {"required": True, "type": "string"},
        "wsdl": {"required": True, "type": "string"},
    }


def load_Production_yaml():
    with open("config/config.Production.yml", "r") as f:
        return yaml.load(f.read())["siriusxm"]

def load_QualityAssurance_yaml():
    with open("config/config.QualityAssurance.yml", "r") as f:
        return yaml.load(f.read())["siriusxm"]

def load_Staging_yaml():
    with open("config/config.Staging.yml", "r") as f:
        return yaml.load(f.read())["siriusxm"]


def test_siriusxm_config():
    siriusxm_yaml_file_schema = generate_siriusxm_yaml_file_schema()
    v = Validator(siriusxm_yaml_file_schema)
    assert v.validate(load_Production_yaml(), siriusxm_yaml_file_schema) == True
    assert v.validate(load_QualityAssurance_yaml(), siriusxm_yaml_file_schema) == True
    assert v.validate(load_Staging_yaml(), siriusxm_yaml_file_schema) == True





# from unittest.mock import patch

# from pydantic import ValidationError
# from pytest import fixture

# from src.config.siriusxm_config import SiriusXmConfig


# @fixture
# def patched_decrypt_secret():
#     with patch(
#         "src.config.siriusxm_config.decrypt_secret", autospec=True
#     ) as patched_decrypt:
#         yield patched_decrypt


# def test_config_works_without_raw_apikey(patched_decrypt_secret):
#     patched_decrypt_secret.return_value = "foo"
#     config = SiriusXmConfig(
#         api_key="fooApiKey",
#         base_url="fooUrl",
#     )
#     patched_decrypt_secret.assert_called_once_with("fooApiKey")
#     assert config.raw_apikey == "foo"


# def test_config_raises_validation_error_if_decrypt_raises_for_apikey(
#     patched_decrypt_secret
# ):
#     patched_decrypt_secret.side_effect = Exception()
#     try:
#         SiriusXmConfig(
#             api_key="fooApiKey",
#             raw_apikey="fooRawApiKey",
#             base_url="fooUrl",
#         )
#     except ValidationError as e:
#         assert "Unable to decrypt api_key" in str(e)
