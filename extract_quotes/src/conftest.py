import pytest
from pytest_mock import MockerFixture


@pytest.fixture
def mocker(pytestconfig):
    m = MockerFixture(pytestconfig)
    yield m
    m.stopall()
