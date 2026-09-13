import abc
from concurrent import futures
from registrar import register_quote_extraction
import grpc


def create_grpc_server(max_num_workers: int):
    return grpc.server(futures.ThreadPoolExecutor(max_workers=max_num_workers))


def serve(port: int, max_num_workers: int) -> grpc.Server:
    server = create_grpc_server(max_num_workers)
    register_quote_extraction(server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    server.wait_for_termination()
