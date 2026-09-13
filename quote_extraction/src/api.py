import abc
from concurrent import futures
from registrar import register_quote_extraction
import grpc


class ServerFactory(abc.ABC):
    @abc.abstractmethod
    def create(self, max_num_workers: int) -> grpc.Server: pass


def serve(server_factory: ServerFactory, port: int, max_num_workers: int) -> grpc.Server:
    server = server_factory.create(max_num_workers)
    register_quote_extraction(server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    return server
