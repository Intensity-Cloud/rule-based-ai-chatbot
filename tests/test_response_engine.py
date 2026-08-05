"""Unit tests for chatbot.response_engine.ResponseEngine."""

import json

import pytest

from chatbot.knowledge_base import KnowledgeBase
from chatbot.response_engine import ResponseEngine


@pytest.fixture
def engine(tmp_path):
    data = {
        "intents": {
            "greeting": {"triggers": ["hi", "hello"], "responses": ["Hi!"]},
        },
        "fallback_responses": ["I don't understand."],
    }
    path = tmp_path / "kb.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    kb = KnowledgeBase(path)
    return ResponseEngine(kb)


def test_exact_match_returns_intent_response(engine):
    assert engine.generate_response("hi") == "Hi!"


def test_keyword_match_returns_intent_response(engine):
    assert engine.generate_response("hello world") == "Hi!"


def test_unrecognized_input_returns_fallback(engine):
    assert engine.generate_response("gibberish text") == "I don't understand."


def test_empty_input_returns_fallback(engine):
    assert engine.generate_response("") == "I don't understand."
