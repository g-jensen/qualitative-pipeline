from . import cli as sut
import pytest
from . import test_util as tutil
from pytest_mock import MockerFixture
from unittest.mock import MagicMock
from typer.testing import CliRunner
from typer.testing import Result as TyperResult
from typing import Sequence
from . import api_test
from . import registrar_test


@pytest.fixture
def runner(): return CliRunner()


def run_patched_app(runner: CliRunner, args: Sequence[str]):
    return runner.invoke(sut.app, args)


def test__cli(runner, mocker, caplog):
    api_test_state = api_test.setup_state(mocker, caplog)

    with tutil.log_capture(caplog):
        result = run_patched_app(runner, args=[])
    
    api_test.assert_serves(api_test_state, port=8080, max_num_workers=10)
    assert result.exit_code == 0


def test_forcing__cli(runner, mocker, caplog):
    api_test_state = api_test.setup_state(mocker, caplog)

    with tutil.log_capture(caplog):
        result = run_patched_app(runner, args=["--port=5050", "--max-workers=5"])
    
    api_test.assert_serves(api_test_state, port=5050, max_num_workers=5)
    assert result.exit_code == 0
