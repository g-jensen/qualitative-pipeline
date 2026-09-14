import api as sut
import grpc
import pytest
import test_util as tutil
from unittest.mock import MagicMock
from pytest_mock import MockerFixture
import registrar_test
import logging


@pytest.fixture
def mocker(pytestconfig): return tutil.mocker(pytestconfig)


def server_mock(mocker: MockerFixture):
    return mocker.MagicMock(spec=grpc.Server)


def patch_grpc_server(mocker: MockerFixture):
    server = server_mock(mocker)
    stub = mocker.patch("api.create_grpc_server", return_value=server)
    return (stub, server)


def assert_logged(caplog: pytest.LogCaptureFixture, levelname: str, message: str):
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == levelname
    assert caplog.records[0].message == message


def assert_serves(
    server_stub: grpc.Server, grpc_stub: MagicMock, quote_extraction_stub: MagicMock, caplog: pytest.LogCaptureFixture,
    port: int, max_num_workers: int
):
    grpc_stub.assert_called_once_with(max_num_workers)
    registrar_test.assert_registered_quote_extraction(quote_extraction_stub, server_stub)
    server_stub.add_insecure_port.assert_called_once_with(f"127.0.0.1:{port}")
    server_stub.start.assert_called_once()
    server_stub.wait_for_termination.assert_called_once()
    
    assert_logged(caplog, "INFO", f"Serving at http://127.0.0.1:{port}")


def test__serve(mocker, caplog):
    quote_extraction_stub = registrar_test.patch_grpc_quote_extraction(mocker)
    (grpc_stub, server_stub) = patch_grpc_server(mocker)

    with tutil.log_capture(caplog):
        sut.serve(port=8080, max_num_workers=10)
    
    assert_serves(
        server_stub, grpc_stub, quote_extraction_stub, caplog,
        port=8080, max_num_workers=10
    )


def test_forcing__serve(mocker, caplog):
    quote_extraction_stub = registrar_test.patch_grpc_quote_extraction(mocker)
    (grpc_stub, server_stub) = patch_grpc_server(mocker)

    with tutil.log_capture(caplog):
        sut.serve(port=1234, max_num_workers=5)

    assert_serves(
        server_stub, grpc_stub, quote_extraction_stub, caplog,
        port=1234, max_num_workers=5
    )
