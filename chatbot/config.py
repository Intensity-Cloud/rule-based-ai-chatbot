"""
Centralized configuration for the chatbot application.

Keeping paths and constants in a single module avoids magic strings
scattered across the codebase and makes the project trivially
relocatable (e.g. for packaging or containerization).
"""

from pathlib import Path

# Project root is two levels up from this file: chatbot/config.py -> project root
BASE_DIR: Path = Path(__file__).resolve().parent.parent

DATA_PATH: Path = BASE_DIR / "data" / "knowledge_base.json"
LOG_DIR: Path = BASE_DIR / "logs"

APP_NAME: str = "DecodeBot"
APP_VERSION: str = "1.0.0"

# Commands that terminate the conversation loop immediately.
# Kept separate from intents in the knowledge base because exiting is a
# control-flow decision, not a conversational response (see ARCHITECTURE.md).
EXIT_COMMANDS: frozenset[str] = frozenset({"exit", "quit", "stop"})
