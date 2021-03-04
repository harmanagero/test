from enum import Enum


class Status(str, Enum):
    SUCCESS = 200
    CREATED = 201
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500
    UNKNOWN = 0
    INVALID_STATE_ERROR = 403
    BAD_REQUEST = 400
