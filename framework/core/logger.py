"""Centralized logging.

Provides console + rotating file handlers. Log level is driven by settings
(LOG_LEVEL). Loggers are cached by name so repeated calls are cheap and do not
attach duplicate handlers.
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured: set[str] = set()


def _resolve_level() -> int:
    # Imported lazily to avoid a circular import at module load time.
    from config.settings import get_settings

    return getattr(logging, get_settings().log_level, logging.INFO)


def get_logger(name: str = "api-framework") -> logging.Logger:
    """Return a configured logger. Idempotent per logger name."""
    logger = logging.getLogger(name)
    if name in _configured:
        return logger

    level = _resolve_level()
    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    console = logging.StreamHandler(stream=sys.stdout)
    console.setFormatter(formatter)
    console.setLevel(level)
    logger.addHandler(console)

    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            _LOG_DIR / "api-framework.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    except OSError:
        # If the filesystem is read-only, console logging still works.
        logger.warning("Could not create log file; continuing with console only.")

    _configured.add(name)
    return logger
