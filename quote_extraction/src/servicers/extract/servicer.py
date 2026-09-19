from protos import extract_pb2_grpc
from protos import extract_pb2


class ExtractServicer(extract_pb2_grpc.ExtractServicer):
    def __init__(self):
        return
    
    def Call(self, request, context):
        raise Exception("Not implemented")

