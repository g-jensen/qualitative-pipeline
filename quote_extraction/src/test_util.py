import pytest
from pytest_mock import MockerFixture
import logging


def _mocker(pytestconfig: pytest.Config):
    mocker = MockerFixture(pytestconfig)
    yield mocker
    mocker.stopall()


def mocker(pytestconfig: pytest.Config):
    return next(_mocker(pytestconfig))


def log_capture(caplog: pytest.LogCaptureFixture):
    return caplog.at_level(logging.DEBUG)