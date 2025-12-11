"""
Logging configuration.
"""

import logging
from app.config.settings import settings


def setup_logging() -> None:
    """
    Configure application logging settings.
    """
    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Set specific log levels for third-party libraries to reduce noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
