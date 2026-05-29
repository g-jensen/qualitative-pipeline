from opentelemetry import trace

def extraction_tracer():
    return trace.get_tracer("quote_extraction")