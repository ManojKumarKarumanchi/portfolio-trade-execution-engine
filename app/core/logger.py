"""Logger configuration module."""
import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    log = logging.getLogger(name)

    if log.handlers:
        return log

    log.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(levelname)s] [%(asctime)s] [%(name)s] %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.propagate = False

    return log


logger = get_logger("app")
