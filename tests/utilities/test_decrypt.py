import base64
from unittest.mock import patch

from pytest import fixture

from src.utilities.decrypt import decrypt_secret


@fixture
def patched_boto3(mock_kms_client):
    with patch("src.utilities.decrypt.boto3", autospec=True) as patched_boto3:
        patched_boto3.client.return_value = mock_kms_client
        yield patched_boto3


# def test_decrypt_secret_calls_as_expected(patched_boto3, mock_kms_client):
#     plaintext = "foo"
#     byte_array = bytes(plaintext, "utf-8")
#     encoded = base64.b64encode(byte_array).decode("utf-8")
#     return_value = {"Plaintext": byte_array}
#     mock_kms_client.decrypt.return_value = return_value
#     response = decrypt_secret(encoded)
#     patched_boto3.client.assert_called_once_with("kms")
#     mock_kms_client.decrypt.assert_called_once_with(CiphertextBlob=byte_array)
#     assert response == plaintext

