"""
Knowledge base — the chatbot's "memory" of intents and responses.

Design note (see docs/ARCHITECTURE.md for the full rationale):
The training material explicitly contrasts an if-elif ladder (O(n),
"high technical debt", "UNSTABLE") against a dictionary lookup via
``.get()`` (O(1), "the professional approach"). This module implements
the latter: intents are loaded once at startup into a dictionary index,
so recognizing a trigger phrase is a constant-time hash lookup no matter
how large the knowledge base grows.

The knowledge base itself lives in ``data/knowledge_base.json`` rather
than being hard-coded in Python. That is a deliberate extensibility
choice: the conclusion slide explicitly encourages "expanding the bot's
vocabulary" — with this design, that means editing a JSON file, not
touching application code.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from random import choice
from typing import Any, Optional

from .exceptions import KnowledgeBaseError


@dataclass(frozen=True)
class Intent:
    """A single recognizable conversational intent.

    Attributes:
        name: Unique identifier for the intent (e.g. ``"greeting"``).
        triggers: Normalized phrases that should resolve to this intent.
        responses: Candidate replies; one is chosen at random per match to
            keep repeated conversations from feeling robotic.
    """

    name: str
    triggers: set[str]
    responses: list[str]


class KnowledgeBase:
    """Loads, validates, and serves intent/response data.

    Two lookup strategies are exposed:

    * :meth:`match_exact` — O(1) dictionary lookup for exact phrase matches.
    * :meth:`match_keywords` — a slightly more forgiving token-overlap
      match, used only when the exact lookup misses, so that phrasing like
      "hello there!" still resolves to the "greeting" intent even though
      the full sanitized string isn't itself a registered trigger.
    """

    def __init__(self, data_path: Path) -> None:
        self._data_path = Path(data_path)
        self._intents: dict[str, Intent] = {}
        self._trigger_index: dict[str, str] = {}
        self._fallback_responses: list[str] = []
        self._load()

    # ------------------------------------------------------------------ #
    # Loading & validation
    # ------------------------------------------------------------------ #

    def _load(self) -> None:
        if not self._data_path.exists():
            raise KnowledgeBaseError(
                f"Knowledge base file not found: {self._data_path}"
            )

        try:
            raw = json.loads(self._data_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise KnowledgeBaseError(
                f"Invalid JSON in knowledge base file '{self._data_path}': {exc}"
            ) from exc

        if not isinstance(raw, dict):
            raise KnowledgeBaseError("Knowledge base root must be a JSON object.")

        self._load_intents(raw.get("intents"))
        self._load_fallbacks(raw.get("fallback_responses"))

    def _load_intents(self, intents_raw: Any) -> None:
        if not intents_raw or not isinstance(intents_raw, dict):
            raise KnowledgeBaseError(
                "Knowledge base must define a non-empty 'intents' object."
            )

        for name, payload in intents_raw.items():
            triggers = payload.get("triggers") if isinstance(payload, dict) else None
            responses = payload.get("responses") if isinstance(payload, dict) else None

            if not triggers or not isinstance(triggers, list):
                raise KnowledgeBaseError(
                    f"Intent '{name}' is missing a non-empty 'triggers' list."
                )
            if not responses or not isinstance(responses, list):
                raise KnowledgeBaseError(
                    f"Intent '{name}' is missing a non-empty 'responses' list."
                )

            normalized_triggers = {
                t.strip().lower() for t in triggers if isinstance(t, str) and t.strip()
            }
            if not normalized_triggers:
                raise KnowledgeBaseError(
                    f"Intent '{name}' has no valid (non-empty string) trigger phrases."
                )

            self._intents[name] = Intent(
                name=name, triggers=normalized_triggers, responses=list(responses)
            )
            self._index_triggers(name, normalized_triggers)

    def _index_triggers(self, intent_name: str, triggers: set[str]) -> None:
        for trigger in triggers:
            existing_owner = self._trigger_index.get(trigger)
            if existing_owner is not None and existing_owner != intent_name:
                raise KnowledgeBaseError(
                    f"Trigger phrase '{trigger}' is claimed by both "
                    f"'{existing_owner}' and '{intent_name}'. Trigger phrases "
                    f"must be unique across intents."
                )
            self._trigger_index[trigger] = intent_name

    def _load_fallbacks(self, fallback_raw: Any) -> None:
        if not fallback_raw or not isinstance(fallback_raw, list):
            raise KnowledgeBaseError(
                "Knowledge base must define a non-empty 'fallback_responses' list."
            )
        self._fallback_responses = list(fallback_raw)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    @property
    def intent_names(self) -> list[str]:
        """Names of every loaded intent, primarily useful for diagnostics/tests."""
        return list(self._intents.keys())

    def match_exact(self, sanitized_text: str) -> Optional[str]:
        """O(1) exact-phrase lookup against the trigger index.

        This is the "professional approach" the training material
        describes: ``responses.get(user_input, default)`` in spirit,
        generalized to map a phrase to an *intent name* rather than
        directly to a response string, which keeps matching and response
        selection as separate concerns.
        """
        return self._trigger_index.get(sanitized_text)

    def match_keywords(self, sanitized_text: str) -> Optional[str]:
        """Token-overlap fallback match for phrasing not registered verbatim.

        An intent matches if *all* of one of its trigger phrases' words
        appear among the user's input tokens (e.g. trigger "good morning"
        matches input "good morning everyone"). Among all qualifying
        intents, the one with the most overlapping words wins, which
        favors more specific (longer) trigger phrases over shorter,
        more generic ones.
        """
        tokens = set(sanitized_text.split())
        if not tokens:
            return None

        best_intent: Optional[str] = None
        best_score = 0

        for intent in self._intents.values():
            for trigger in intent.triggers:
                trigger_tokens = set(trigger.split())
                overlap = len(trigger_tokens & tokens)
                is_full_trigger_match = overlap == len(trigger_tokens)
                if is_full_trigger_match and overlap > best_score:
                    best_score = overlap
                    best_intent = intent.name

        return best_intent

    def get_response(self, intent_name: str) -> str:
        """Return a (randomly chosen) response for a known intent.

        Raises:
            KnowledgeBaseError: if ``intent_name`` was never loaded. This
                indicates a programming error upstream (e.g. a matcher
                returning a stale name), not a bad user input, so it is
                intentionally not swallowed silently.
        """
        intent = self._intents.get(intent_name)
        if intent is None:
            raise KnowledgeBaseError(f"Unknown intent requested: '{intent_name}'")
        return choice(intent.responses)

    def get_fallback_response(self) -> str:
        """Return a (randomly chosen) default response for unrecognized input."""
        return choice(self._fallback_responses)
