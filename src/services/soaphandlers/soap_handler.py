from requests import Session
from zeep import Client
from zeep.cache import InMemoryCache
from zeep.transports import Transport

from src.models.exceptions.application_exception import ApplicationException
from src.utilities.extensions.string_extension import isnull_whitespaceorempty


def get_zeepclient(wsdl, serviceurl, rootcert, key, localstore):
    if not isinstance(localstore, dict):
        raise ApplicationException(
            "get_zeepclient: Dictionary param missing, please check"
        )

    if (
        isnull_whitespaceorempty(wsdl)
        or isnull_whitespaceorempty(serviceurl)
        or isnull_whitespaceorempty(key)
        or isnull_whitespaceorempty(rootcert)
    ):
        raise ApplicationException("get_zeepclient: Input param can't be null or empty")

    if key not in localstore.keys():
        setup_zeepclient(wsdl, serviceurl, rootcert, localstore, key)
    else:
        if not localstore[key].service._binding_options["address"] == serviceurl:
            del localstore[key]
            setup_zeepclient(wsdl, serviceurl, rootcert, localstore, key)
    return localstore[key]


def setup_zeepclient(wsdl, serviceurl, rootcert, localstore, key):
    session = Session()
    session.verify = rootcert
    transport = Transport(cache=InMemoryCache(), session=session)
    client = Client(wsdl=wsdl, transport=transport)
    #   Zeep takes the service url from wsdl by default, hence static wsdl demands the below override
    client.service._binding_options["address"] = serviceurl
    localstore[key] = client
