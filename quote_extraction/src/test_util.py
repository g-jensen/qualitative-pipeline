import pytest
import logging


def log_capture(caplog: pytest.LogCaptureFixture):
    return caplog.at_level(logging.DEBUG)
