from protos import extract_pb2_grpc
from .servicers import extract

import grpc
from typing import Callable

from . import stub

import os

import logging

logger = logging.getLogger(__name__)

def load_extraction_servicer():
    log_message = f"Loading {extract.__name__}"
    if os.environ.get("RUN_MODE") == "test":
        logger.info(f"{log_message} (TEST MODE)")
        return extract.ExtractServicer(stub_fn=stub.stub_fn)
    else:
        logger.info(log_message)
        return extract.ExtractServicer()


def services_to_register():
    return [
        (extract_pb2_grpc.add_ExtractServicer_to_server, load_extraction_servicer()),
    ]


def register_services(services: tuple[Callable, object], server: grpc.Server):
    for (add_fn, servicer) in services:
        add_fn(servicer, server)
