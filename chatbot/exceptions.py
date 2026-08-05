"""Custom exception hierarchy for the chatbot package.

Using dedicated exception types (instead of bare ``Exception`` or
``ValueError``) lets callers distinguish between "the knowledge base is
broken" and other, unrelated failure modes, and keeps error handling in
``main.py`` precise rather than a catch-all.
"""


class ChatbotError(Exception):
    """Base class for all chatbot-specific errors."""


class KnowledgeBaseError(ChatbotError):
    """Raised when the knowledge base file is missing, malformed, or invalid.

    Examples: the JSON file does not exist, it fails to parse, an intent is
    missing required fields, or two intents claim the same trigger phrase.
    """
