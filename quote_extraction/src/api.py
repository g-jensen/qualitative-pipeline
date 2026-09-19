import abc
from concurrent import futures
from . import registrar
import grpc
import logging


logger = logging.getLogger(__name__)


def create_grpc_server(max_num_workers: int):
    return grpc.server(futures.ThreadPoolExecutor(max_workers=max_num_workers))


def serve(port: int, max_num_workers: int) -> grpc.Server:
    server = create_grpc_server(max_num_workers)

    registrar.register_services(registrar.services_to_register(), server)
    
    address = f"127.0.0.1:{port}"
    server.add_insecure_port(address)
    server.start()
    logger.info(f"Serving at http://{address}")

    server.wait_for_termination()
