from registrar import register_quote_extraction
import grpc


def serve(port: int) -> grpc.Server:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    register_quote_extraction(server)
    server.add_insecure_port("[::]:50051")
    server.start()
    return server
