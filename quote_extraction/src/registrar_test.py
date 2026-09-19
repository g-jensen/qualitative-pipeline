from .servicers.echo import EchoServicer
from .servicers.extract import ExtractServicer

from . import registrar as sut
import grpc
import pytest
from unittest.mock import MagicMock
from pytest_mock import MockerFixture
from typing import Sequence


def stub_services_to_register(mocker: MockerFixture):
    return [
        (mocker.patch("protos.echo_pb2_grpc.add_EchoServicer_to_server"), EchoServicer),
        (mocker.patch("protos.extract_pb2_grpc.add_ExtractServicer_to_server"), ExtractServicer)
    ]


def assert_registered_service(service_stub: MagicMock, mock_server: grpc.Server, service_type: type):
    assert len(service_stub.call_args_list) == 1
    (servicer, server) = service_stub.call_args_list[0].args
    assert isinstance(servicer, service_type)
    assert mock_server == server


def assert_registered_services(service_stubs: Sequence[tuple[MockerFixture,type]], server: grpc.Server):
    for (service_stub, service_type) in service_stubs:
        assert_registered_service(service_stub, server, service_type)


def test__service_registration(mocker):
    mock_server = mocker.MagicMock(spec=grpc.Server)
    service_stubs = stub_services_to_register(mocker)

    sut.register_services(sut.services_to_register(), mock_server)

    assert_registered_services(service_stubs, mock_server)