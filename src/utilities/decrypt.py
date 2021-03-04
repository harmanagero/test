# import base64
# import json
# import logging
# import boto3
# logger = logging.getLogger()
# logger.setLevel("DEBUG")


def decrypt_secret(encrypted: str) -> str:
    return encrypted
    # client = boto3.client("kms")
    # logger.info("test key: {}".format(encrypted))

    # Decrypts secret using the associated KMS CMK.
    # Depending on whether the secret is a string or binary, one of these fields will be populated.
    # if "SecretString" in encrypted:
    #     secret = encrypted["SecretString"]
    #     return json.loads(secret)["api_key"]
    # else:
    #     decoded_binary_secret = base64.b64decode(encrypted["SecretBinary"])
    #     decrypt_response = client.decrypt(decoded_binary_secret)
    #     return decrypt_response["Plaintext"].decode("utf-8")

    # decrypt_response = client.decrypt(CiphertextBlob=base64.b64decode(encrypted))
    # return decrypt_response["Plaintext"].decode("utf-8")
