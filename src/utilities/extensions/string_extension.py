def isnotnull_whitespaceorempty(value):
    if type(value) not in (str, dict, tuple, list, set):
        return value is not None and len(str(value).strip()) > 0
    return value is not None and len(value) > 0 and len(str(value).strip()) > 0


def isnull_whitespaceorempty(value):
    return not isnotnull_whitespaceorempty(value)
