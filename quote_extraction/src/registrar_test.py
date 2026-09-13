import registrar as sut
import grpc
import pytest
from unittest.mock import MagicMock
from pytest_mock import MockerFixture
from servicers.quote_extraction import QuoteExtractionServicer

@pytest.fixture
def mocker(pytestconfig: pytest.Config):
    mocker = MockerFixture(pytestconfig)
    yield mocker
    mocker.stopall()


def patch_grpc_quote_extraction(mocker: MockerFixture):
    stub = mocker.stub()
    mocker.patch("registrar.add_QuoteExtractionServicer_to_server", new=stub)
    return stub


def assert_registered_quote_extraction(quote_extraction_stub: MagicMock, mock_server: grpc.Server):
    assert len(quote_extraction_stub.call_args_list) == 1
    (servicer, server) = quote_extraction_stub.call_args_list[0].args
    assert isinstance(servicer, QuoteExtractionServicer)
    assert mock_server == server


def test__register_quote_extraction(mocker):
    quote_extraction_stub = patch_grpc_quote_extraction(mocker)
    mock_server = mocker.MagicMock(spec=grpc.Server)

    sut.register_quote_extraction(mock_server)

    assert_registered_quote_extraction(quote_extraction_stub, mock_server)