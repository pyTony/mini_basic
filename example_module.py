import logging

logger = logging.getLogger(__name__)

def do_something():
    logger.info("Doing something important in the module")
    logger.debug("Debug detail here")
    return True