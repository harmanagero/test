from unittest.mock import patch

import pytest

from src.config.dynamo_config import DynamoConfig
from src.services.dynamodb_tables import get_main_table
from src.services.dynamodb_tables import get_supplement_table


@pytest.fixture
def patched_exists():
    with patch(
        "src.services.dynamodb_tables.ConnectedVehicleTable.exists"
    ) as patched_cv_exists:
        yield patched_cv_exists


@pytest.fixture
def patched_createtable():
    with patch(
        "src.services.dynamodb_tables.ConnectedVehicleTable.create_table"
    ) as patched_cv_createtable:
        yield patched_cv_createtable


def test_get_main_table_should_set_table_name_if_present(patched_exists):
    table_name = "fooTable"
    patched_exists.return_value = True
    config = DynamoConfig(table_name=table_name)
    table = get_main_table(config)
    assert table.Meta.table_name == table_name


def test_get_main_table_should_createtable_if_table_not_exist(
    patched_exists, patched_createtable
):
    table_name = "fooTable"
    patched_exists.return_value = False
    config = DynamoConfig(table_name=table_name)
    table = get_main_table(config)
    assert patched_createtable.called is True
    assert table is not None


def test_get_main_table_should_set_host_if_present(patched_exists):
    host = "fooHost"
    patched_exists.return_value = True
    config = DynamoConfig(table_name="whatever", endpoint=host)
    table = get_main_table(config)
    assert table.Meta.host == host


def test_get_main_table_host_should_be_none_if_not_present(patched_exists):
    config = DynamoConfig(table_name="whatever")
    patched_exists.return_value = True
    table = get_main_table(config)
    assert table.Meta.host is None


@pytest.fixture
def patched_supplement_exists():
    with patch(
        "src.services.dynamodb_tables.ConnectedVehicleSupplementTable.exists"
    ) as patched_cv_exists:
        yield patched_cv_exists


@pytest.fixture
def patched_supplement_createtable():
    with patch(
        "src.services.dynamodb_tables.ConnectedVehicleSupplementTable.create_table"
    ) as patched_cv_st_createtable:
        yield patched_cv_st_createtable


def test_get_supplement_table_should_set_table_name_if_present(
    patched_supplement_exists
):
    table_name = "fooTable"
    patched_supplement_exists.return_value = True
    config = DynamoConfig(supplement_table_name=table_name)
    table = get_supplement_table(config)
    assert table.Meta.table_name == table_name


def test_get_supplement_table_should_createtable_if_table_not_exist(
    patched_supplement_exists, patched_supplement_createtable
):
    table_name = "fooTable"
    patched_supplement_exists.return_value = False
    config = DynamoConfig(supplement_table_name=table_name)
    table = get_supplement_table(config)
    assert patched_supplement_createtable.called is True
    assert table is not None


def test_get_supplement_table_should_set_host_if_present(patched_supplement_exists):
    host = "fooHost"
    patched_supplement_exists.return_value = True
    config = DynamoConfig(supplement_table_name="whatever", endpoint=host)
    table = get_supplement_table(config)
    assert table.Meta.host == host


def test_get_supplement_table_host_should_be_none_if_not_present(
    patched_supplement_exists
):
    config = DynamoConfig(supplement_table_name="whatever")
    patched_supplement_exists.return_value = True
    table = get_supplement_table(config)
    assert table.Meta.host is None
