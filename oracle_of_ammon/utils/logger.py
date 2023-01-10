import logging
import os

from rich.logging import RichHandler


def configure_logger(name: str = __name__) -> logging.Logger:
    log_fmt = "%(message)s"
    logger = logging.getLogger(name)
    logger.propagate = False

    # ensures we do not print duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    # the handler determines where the logs go: stdout/file
    shell_handler = RichHandler()
    shell_formatter = logging.Formatter(log_fmt)

    shell_handler.setFormatter(shell_formatter)
    logger.addHandler(shell_handler)

    logger.setLevel(os.environ.get("LOG_LEVEL", "DEBUG"))

    return logger
