from datetime import datetime, timezone

import pytest
from src.utilities.extensions.datetime_extension import (
    convert_utc_timestamp_to_epoch,
    convert_epoch_to_utc_timestamp,
    get_utc_epoch,
)


@pytest.mark.parametrize(
    "epoch_input, expected",
    [(1605744000000, datetime(2020, 11, 19, 0,0,0, 000000, tzinfo=timezone.utc)), (1486684800000, datetime(2017, 2, 10, 0,0,0, 000000, tzinfo=timezone.utc)), (1486741602, datetime(2017, 2, 10, 15,46,42, 000000, tzinfo=timezone.utc))],
)
def test_convert_epoch_to_utc_timestamp_returns_valid_timestamp(epoch_input, expected):
    tmp = convert_epoch_to_utc_timestamp(epoch_input)
    assert tmp == expected


@pytest.mark.parametrize(
    "timestamp_input, expected",
    [(datetime(2020, 11, 19, 0,0,0, 000000), 1605744000000), (datetime(2017, 2, 10, 0,0,0, 000000, tzinfo=timezone.utc), 1486684800000)],
)
def test_convert_utc_timestamp_to_epoch_returns_valid_epoch(timestamp_input, expected):
    epoch = convert_utc_timestamp_to_epoch(timestamp_input)
    assert epoch == expected


def test_get_utc_epoch_returns_valid_utc_timestamp():
    utc_epoch = get_utc_epoch()
    utc_dt = datetime.utcnow()
    assert convert_epoch_to_utc_timestamp(utc_epoch).strftime(
        "%Y-%m-%dT%H:%M:%S"
    ) == utc_dt.strftime("%Y-%m-%dT%H:%M:%S")
