import grpc

from servicers.quote_extraction.quote_extraction_pb2_grpc import add_QuoteExtractionServicer_to_server
from servicers.quote_extraction import QuoteExtractionServicer
def register_quote_extraction(server: grpc.Server):
    add_QuoteExtractionServicer_to_server(QuoteExtractionServicer(), server)