import cli as sut
import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner
from typing import Sequence

@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mocker(pytestconfig: pytest.Config):
    mocker = MockerFixture(pytestconfig)
    yield mocker
    mocker.stopall()


def mock_unvicorn(mocker: MockerFixture, stub=None):
    mocker.patch('uvicorn.run', new=stub)


def assert_ran_with_port(runner: CliRunner, mocker: MockerFixture, port: int | None, args: Sequence[str]):
    stub = mocker.stub()
    mock_unvicorn(mocker,stub=stub)
    
    result = runner.invoke(sut.app, args)

    assert result.exit_code == 0
    stub.assert_called_once_with("api:app", host="127.0.0.1", port=port)


def test__cli__default_port(runner, mocker):
    assert_ran_with_port(runner, mocker, port=8080, args=[])


def test__cli__custom_port(runner, mocker):
    assert_ran_with_port(runner, mocker, port=1234, args=["--port=1234"])
