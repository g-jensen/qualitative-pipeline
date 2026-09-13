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


def patch_grpc_server(mocker: MockerFixture):
    server = server_mock(mocker)
    stub = mocker.patch("api.create_grpc_server", return_value=server)
    return (stub, server)


def assert_serves(
    server_stub: grpc.Server, grpc_stub: MagicMock, quote_extraction_stub: MagicMock, 
    port: int, max_num_workers: int
):
    grpc_stub.assert_called_once_with(max_num_workers)
    registrar_test.assert_registered_quote_extraction(quote_extraction_stub, server_stub)
    server_stub.add_insecure_port.assert_called_once_with(f"[::]:{port}")
    server_stub.start.assert_called_once()
    server_stub.wait_for_termination.assert_called_once()


def test__serve(mocker):
    quote_extraction_stub = registrar_test.patch_grpc_quote_extraction(mocker)
    (grpc_stub, server_stub) = patch_grpc_server(mocker)

    sut.serve(port=8080, max_num_workers=10)
    
    assert_serves(
        server_stub, grpc_stub, quote_extraction_stub,
        port=8080, max_num_workers=10
    )


def test_forcing__serve(mocker):
    quote_extraction_stub = registrar_test.patch_grpc_quote_extraction(mocker)
    (grpc_stub, server_stub) = patch_grpc_server(mocker)

    sut.serve(port=1234, max_num_workers=5)
    
    assert_serves(
        server_stub, grpc_stub, quote_extraction_stub,
        port=1234, max_num_workers=5
    )
