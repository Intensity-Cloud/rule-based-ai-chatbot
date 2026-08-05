"""Unit tests for chatbot.sanitizer.InputSanitizer."""

from chatbot.sanitizer import InputSanitizer


def test_lowercases_and_strips_outer_whitespace():
    assert InputSanitizer.sanitize("  HeLLo  ") == "hello"


def test_removes_trailing_punctuation():
    assert InputSanitizer.sanitize("Hello!!!") == "hello"


def test_removes_question_marks():
    assert InputSanitizer.sanitize("How are you?") == "how are you"


def test_collapses_internal_whitespace():
    assert InputSanitizer.sanitize("hi    there") == "hi there"


def test_handles_none_input():
    assert InputSanitizer.sanitize(None) == ""


def test_handles_empty_string():
    assert InputSanitizer.sanitize("") == ""


def test_handles_whitespace_only_string():
    assert InputSanitizer.sanitize("     ") == ""


def test_preserves_apostrophes_for_contractions():
    assert InputSanitizer.sanitize("What's up?") == "what's up"


def test_is_idempotent():
    once = InputSanitizer.sanitize("  Hello, World!  ")
    twice = InputSanitizer.sanitize(once)
    assert once == twice


def test_truncates_excessively_long_input():
    huge_input = "a" * 10_000
    result = InputSanitizer.sanitize(huge_input)
    assert len(result) == InputSanitizer._MAX_INPUT_LENGTH


def test_truncation_applies_before_normalization():
    # The cap is on raw length, so trailing content past the limit (here,
    # a punctuation run) must never appear in the output.
    huge_input = "b" * InputSanitizer._MAX_INPUT_LENGTH + "!!!excess text!!!"
    result = InputSanitizer.sanitize(huge_input)
    assert result == "b" * InputSanitizer._MAX_INPUT_LENGTH
    assert "excess" not in result
