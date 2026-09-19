from . import log as sut
import logging
from sys import stdout
from . import test_util as tutil
import pytest


def patch_basic_config(mocker):
    return mocker.patch("logging.basicConfig")


def assert_logged(caplog):
    assert len(caplog.records) == 1
    assert "Logging with level: DEBUG" == caplog.records[0].message


def test__init__default(mocker, caplog, monkeypatch):
    log_stub = patch_basic_config(mocker)
    monkeypatch.setenv("RUN_MODE", "")

    with tutil.log_capture(caplog):
        sut.init()
    
    log_stub.assert_called_once_with(stream=stdout, level=logging.DEBUG)
    
    assert_logged(caplog)


def test__init__production(mocker, caplog, monkeypatch):
    log_stub = patch_basic_config(mocker)
    monkeypatch.setenv("RUN_MODE", "production")

    with tutil.log_capture(caplog):
        sut.init()
    
    log_stub.assert_called_once_with(filename="log.txt", level=logging.DEBUG)
    
    assert_logged(caplog)
