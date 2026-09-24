import pytest
import logging


def log_capture(caplog: pytest.LogCaptureFixture):
    return caplog.at_level(logging.DEBUG)


def logs_by_name(caplog, name):
    return (filter(lambda r: r.name == name, caplog.records))


def list_logs_by_name(caplog, name):
    return list(logs_by_name(caplog,name))


def assert_logged(records, levelname: str, message: str):
    assert len(records) == 1
    assert records[0].levelname == levelname
    assert records[0].message == message

