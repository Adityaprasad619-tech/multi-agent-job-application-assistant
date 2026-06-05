"""
Logger Setup
=============
Configures structured logging using Loguru.

Design Decisions:
- Loguru chosen over stdlib logging for cleaner syntax and auto-rotation.
- Logs to both console (colorized) and rotating file.
- Single setup function called once at app startup.
- Log files auto-rotate at 10 MB, kept for 7 days.
"""

import sys
from pathlib import Path

from loguru import logger


def setup_logger(log_dir: Path) -> None:
    """
    Configure Loguru with console + file sinks.

    Parameters
    ----------
    log_dir : Path
        Directory where log files will be written.
    """
    # Remove default handler to avoid duplicate console output
    logger.remove()

    # Console sink — colored, INFO level
    logger.add(
        sys.stderr,
        level="INFO",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # File sink — DEBUG level for full trace, auto-rotated
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} — {message}"
        ),
    )

    logger.info("Logger initialized — logs at {}", log_dir)
