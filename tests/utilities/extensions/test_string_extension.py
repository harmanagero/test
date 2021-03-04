import pytest

from src.utilities.extensions.string_extension import isnotnull_whitespaceorempty
from src.utilities.extensions.string_extension import isnull_whitespaceorempty

testdata = [
    (None, False),
    ("", False),
    ("  ", False),
    ("some", True),
    ({}, False),  # dict
    ({"somekey": ""}, True),
    ({"somekey": "somevalue"}, True),
    ((), False),  # tuple
    (set({}), False),  # set
    ([], False),  # list
]


@pytest.mark.parametrize(
    "input, expected",
    testdata,
    ids=[
        "NullCheck",
        "Empty",
        "WhiteSpace",
        "ProperData",
        "EmptyJson",
        "EmptyValue",
        "ProperJson",
        "EmptyTuple",
        "EmptySet",
        "EmptyList",
    ],
)
def test_is_not_nullorempty_on_different_value_returns_as_expected(input, expected):
    assert isnotnull_whitespaceorempty(input) == expected


@pytest.mark.parametrize(
    "input, not_null_result",
    testdata,
    ids=[
        "NullCheck",
        "Empty",
        "WhiteSpace",
        "ProperData",
        "EmptyJson",
        "EmptyValue",
        "ProperJson",
        "EmptyTuple",
        "EmptySet",
        "EmptyList",
    ],
)
def test_is_nullorempty_on_different_value_returns_as_expected(input, not_null_result):
    expected = not not_null_result
    assert isnull_whitespaceorempty(input) == expected
