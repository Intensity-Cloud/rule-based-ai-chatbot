"""
Conversation loop — the chatbot's "heartbeat".

Implements the continuous input/process/output cycle: the program stays
alive, reading one line at a time, until an explicit exit command (or an
interrupt) breaks the loop. This mirrors the "Heartbeat: The Infinite
Loop" diagram from the project brief exactly:

    while True:
        user_input = get_input()
        if user_input == 'exit':
            break
        process(user_input)

Two control-flow strategies are used side by side, deliberately:

* Exit detection uses an explicit ``if`` check against a small, fixed set
  of control commands — this *is* the if-else logic the brief asks for,
  applied where it belongs: a binary "keep going / stop" decision.
* Everything else (which intent matched, what to reply) is delegated to
  :class:`~chatbot.response_engine.ResponseEngine`, which uses dictionary
  lookups rather than an if-elif ladder, per the brief's own guidance on
  the anti-pattern. See docs/ARCHITECTURE.md for the full rationale.
"""

import logging
from typing import Optional

from .config import EXIT_COMMANDS
from .knowledge_base import KnowledgeBase
from .response_engine import ResponseEngine
from .sanitizer import InputSanitizer


class ChatbotSession:
    """Runs a single interactive chatbot session on the console.

    Kept intentionally thin: this class only coordinates *when* to read
    input, sanitize it, check for exit, and print a response. All of the
    interesting logic lives in the components it delegates to, which keeps
    this class easy to read top-to-bottom and easy to swap out (e.g. for
    a GUI or web front end that drives the same engine).
    """

    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        response_engine: ResponseEngine,
        sanitizer: type[InputSanitizer] = InputSanitizer,
        logger: Optional[logging.Logger] = None,
        bot_name: str = "DecodeBot",
    ) -> None:
        self._kb = knowledge_base
        self._engine = response_engine
        self._sanitizer = sanitizer
        self._logger = logger or logging.getLogger(__name__)
        self._bot_name = bot_name

    def run(self) -> None:
        """Start the continuous conversation loop.

        Blocks until the user issues an exit command, sends EOF (Ctrl+D),
        or interrupts the process (Ctrl+C) — all three are handled
        gracefully with a friendly farewell rather than a stack trace.
        """
        self._print_welcome()

        while True:
            raw_input_text = self._read_input()
            if raw_input_text is None:
                # EOF or KeyboardInterrupt already handled/logged/printed
                # inside _read_input; just end the loop.
                break

            sanitized = self._sanitizer.sanitize(raw_input_text)
            self._logger.debug("raw=%r sanitized=%r", raw_input_text, sanitized)

            if sanitized in EXIT_COMMANDS:
                self._handle_exit()
                break

            response = self._engine.generate_response(sanitized)
            self._say(response)
            self._logger.info("input=%r response=%r", sanitized, response)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _read_input(self) -> Optional[str]:
        try:
            return input("You: ")
        except EOFError:
            self._say("Input stream closed. Goodbye!")
            self._logger.info("Session ended via EOF.")
            return None
        except KeyboardInterrupt:
            print()  # move past the '^C' the terminal echoes
            self._say("Session interrupted. Goodbye!")
            self._logger.info("Session ended via KeyboardInterrupt.")
            return None

    def _handle_exit(self) -> None:
        self._say("Goodbye! Ending session.")
        self._logger.info("Session ended via exit command.")

    def _print_welcome(self) -> None:
        self._say(
            "Hello! I'm a rule-based chatbot. "
            "Type 'exit', 'quit', or 'stop' anytime to leave."
        )

    def _say(self, message: str) -> None:
        print(f"{self._bot_name}: {message}")
