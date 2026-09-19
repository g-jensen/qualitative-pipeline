from protos import echo_pb2_grpc
from protos import echo_pb2


class EchoServicer(echo_pb2_grpc.EchoServicer):
    def __init__(self):
        return
    
    def Call(self, request: echo_pb2.EchoRequest, context):
        return echo_pb2.EchoResponse(content=request.content)
