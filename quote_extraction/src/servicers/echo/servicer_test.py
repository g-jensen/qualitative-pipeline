from . import servicer as sut
import pytest

from protos import echo_pb2
from protos import echo_pb2_grpc


@pytest.fixture(scope="module")
def grpc_add_to_server(): return echo_pb2_grpc.add_EchoServicer_to_server


@pytest.fixture(scope="module")
def grpc_servicer(): return sut.EchoServicer()


@pytest.fixture(scope="module")
def grpc_stub_cls(): return echo_pb2_grpc.EchoStub


def test__echo(grpc_stub):
    request = echo_pb2.EchoRequest(content="Hello!")
    responses = grpc_stub.Call(request)

    assert echo_pb2.EchoResponse(content="Hello!") == responses


def test_forcing__echo(grpc_stub):
    request = echo_pb2.EchoRequest(content="Goodbye!")
    responses = grpc_stub.Call(request)

    assert echo_pb2.EchoResponse(content="Goodbye!") == responses
