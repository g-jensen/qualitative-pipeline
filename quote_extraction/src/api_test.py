from . import api as sut
import grpc
import pytest
from . import test_util as tutil
from unittest.mock import MagicMock
from pytest_mock import MockerFixture
from . import registrar_test
import logging
from typing import Sequence


def server_mock(mocker: MockerFixture):
    return mocker.MagicMock(spec=grpc.Server)


def patch_grpc_server(mocker: MockerFixture):
    server = server_mock(mocker)
    stub = mocker.patch("src.api.create_grpc_server", return_value=server)
    return (stub, server)


def assert_logged(caplog: pytest.LogCaptureFixture, levelname: str, message: str):
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == levelname
    assert caplog.records[0].message == message


def _assert_serves(
    service_stubs: Sequence[tuple[MagicMock, type]], grpc_stub: MagicMock, server_stub: grpc.Server, caplog: pytest.LogCaptureFixture,
    port: int, max_num_workers: int
):
    grpc_stub.assert_called_once_with(max_num_workers)

    registrar_test.assert_registered_services(service_stubs, server_stub)
    
    server_stub.add_insecure_port.assert_called_once_with(f"127.0.0.1:{port}")
    server_stub.start.assert_called_once()
    server_stub.wait_for_termination.assert_called_once()
    
    assert_logged(caplog, "INFO", f"Serving at http://127.0.0.1:{port}")


def setup_state(mocker, caplog):
    (grpc_stub, server_stub) = patch_grpc_server(mocker)
    return (registrar_test.stub_services_to_register(mocker), grpc_stub, server_stub, caplog)


def assert_serves(test_state, port: int, max_num_workers: int):
    (service_stubs, grpc_stub, server_stub, caplog) = test_state
    _assert_serves(
        service_stubs, grpc_stub, server_stub, caplog,
        port, max_num_workers
    )


def test__serve(mocker, caplog):
    test_state = setup_state(mocker, caplog)

    with tutil.log_capture(caplog):
        sut.serve(port=8080, max_num_workers=10)
    
    assert_serves(test_state, port=8080, max_num_workers=10)


def test_forcing__serve(mocker, caplog):
    test_state = setup_state(mocker, caplog)

    with tutil.log_capture(caplog):
        sut.serve(port=1234, max_num_workers=5)

    assert_serves(test_state, port=1234, max_num_workers=5)
