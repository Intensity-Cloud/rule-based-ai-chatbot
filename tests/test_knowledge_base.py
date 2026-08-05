"""Unit tests for chatbot.knowledge_base.KnowledgeBase."""

import json

import pytest

from chatbot.exceptions import KnowledgeBaseError
from chatbot.knowledge_base import KnowledgeBase


@pytest.fixture
def valid_kb_path(tmp_path):
    data = {
        "intents": {
            "greeting": {"triggers": ["hi", "hello"], "responses": ["Hi!"]},
            "farewell": {"triggers": ["bye"], "responses": ["Bye!"]},
        },
        "fallback_responses": ["I don't understand."],
    }
    path = tmp_path / "kb.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class TestLoading:
    def test_loads_valid_file(self, valid_kb_path):
        kb = KnowledgeBase(valid_kb_path)
        assert set(kb.intent_names) == {"greeting", "farewell"}

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(KnowledgeBaseError, match="not found"):
            KnowledgeBase(tmp_path / "missing.json")

    def test_invalid_json_raises(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(KnowledgeBaseError, match="Invalid JSON"):
            KnowledgeBase(path)

    def test_non_object_root_raises(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")
        with pytest.raises(KnowledgeBaseError):
            KnowledgeBase(path)

    def test_missing_intents_key_raises(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text(json.dumps({"fallback_responses": ["x"]}), encoding="utf-8")
        with pytest.raises(KnowledgeBaseError, match="intents"):
            KnowledgeBase(path)

    def test_missing_fallback_key_raises(self, tmp_path):
        data = {"intents": {"greeting": {"triggers": ["hi"], "responses": ["Hi!"]}}}
        path = tmp_path / "bad.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(KnowledgeBaseError, match="fallback_responses"):
            KnowledgeBase(path)

    def test_intent_missing_triggers_raises(self, tmp_path):
        data = {
            "intents": {"greeting": {"responses": ["Hi!"]}},
            "fallback_responses": ["x"],
        }
        path = tmp_path / "bad.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(KnowledgeBaseError, match="triggers"):
            KnowledgeBase(path)

    def test_intent_missing_responses_raises(self, tmp_path):
        data = {
            "intents": {"greeting": {"triggers": ["hi"]}},
            "fallback_responses": ["x"],
        }
        path = tmp_path / "bad.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(KnowledgeBaseError, match="responses"):
            KnowledgeBase(path)

    def test_intent_with_only_blank_triggers_raises(self, tmp_path):
        data = {
            "intents": {"greeting": {"triggers": ["   ", ""], "responses": ["Hi!"]}},
            "fallback_responses": ["x"],
        }
        path = tmp_path / "bad.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(KnowledgeBaseError, match="no valid"):
            KnowledgeBase(path)

    def test_duplicate_trigger_across_intents_raises(self, tmp_path):
        data = {
            "intents": {
                "a": {"triggers": ["hi"], "responses": ["x"]},
                "b": {"triggers": ["hi"], "responses": ["y"]},
            },
            "fallback_responses": ["z"],
        }
        path = tmp_path / "bad.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(KnowledgeBaseError, match="unique"):
            KnowledgeBase(path)


class TestMatching:
    def test_exact_match_returns_intent(self, valid_kb_path):
        kb = KnowledgeBase(valid_kb_path)
        assert kb.match_exact("hi") == "greeting"
        assert kb.match_exact("bye") == "farewell"

    def test_exact_match_returns_none_when_unmatched(self, valid_kb_path):
        kb = KnowledgeBase(valid_kb_path)
        assert kb.match_exact("nonexistent phrase") is None

    def test_keyword_match_matches_partial_phrase(self, valid_kb_path):
        kb = KnowledgeBase(valid_kb_path)
        assert kb.match_keywords("hello there friend") == "greeting"

    def test_keyword_match_returns_none_for_empty_input(self, valid_kb_path):
        kb = KnowledgeBase(valid_kb_path)
        assert kb.match_keywords("") is None

    def test_keyword_match_returns_none_when_no_overlap(self, valid_kb_path):
        kb = KnowledgeBase(valid_kb_path)
        assert kb.match_keywords("completely unrelated text") is None

    def test_keyword_match_prefers_longer_more_specific_trigger(self, tmp_path):
        # "good" (1 word) and "good morning" (2 words) both qualify against
        # this input; the longer, more specific trigger must win.
        data = {
            "intents": {
                "mood": {"triggers": ["good"], "responses": ["Good to hear."]},
                "greeting": {
                    "triggers": ["good morning"],
                    "responses": ["Morning!"],
                },
            },
            "fallback_responses": ["x"],
        }
        path = tmp_path / "kb.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        kb = KnowledgeBase(path)

        assert kb.match_keywords("good morning everyone") == "greeting"


class TestResponses:
    def test_get_response_returns_a_known_reply(self, valid_kb_path):
        kb = KnowledgeBase(valid_kb_path)
        assert kb.get_response("greeting") == "Hi!"

    def test_get_response_unknown_intent_raises(self, valid_kb_path):
        kb = KnowledgeBase(valid_kb_path)
        with pytest.raises(KnowledgeBaseError, match="Unknown intent"):
            kb.get_response("nonexistent")

    def test_get_fallback_response_returns_configured_value(self, valid_kb_path):
        kb = KnowledgeBase(valid_kb_path)
        assert kb.get_fallback_response() == "I don't understand."
