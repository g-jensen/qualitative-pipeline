import api as sut
import grpc
import pytest
import test_util
from unittest.mock import MagicMock
from pytest_mock import MockerFixture
import registrar_test


@pytest.fixture
def mocker(pytestconfig): return test_util.mocker(pytestconfig)


def server_mock(mocker: MockerFixture):
    return mocker.MagicMock(spec=grpc.Server)


def server_factory_mock(mocker: MockerFixture):
    return mocker.MagicMock(spec=sut.ServerFactory)


def assert_serves(
    mock_server: grpc.Server, mock_server_factory: sut.ServerFactory, quote_extraction_stub: MagicMock, 
    server: grpc.Server, port: int, max_num_workers: int
):
    mock_server_factory.create.assert_called_once_with(max_num_workers)
    registrar_test.assert_registered_quote_extraction(quote_extraction_stub, mock_server)
    mock_server.add_insecure_port.assert_called_once_with(f"[::]:{port}")
    mock_server.start.assert_called_once()
    assert mock_server == server


def pub_test__serve(mocker: MockerFixture, port: int, max_num_workers: int):
    quote_extraction_stub = registrar_test.patch_grpc_quote_extraction(mocker)
    mock_server_factory = server_factory_mock(mocker)
    mock_server = server_mock(mocker)
    mock_server_factory.create.return_value = mock_server
    
    server = sut.serve(mock_server_factory, port, max_num_workers)
    
    assert_serves(
        mock_server, mock_server_factory, quote_extraction_stub,
        server, port, max_num_workers
    )


def test_control__serve(mocker):
    pub_test__serve(mocker, port=8080, max_num_workers=10)


def test_forcing__serve(mocker):
    pub_test__serve(mocker, port=1234, max_num_workers=5)