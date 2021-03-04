from mangum import Mangum

from src.api.api import app
from src.handler import handler


def test_handler_is_configured_mangum():
    assert isinstance(handler, Mangum)
    assert handler.app is app
