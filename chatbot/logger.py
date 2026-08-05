"""
Logging configuration.

Every session writes a timestamped transcript to ``logs/``, separate from
the console conversation. This is standard production practice: it means
a bug report can include "here's exactly what was typed and matched"
without asking the user to reproduce it manually.
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logger(log_dir: Path, name: str = "chatbot") -> logging.Logger:
    """Configure and return a file-backed logger for a chatbot session.

    Args:
        log_dir: Directory where session log files are written. Created
            if it does not already exist.
        name: Logger name; reusing the same name across calls returns a
            logger with the same handlers attached (idempotent setup).

    Returns:
        A configured ``logging.Logger`` writing DEBUG-and-above records to
        a per-session timestamped file.
    """
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Second-level resolution alone isn't enough: two sessions started in
    # the same wall-clock second (e.g. two quick test runs, or two
    # processes launched from a script) would otherwise resolve to the
    # same filename and silently interleave their log records. Microsecond
    # resolution plus the PID makes collisions effectively impossible.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_file = log_dir / f"session_{timestamp}_{os.getpid()}.log"

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # don't also spam the root logger / console

    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
