import cli as sut
import pytest
import test_util
from pytest_mock import MockerFixture
from unittest.mock import MagicMock
from typer.testing import CliRunner
from typer.testing import Result as TyperResult
from typing import Sequence
import api_test
import registrar_test


@pytest.fixture
def runner(): return CliRunner()


@pytest.fixture
def mocker(pytestconfig): return test_util.mocker(pytestconfig)


def run_patched_app(runner: CliRunner, args: Sequence[str]):
    return runner.invoke(sut.app, args)


def test__cli(runner, mocker, caplog):
    quote_extraction_stub = registrar_test.patch_grpc_quote_extraction(mocker)
    (grpc_stub, server_stub) = api_test.patch_grpc_server(mocker)

    with api_test.log_capture(caplog):
        result = run_patched_app(runner, args=[])
    
    api_test.assert_serves(
        server_stub, grpc_stub, quote_extraction_stub, caplog,
        port=8080, max_num_workers=10
    )
    assert result.exit_code == 0


def test_forcing__cli(runner, mocker, caplog):
    quote_extraction_stub = registrar_test.patch_grpc_quote_extraction(mocker)
    (grpc_stub, server_stub) = api_test.patch_grpc_server(mocker)

    with api_test.log_capture(caplog):
        result = run_patched_app(runner, args=["--port=5050", "--max-workers=5"])
    
    api_test.assert_serves(
        server_stub, grpc_stub, quote_extraction_stub, caplog,
        port=5050, max_num_workers=5
    )
    assert result.exit_code == 0
