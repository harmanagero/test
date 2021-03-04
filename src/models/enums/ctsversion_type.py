from enum import Enum


class CtsVersion(str, Enum):
    """
    Client Telematics System version.
    """

    ONE_DOT_ZERO = "1.0"
    TWO_DOT_ZERO = "2.0"
