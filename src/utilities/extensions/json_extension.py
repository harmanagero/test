def checkjsonnode(jsonnode, jsonresult):
    return jsonnode in jsonresult


def seterrorjson(statusreason, statusmessage):
    return {"status": statusreason, "errorCode": statusmessage}
