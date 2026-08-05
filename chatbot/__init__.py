"""
chatbot
~~~~~~~

A deterministic, rule-based conversational engine built around the
Input -> Process -> Output (IPO) model.

This package intentionally contains zero machine-learning code. Every
response is traceable to an explicit rule in ``data/knowledge_base.json``,
by design (see docs/ARCHITECTURE.md for the rationale).
"""

__version__ = "1.0.0"
__all__ = ["__version__"]
