"""Structured logging configuration with Arabic text support."""

import logging
import sys


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure application-wide logging."""
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
    )

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Ensure UTF-8 for Arabic output
    for handler in logging.root.handlers:
        if hasattr(handler, "stream"):
            try:
                handler.stream.reconfigure(encoding="utf-8")
            except (AttributeError, OSError):
                pass

    # Suppress noisy third-party loggers
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("qdrant_client").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

    logger = logging.getLogger("smart_legal_advisor")
    logger.info("Logging initialized — level=%s", level)
    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger."""
    return logging.getLogger(f"smart_legal_advisor.{name}")
