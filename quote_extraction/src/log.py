import logging
from sys import stdout
from . import env
import grpc
from grpc_interceptor import ServerInterceptor
import json
from google.protobuf.json_format import MessageToDict
import uuid


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


def log_message(message, key: str, uuid: str):
    logger.info(json.dumps({
        "uuid": uuid,
        key: MessageToDict(message)
    }))


def log_request(request, uuid: str):
    log_message(request, "request", uuid)


def log_response(response, uuid: str):
    log_message(response, "response", uuid)


# TODO - potentially clamp logs to a maximum length
class LogInterceptor(ServerInterceptor):
    def intercept(self, method, request, context, method_name):
        log_uuid = str(uuid.uuid1()) # insecure but fast. use uuid4() for more security. TODO - eventually, this should be replaced by a trace id.
        log_request(request, log_uuid)
        responses = method(request, context)
        for response in responses:
            log_response(response, log_uuid)
            yield response