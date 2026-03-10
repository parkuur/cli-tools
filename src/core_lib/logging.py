"""Logging configuration for cli-tools."""

import logging


def configure_logging(level: str) -> None:
    """Configure the root handler for cli-tools. Call once at CLI startup."""
    handler = logging.StreamHandler()
    handler.setLevel(level.upper())
    logging.root.addHandler(handler)
    logging.root.setLevel(level.upper())
