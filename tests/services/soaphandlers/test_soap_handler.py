import pytest
from mock import patch
from requests import Session

from src.models.exceptions.application_exception import ApplicationException
from src.services.soaphandlers.soap_handler import get_zeepclient

testdata = [
    ("cab.com", True),
    ("bcd.com", True),
    ("abc.com", True),
    ("abc.com", False),
    ("bcd.com", True),
    ("bcd.com", False),
    ("bcd.com", False),
]
invalidinput_testdata = [
    ("", "serviceurl", "somecert", "somekey"),
    (None, "serviceurl", "somecert", "somekey"),
    (" ", "serviceurl", "somecert", "somekey"),
    ("somewsdl", "", "somecert", "somekey"),
    ("somewsdl", None, "somecert", "somekey"),
    ("somewsdl", " ", "somecert", "somekey"),
    ("somewsdl", "someserviceurl", "", "somekey"),
    ("somewsdl", "someserviceurl", None, "somekey"),
    ("somewsdl", "someserviceurl", " ", "somekey"),
    ("somewsdl", "someserviceurl", "somecert", ""),
    ("somewsdl", "someserviceurl", "somecert", None),
    ("somewsdl", "someserviceurl", "somecert", " "),
]
localstore = {}


@pytest.mark.parametrize(
    "expectedresult",
    [True, False, False],
    ids=["initialRequest", "secondRequest", "thirdRequest"],
)
def test_soap_handler_with_same_serviceurl_returns_zeepclient_as_expected(
    expectedresult
):
    with patch("src.services.soaphandlers.soap_handler.Session") as patched_session:
        patched_session.return_value = Session()
        serviceurl = "abc.com"
        client = get_zeepclient(
            "src/config/wsdl/siriusxm.wsdl",
            serviceurl,
            "src/config/certs/corpvtcert.cer",
            "siriusxm_zeepclient",
            localstore,
        )
        assert client.service._binding_options["address"] == serviceurl
        assert len(localstore) == 1
        assert patched_session.called == expectedresult


@pytest.mark.parametrize(
    "serviceUrl, expectedresult",
    testdata,
    ids=[
        "1stRequest",
        "2ndRequest",
        "3rdRequest",
        "4thRequest",
        "5thRequest",
        "6thRequest",
        "7thRequest",
    ],
)
def test_soap_handler_with_different_serviceurl_returns_zeepclient_as_expected(
    serviceUrl, expectedresult
):
    with patch("src.services.soaphandlers.soap_handler.Session") as patched_session:
        patched_session.return_value = Session()
        serviceurl = serviceUrl
        client = get_zeepclient(
            "src/config/wsdl/siriusxm.wsdl",
            serviceurl,
            "src/config/certs/corpvtcert.cer",
            "siriusxm_zeepclient",
            localstore,
        )
        assert client.service._binding_options["address"] == serviceUrl
        assert len(localstore) == 1
        assert patched_session.called == expectedresult


def test_soap_handler_with_input_dictionary_type_missing_should_return_500():
    lcl = ""
    with pytest.raises(Exception) as execinfo:
        get_zeepclient("wsdl", "serviceurl", "rootcert", "siriusxm_zeepclient", lcl)
    assert execinfo.type == ApplicationException
    assert execinfo.value.status_code == 500
    assert (
        execinfo.value.detail
        == "get_zeepclient: Dictionary param missing, please check"
    )


@pytest.mark.parametrize(
    "wsdl, serviceurl, rootcert, keyinput",
    invalidinput_testdata,
    ids=[
        "wsdlEmpty",
        "wsdlNone",
        "wsdlSpace",
        "serviceurlEmpy",
        "serviceurlNone",
        "serviceurlSpace",
        "rootcertEmpty",
        "rootcertNone",
        "rootcertSpace",
        "keyEmpty",
        "keyNone",
        "keySpace",
    ],
)
def test_soap_handler_with_invalid_input_should_return_500(
    wsdl, serviceurl, keyinput, rootcert
):
    with pytest.raises(Exception) as execinfo:
        get_zeepclient(wsdl, serviceurl, rootcert, keyinput, localstore)
    assert execinfo.type == ApplicationException
    assert execinfo.value.status_code == 500
    assert execinfo.value.detail == "get_zeepclient: Input param can't be null or empty"


def test_soap_handler_with_invalid_certificatepath_should_throw_exception():
    try:
        get_zeepclient(
            "src/config/wsdl/siriusxm.wsdl",
            "dddd.com",
            "invalidpath/invalid.cer",
            "siriusxm_zeepclient",
            localstore,
        )
    except Exception as e:
        assert "invalid path: invalidpath/invalid.cer" in e.args[0]
