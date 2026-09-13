from . import quote_extraction_pb2_grpc

class QuoteExtractionServicer(quote_extraction_pb2_grpc.QuoteExtractionServicer):
    def __init__(self):
        return
    
    def Extract(self, request, context):
        return