"""Logging configuration utilities."""

from __future__ import annotations

import logging


def configure_logging(debug: bool = False) -> None:
    """Configure process-wide logging format and level."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
