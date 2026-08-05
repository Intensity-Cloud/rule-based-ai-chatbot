#!/usr/bin/env python3
"""
DecodeLabs AI Internship — Project 1: Rule-Based AI Chatbot.

Entry point. Wires together the sanitizer, knowledge base, response
engine, and conversation loop, and handles startup failures gracefully
(e.g. a missing or corrupt knowledge base file) rather than letting a
raw traceback reach the user.

Usage:
    python main.py
"""

import sys

from chatbot.config import APP_NAME, DATA_PATH, LOG_DIR
from chatbot.conversation import ChatbotSession
from chatbot.exceptions import ChatbotError
from chatbot.knowledge_base import KnowledgeBase
from chatbot.logger import setup_logger
from chatbot.response_engine import ResponseEngine


def main() -> int:
    """Run the chatbot and return a process exit code."""
    logger = setup_logger(LOG_DIR)

    try:
        knowledge_base = KnowledgeBase(DATA_PATH)
    except ChatbotError as exc:
        print(f"Failed to start {APP_NAME}: {exc}", file=sys.stderr)
        logger.error("Startup failure: %s", exc)
        return 1

    response_engine = ResponseEngine(knowledge_base)
    session = ChatbotSession(
        knowledge_base=knowledge_base,
        response_engine=response_engine,
        logger=logger,
        bot_name=APP_NAME,
    )

    try:
        session.run()
    except Exception as exc:  # pragma: no cover - top-level safety net
        logger.exception("Unhandled exception during session.")
        print(f"An unexpected error occurred: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
