from . import quote_extraction_pb2_grpc
from . import quote_extraction_pb2


class QuoteExtractionServicer(quote_extraction_pb2_grpc.QuoteExtractionServicer):
    def __init__(self):
        return
    
    def Extract(self, request, context):
        yield quote_extraction_pb2.Extraction(content="Hello")