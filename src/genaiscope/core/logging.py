"""Logging utilities."""

import logging

from genaiscope.core.config import get_config


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    config = get_config()
    logger = logging.getLogger(name)

    if not logger.handlers:
        level = getattr(logging, config.log_level.upper(), logging.INFO)
        logger.setLevel(level)

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if config.log_file:
            file_handler = logging.FileHandler(config.log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger
