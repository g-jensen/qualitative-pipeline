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
    
    logging.basicConfig(**kwargs)
    logger.info(f"Logging with level: {logging.getLevelName(level)}")
