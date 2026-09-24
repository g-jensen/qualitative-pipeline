from protos import extract_pb2_grpc
from .servicers import extract

import grpc
from typing import Callable

from . import stub

import os

def extraction_servicer():
    if os.environ.get("RUN_MODE") == "test":
        return extract.ExtractServicer(stub_fn=stub.stub_fn)
    else:
        return extract.ExtractServicer()


def services_to_register():
    return [
        (extract_pb2_grpc.add_ExtractServicer_to_server, extraction_servicer()),
    ]


def register_services(services: tuple[Callable, object], server: grpc.Server):
    for (add_fn, servicer) in services:
        add_fn(servicer, server)
