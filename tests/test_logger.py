"""Unit tests for chatbot.logger.setup_logger."""

import logging
import os

from chatbot.logger import setup_logger


def test_creates_log_directory_and_file(tmp_path):
    log_dir = tmp_path / "logs"
    setup_logger(log_dir, name="test_logger_creates_dir")

    assert log_dir.exists()
    assert any(log_dir.glob("session_*.log"))


def test_log_filename_includes_pid_for_collision_resistance(tmp_path):
    log_dir = tmp_path / "logs"
    setup_logger(log_dir, name="test_logger_pid")

    log_files = list(log_dir.glob("session_*.log"))
    assert log_files
    assert str(os.getpid()) in log_files[0].name


def test_two_sessions_get_distinct_log_files(tmp_path):
    log_dir = tmp_path / "logs"
    setup_logger(log_dir, name="test_logger_distinct_a")
    setup_logger(log_dir, name="test_logger_distinct_b")

    log_files = list(log_dir.glob("session_*.log"))
    assert len(log_files) == 2


def test_returns_configured_logger(tmp_path):
    logger = setup_logger(tmp_path / "logs", name="test_logger_configured")

    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.DEBUG
    assert logger.propagate is False
    assert len(logger.handlers) == 1


def test_log_message_is_written_to_file(tmp_path):
    log_dir = tmp_path / "logs"
    logger = setup_logger(log_dir, name="test_logger_writes")
    logger.info("hello from test")

    for handler in logger.handlers:
        handler.flush()

    log_files = list(log_dir.glob("session_*.log"))
    assert log_files
    contents = log_files[0].read_text(encoding="utf-8")
    assert "hello from test" in contents


def test_setup_is_idempotent_for_same_logger_name(tmp_path):
    name = "test_logger_idempotent"
    first = setup_logger(tmp_path / "logs", name=name)
    second = setup_logger(tmp_path / "logs", name=name)

    assert first is second
    assert len(second.handlers) == 1
