"""
Response engine — the "Process" stage of the IPO model.

Given already-sanitized text, this module is solely responsible for
deciding *what intent it represents* and *what to say back*. It knows
nothing about I/O (stdin/stdout) or raw text handling — that separation
keeps it trivially testable and reusable (e.g. behind a future web API).
"""

from .knowledge_base import KnowledgeBase


class ResponseEngine:
    """Resolves sanitized input to a response using a layered matching
    strategy, falling back to a default reply when nothing matches.

    Matching order:
        1. Exact-phrase match   (O(1), highest confidence)
        2. Keyword/token match  (more forgiving, still deterministic)
        3. Fallback response    (guarantees the bot never has "nothing to say")
    """

    def __init__(self, knowledge_base: KnowledgeBase) -> None:
        self._kb = knowledge_base

    def generate_response(self, sanitized_text: str) -> str:
        """Return the chatbot's reply for a single sanitized user message.

        Args:
            sanitized_text: Output of :meth:`InputSanitizer.sanitize`.

        Returns:
            A response string. Always non-empty — the fallback guarantee
            means this method never returns ``None`` or raises for
            well-formed (even if unrecognized) input.
        """
        if not sanitized_text:
            return self._kb.get_fallback_response()

        intent_name = self._kb.match_exact(sanitized_text)
        if intent_name is None:
            intent_name = self._kb.match_keywords(sanitized_text)

        if intent_name is not None:
            return self._kb.get_response(intent_name)

        return self._kb.get_fallback_response()
