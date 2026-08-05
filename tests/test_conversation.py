"""
Integration tests for chatbot.conversation.ChatbotSession.

These simulate a real terminal session by monkeypatching `builtins.input`
with a canned sequence of user messages, and asserting on captured stdout.
"""

import json

import pytest

from chatbot.conversation import ChatbotSession
from chatbot.knowledge_base import KnowledgeBase
from chatbot.response_engine import ResponseEngine


@pytest.fixture
def session(tmp_path):
    data = {
        "intents": {"greeting": {"triggers": ["hi"], "responses": ["Hi!"]}},
        "fallback_responses": ["Huh?"],
    }
    path = tmp_path / "kb.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    kb = KnowledgeBase(path)
    engine = ResponseEngine(kb)
    return ChatbotSession(kb, engine)


def _feed_inputs(monkeypatch, values):
    iterator = iter(values)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(iterator))


def test_session_responds_and_ends_on_exit(monkeypatch, session, capsys):
    _feed_inputs(monkeypatch, ["hi", "exit"])
    session.run()
    out = capsys.readouterr().out
    assert "Hi!" in out
    assert "Goodbye" in out


def test_session_ends_on_quit_synonym(monkeypatch, session, capsys):
    _feed_inputs(monkeypatch, ["quit"])
    session.run()
    out = capsys.readouterr().out
    assert "Goodbye" in out


def test_session_case_and_whitespace_insensitive_exit(monkeypatch, session, capsys):
    _feed_inputs(monkeypatch, ["   EXIT   "])
    session.run()
    out = capsys.readouterr().out
    assert "Goodbye" in out


def test_session_handles_eof_gracefully(monkeypatch, session, capsys):
    def raise_eof(prompt=""):
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)
    session.run()
    out = capsys.readouterr().out.lower()
    assert "goodbye" in out or "closed" in out


def test_session_handles_keyboard_interrupt_gracefully(monkeypatch, session, capsys):
    def raise_interrupt(prompt=""):
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", raise_interrupt)
    session.run()
    out = capsys.readouterr().out.lower()
    assert "interrupted" in out


def test_unrecognized_input_gets_fallback(monkeypatch, session, capsys):
    _feed_inputs(monkeypatch, ["asdkjfh", "exit"])
    session.run()
    out = capsys.readouterr().out
    assert "Huh?" in out
