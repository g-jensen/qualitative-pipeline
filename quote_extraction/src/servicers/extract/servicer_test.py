from . import servicer as sut
import pytest

from protos import extract_pb2
from protos import extract_pb2_grpc


@pytest.fixture(scope="module")
def grpc_add_to_server(): return extract_pb2_grpc.add_ExtractServicer_to_server


@pytest.fixture(scope="module")
def grpc_servicer(): return sut.ExtractServicer()


@pytest.fixture(scope="module")
def grpc_stub_cls(): return extract_pb2_grpc.ExtractStub


def test__call(grpc_stub):
    request = extract_pb2.ExtractionRequest()
    responses = list(grpc_stub.Call(request))


