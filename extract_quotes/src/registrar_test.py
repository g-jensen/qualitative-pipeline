from .servicers import extract

from . import registrar as sut
from . import test_util as tutil
import grpc
import pytest
from unittest.mock import MagicMock
from pytest_mock import MockerFixture
from typing import Sequence
from . import stub
import os


def assert_registered_service(service_stubs, mock_server: grpc.Server, **kwargs):
    (service_stub, servicer_stub, servicer_obj) = service_stubs
    assert len(service_stub.call_args_list) == 1
    (servicer, server) = service_stub.call_args_list[0].args
    servicer_stub.assert_called_once_with(**kwargs)
    assert servicer == servicer_obj
    assert mock_server == server


class ExtractionRegistrationTest():
    def __init__(self, mocker: MockerFixture, mock_server, **kwargs):
        self.mocker_server = mock_server

        extract_servicer = object()
        self.extraction_stubs = (
            mocker.patch("protos.extract_pb2_grpc.add_ExtractServicer_to_server"), 
            mocker.patch("src.servicers.extract.ExtractServicer", return_value=extract_servicer),
            extract_servicer
        )

        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.environ.get("RUN_MODE") == "test":
            assert_registered_service(self.extraction_stubs, self.mocker_server, stub_fn=stub.stub_fn)
        else:
            assert_registered_service(self.extraction_stubs, self.mocker_server)
        return False


def registration_tests(mocker: MockerFixture, mock_server):
    return [
        ExtractionRegistrationTest(mocker, mock_server),
    ]


class RegistrationTests():
    def __init__(self, mocker: MockerFixture, mock_server):
        self.services = registration_tests(mocker, mock_server)
    
    def __enter__(self):
        for service in self.services:
            service.__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for service in self.services:
            service.__exit__(exc_type, exc_val, exc_tb)


def test__extract_service_default_mode(mocker, monkeypatch, caplog):
    monkeypatch.setenv("RUN_MODE", "")
    mock_server = mocker.MagicMock(spec=grpc.Server)
    
    with ExtractionRegistrationTest(mocker, mock_server):
        with tutil.log_capture(caplog):
            sut.register_services(sut.services_to_register(), mock_server)

    records = tutil.list_logs_by_name(caplog,sut.__name__)
    tutil.assert_logged(records,"INFO",f"Loading {extract.__name__}")


def test__extract_service_test_mode(mocker, monkeypatch, caplog):
    monkeypatch.setenv("RUN_MODE", "test")
    mock_server = mocker.MagicMock(spec=grpc.Server)

    with ExtractionRegistrationTest(mocker, mock_server):
        with tutil.log_capture(caplog):
            sut.register_services(sut.services_to_register(), mock_server)
    
    records = tutil.list_logs_by_name(caplog,sut.__name__)
    tutil.assert_logged(records,"INFO",f"Loading {extract.__name__} (TEST MODE)")
