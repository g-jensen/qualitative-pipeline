import pytest
import logging
from protos import test_pb2, test_pb2_grpc
import grpc


def log_capture(caplog: pytest.LogCaptureFixture):
    return caplog.at_level(logging.DEBUG)


def logs_by_name(caplog, name):
    return (filter(lambda r: r.name == name, caplog.records))


def list_logs_by_name(caplog, name):
    return list(logs_by_name(caplog,name))


def assert_logged(records, levelname: str, message: str):
    assert len(records) == 1
    assert records[0].levelname == levelname
    assert records[0].message == message


class _TestServicer(test_pb2_grpc.TestServicer):
    def __init__(self, response):
        self.response = response

    def Call(self, request, context: grpc.ServicerContext):
        return self.response


class _TestStreamServicer(test_pb2_grpc.TestStreamServicer):
    def __init__(self, response):
        self.response = response

    def Call(self, request, context: grpc.ServicerContext):
        yield self.response
