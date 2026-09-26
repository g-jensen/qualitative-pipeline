from . import log as sut
import logging
from sys import stdout
from . import test_util as tutil
import pytest
from protos import test_pb2
import uuid
import json
from google.protobuf.json_format import MessageToDict


def patch_basic_config(mocker):
    return mocker.patch("logging.basicConfig")


def assert_logged(caplog, level: str):
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "INFO"
    assert f"Logging with level: {level}" == caplog.records[0].message


def test__init__default(mocker, caplog, monkeypatch):
    log_stub = patch_basic_config(mocker)
    monkeypatch.setenv("RUN_MODE", "")

    with tutil.log_capture(caplog):
        sut.init()
    
    log_stub.assert_called_once_with(stream=stdout, level=logging.DEBUG, force=True)
    
    assert_logged(caplog, "DEBUG")


def test__init__production(mocker, caplog, monkeypatch):
    log_stub = patch_basic_config(mocker)
    monkeypatch.setenv("RUN_MODE", "production")

    with tutil.log_capture(caplog):
        sut.init()
    
    log_stub.assert_called_once_with(stream=stdout, level=logging.INFO, force=True)
    
    assert_logged(caplog, "INFO")


def assert_message_logged(record, message_obj):
    assert record.levelname == "INFO"
    assert json.loads(record.message) == message_obj


def test__interceptor(mocker, caplog):
    interceptor = sut.LogInterceptor()
    response = test_pb2.TestResponse(content="This is my response")
    method = tutil._TestStreamServicer(response).Call
    request = test_pb2.TestRequest(content="This is my request")
    context = {}
    method_name = "TestServicer_Call"
    mock_uuid = uuid.UUID(int=0x12345678)
    uuid_stub = mocker.patch("uuid.uuid1", return_value=mock_uuid)

    with tutil.log_capture(caplog):
        responses = list(interceptor.intercept(method,request,context,method_name))
    
    assert len(caplog.records) == 2
    
    assert_message_logged(caplog.records[0], {
        "uuid": str(mock_uuid),
        "request": MessageToDict(request)
    })
    
    assert_message_logged(caplog.records[1], {
        "uuid": str(mock_uuid),
        "response": MessageToDict(response)
    })

    uuid_stub.assert_called_once()
    assert responses == [response] 

