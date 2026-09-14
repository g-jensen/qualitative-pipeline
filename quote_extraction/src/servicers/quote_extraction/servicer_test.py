from . import servicer as sut
import pytest

from . import quote_extraction_pb2
from . import quote_extraction_pb2_grpc


@pytest.fixture(scope="module")
def grpc_add_to_server():
    return quote_extraction_pb2_grpc.add_QuoteExtractionServicer_to_server


@pytest.fixture(scope="module")
def grpc_servicer():
    return sut.QuoteExtractionServicer()


@pytest.fixture(scope="module")
def grpc_stub_cls():
    return quote_extraction_pb2_grpc.QuoteExtractionStub


def test__quote_extraction(grpc_stub):
    request = quote_extraction_pb2.ExtractionRequest(topic="Burgers", document="I love burgers.", model="claude", min_example_count=5)
    responses = list(grpc_stub.Extract(request))

    assert quote_extraction_pb2.Extraction(content="Hello") == responses[0]
