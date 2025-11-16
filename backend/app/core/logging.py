import logging
import sys

from app.core.config import config

def set_up():
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s", 
        level=getattr(logging, config.LOG_LEVEL),
        handlers = [
            logging.StreamHandler(sys.stdout)
        ]
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)