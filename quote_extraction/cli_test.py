import cli as sut
import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner
from typer.testing import Result as TyperResult
from typing import Sequence

@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mocker(pytestconfig: pytest.Config):
    mocker = MockerFixture(pytestconfig)
    yield mocker
    mocker.stopall()


def patch_unvicorn(mocker: MockerFixture, stub=None):
    mocker.patch('uvicorn.run', new=stub)


def run_patched_app(runner: CliRunner, mocker: MockerFixture, args: Sequence[str]):
    stub = mocker.stub()
    patch_unvicorn(mocker,stub=stub)
    result = runner.invoke(sut.app, args)
    return (stub, result)


def assert_result_sucess(result: TyperResult):
    assert result.exit_code == 0


def assert_runs_with_port(runner: CliRunner, mocker: MockerFixture, port: int | None, args: Sequence[str]):
    (stub, result) = run_patched_app(runner, mocker, args)

    assert_result_sucess(result)
    assert len(stub.call_args_list) == 1
    assert stub.call_args_list[0].kwargs["port"] == port


def test__cli__runs_app_on_localhost(runner, mocker):
    (stub, result) = run_patched_app(runner, mocker, args=[])

    assert_result_sucess(result)
    assert len(stub.call_args_list) == 1
    assert stub.call_args_list[0].args == ("api:app",)
    assert stub.call_args_list[0].kwargs["host"] == "127.0.0.1"


def test__cli__default_port(runner, mocker):
    assert_runs_with_port(runner, mocker, port=8080, args=[])


def test__cli__custom_port(runner, mocker):
    assert_runs_with_port(runner, mocker, port=1234, args=["--port=1234"])
