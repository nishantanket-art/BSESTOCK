"""
utils/helpers.py
Common utility functions.
"""

import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def now_ist() -> str:
    """Return current IST timestamp as formatted string."""
    return datetime.now().strftime("%d %b %Y, %I:%M %p")


def safe_float(value, default=0.0) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
