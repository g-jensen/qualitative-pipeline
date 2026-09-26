from . import api as sut
import grpc
import pytest
from . import test_util as tutil
from unittest.mock import MagicMock
from pytest_mock import MockerFixture
from . import registrar_test
import logging
from typing import Sequence
from concurrent import futures
from . import log


def server_mock(mocker: MockerFixture):
    return mocker.MagicMock(spec=grpc.Server)


def patch_grpc_server(mocker: MockerFixture):
    server = server_mock(mocker)
    stub = mocker.patch("grpc.server", return_value=server)
    return (stub, server)


def assert_grpc_call(grpc_stub: MagicMock, max_num_workers: int):
    assert len(grpc_stub.call_args_list) == 1
    args = grpc_stub.call_args_list[0].kwargs
    assert args["thread_pool"]._max_workers == max_num_workers
    (log_interceptor,) = args["interceptors"]
    assert isinstance(log_interceptor, log.LogInterceptor)


def _assert_serves(
    grpc_stub: MagicMock, server_stub: grpc.Server, caplog: pytest.LogCaptureFixture,
    port: int, max_num_workers: int
):
    assert_grpc_call(grpc_stub, max_num_workers)

    server_stub.add_insecure_port.assert_called_once_with(f"127.0.0.1:{port}")
    server_stub.start.assert_called_once()
    server_stub.wait_for_termination.assert_called_once()
    
    records = tutil.list_logs_by_name(caplog,sut.__name__)
    tutil.assert_logged(records, "INFO", f"Serving at http://127.0.0.1:{port}")


def setup_state(mocker, caplog):
    (grpc_stub, server_stub) = patch_grpc_server(mocker)
    return (grpc_stub, server_stub, caplog)


def assert_serves(test_state, port: int, max_num_workers: int):
    (grpc_stub, server_stub, caplog) = test_state
    _assert_serves(
        grpc_stub, server_stub, caplog,
        port, max_num_workers
    )


def test__serve(mocker, caplog):
    test_state = setup_state(mocker, caplog)
    (_, server_stub, _) = test_state

    with registrar_test.RegistrationTests(mocker, server_stub):
        with tutil.log_capture(caplog):
            sut.serve(port=8080, max_num_workers=10)
    
    assert_serves(test_state, port=8080, max_num_workers=10)


def test_forcing__serve(mocker, caplog):
    test_state = setup_state(mocker, caplog)
    (_, server_stub, _) = test_state

    with registrar_test.RegistrationTests(mocker, server_stub):
        with tutil.log_capture(caplog):
            sut.serve(port=1234, max_num_workers=5)

    assert_serves(test_state, port=1234, max_num_workers=5)
