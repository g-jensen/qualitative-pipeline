import cli as sut
import pytest
import pytest_mock
from typer.testing import CliRunner


runner = CliRunner()


def test_cli():
    result = runner.invoke(sut.app, ["--port=123"])
    assert result.exit_code == 0
    assert "Serving on port 123\n" == result.output
