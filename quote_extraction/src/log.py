import logging
from sys import stdout
import os

logger = logging.getLogger(__name__)


def in_production():
    return os.environ.get("RUN_MODE") == "production"


def init():
    level = logging.DEBUG
    kwargs = {"level": level}
    
    if in_production():
        kwargs["filename"] = "log.txt"
    else:
        kwargs["stream"] = stdout
    
    logging.basicConfig(**kwargs)
    logger.info(f"Logging with level: {logging.getLevelName(level)}")