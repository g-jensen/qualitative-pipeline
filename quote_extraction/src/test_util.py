import pytest
from pytest_mock import MockerFixture


def _mocker(pytestconfig: pytest.Config):
    mocker = MockerFixture(pytestconfig)
    yield mocker
    mocker.stopall()


def mocker(pytestconfig: pytest.Config):
    return next(_mocker(pytestconfig))