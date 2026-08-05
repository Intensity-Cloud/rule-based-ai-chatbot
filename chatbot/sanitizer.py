"""
Input sanitization — Phase 1 of the IPO model.

Raw user input is noisy: inconsistent casing, stray punctuation, and
irregular whitespace ("HeLLo!!", "  hi  there  "). Every downstream
component (intent matching, logging) assumes it receives *normalized*
text, so sanitization happens exactly once, at the boundary.
"""

import re
from typing import Optional


class InputSanitizer:
    """Normalizes raw user input into a clean, matchable string.

    Stateless by design: every method is a pure function of its input,
    which makes this class trivial to unit test and safe to share across
    threads if the chatbot were ever made concurrent.
    """

    # Collapses any run of whitespace into a single space.
    _WHITESPACE_RE = re.compile(r"\s+")

    # Strips punctuation while preserving word characters, whitespace, and
    # apostrophes (so contractions like "what's" survive sanitization).
    _PUNCTUATION_RE = re.compile(r"[^\w\s']")

    # No conversational intent needs more than this many characters. A cap
    # keeps a pasted multi-megabyte blob (accidental or adversarial) from
    # ballooning the sanitized string, the session log line it produces,
    # and the token-overlap scan in `KnowledgeBase.match_keywords`, all of
    # which currently scale with input length.
    _MAX_INPUT_LENGTH = 2000

    @classmethod
    def sanitize(cls, raw_text: Optional[str]) -> str:
        """Return a lowercase, punctuation-stripped, whitespace-normalized
        version of ``raw_text``.

        Args:
            raw_text: The unprocessed string typed by the user. May be
                ``None`` (defensive: some input sources, like a GUI text
                field, can yield ``None`` instead of an empty string).

        Returns:
            A sanitized string, truncated to :data:`_MAX_INPUT_LENGTH`
            characters. Never ``None`` — an empty or missing input
            sanitizes to ``""``.
        """
        if not raw_text:
            return ""

        text = raw_text[: cls._MAX_INPUT_LENGTH].strip().lower()
        text = cls._PUNCTUATION_RE.sub("", text)
        text = cls._WHITESPACE_RE.sub(" ", text)
        return text.strip()
