from protos import echo_pb2_grpc
from .servicers.echo import EchoServicer

from protos import extract_pb2_grpc
from .servicers.extract import ExtractServicer

import grpc
from typing import Callable


def services_to_register():
    return [
        (echo_pb2_grpc.add_EchoServicer_to_server, EchoServicer()),
        (extract_pb2_grpc.add_ExtractServicer_to_server, ExtractServicer()),
    ]


def register_services(services: tuple[Callable, object], server: grpc.Server):
    for (add_fn, servicer) in services:
        add_fn(servicer, server)
