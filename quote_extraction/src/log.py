import logging
from sys import stdout
from . import env


logger = logging.getLogger(__name__)


def init():
    level = logging.DEBUG
    kwargs = {"level": level}
    
    if env.in_production():
        kwargs["filename"] = "log.txt"
    else:
        kwargs["stream"] = stdout
    
    logging.basicConfig(**kwargs, force=True)
    logger.info(f"Logging with level: {logging.getLevelName(level)}")


import grpc

class LogInterceptor(grpc.ServerInterceptor):
    def __init__(self):
        return

    def intercept_service(self, continuation, handler_call_details):
        logger.info("intercepting...")
        return continuation(handler_call_details)