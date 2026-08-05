# DecodeBot — Rule-Based AI Chatbot

**A deterministic, rule-based conversational engine built in pure Python.**

[![CI](https://github.com/Intensity-Cloud/rule-based-ai-chatbot/actions/workflows/ci.yml/badge.svg)](https://github.com/Intensity-Cloud/rule-based-ai-chatbot/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-46%20passing-brightgreen)](tests)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](pyproject.toml)
[![Type Checked](https://img.shields.io/badge/mypy-strict-blue)](pyproject.toml)
[![Linted](https://img.shields.io/badge/lint-ruff-261230)](pyproject.toml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](requirements.txt)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

DecodeBot recognizes greetings, farewells, and several other conversational
intents through explicit, human-readable rules — **no machine learning, no
external API calls**. It runs as a continuous command-line loop and was
built as the foundation project of an AI engineering internship track:
before building systems that *learn*, the goal is to master control flow,
deterministic decision-making, and clean program architecture — a "logic
engine," not a "probability engine."

---

## Table of contents

- [Demo](#demo)
- [Why this project](#why-this-project)
- [Features](#features)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [Usage](#usage)
- [Extending the knowledge base](#extending-the-knowledge-base)
- [Testing & code quality](#testing--code-quality)
- [Architecture](#architecture)
- [Future improvements](#future-improvements)
- [Developer notes](#developer-notes)
- [Contributing](#contributing)
- [License](#license)

---

## Demo

```
You: hi
DecodeBot: Hello there! How can I help you today?
You: how are you?
DecodeBot: I'm just a program, but I'm running smoothly! How about you?
You: thanks
DecodeBot: You're welcome!
You: what is the airspeed velocity of an unladen swallow
DecodeBot: I do not understand. Could you rephrase that?
You: exit
DecodeBot: Goodbye! Ending session.
```

## Why this project

A small scope on the surface, used deliberately to demonstrate engineering
discipline rather than algorithmic complexity:

| Area | What's demonstrated |
|---|---|
| **Software architecture** | Clean separation of concerns around an Input → Process → Output pipeline (see [Architecture](#architecture)) |
| **Testing discipline** | 46 tests, 100% line **and** branch coverage, enforced as a hard CI gate |
| **Type safety** | Fully annotated codebase, passes `mypy --strict` |
| **Data-driven design** | Bot vocabulary lives in JSON, not hard-coded conditionals — extendable without touching Python |
| **Error handling** | Custom exception hierarchy; startup validation fails fast with actionable messages instead of crashing mid-conversation |
| **CI/CD** | Automated lint, type-check, and test matrix across Python 3.9–3.12 on every push/PR |
| **Documentation** | Dedicated architecture write-up explaining *why*, not just *what* |

## Features

- **Continuous conversation loop** with graceful exit on `exit`, `quit`,
  `stop`, `Ctrl+D` (EOF), or `Ctrl+C` (interrupt) — never crashes with a
  raw traceback on any of these.
- **Input sanitization** — case-insensitive, whitespace-normalized,
  punctuation-stripped, so `"  HeLLo!! "` and `"hello"` are treated
  identically. Input is also capped at 2,000 characters so a pasted wall
  of text can't bloat matching, logging, or memory use.
- **7 built-in intents**: greeting, farewell, thanks, identity,
  capabilities, mood, and creator — each with multiple trigger phrases
  and multiple randomized responses.
- **Two-stage intent matching** — an O(1) exact-phrase dictionary lookup,
  falling back to a more forgiving keyword/token-overlap match, falling
  back to a default response, so the bot always has *something* to say.
- **Data-driven knowledge base** — intents live in
  `data/knowledge_base.json`, not hard-coded in Python. Extend the bot's
  vocabulary by editing JSON, not code.
- **Session logging** — every conversation is transcribed to a
  timestamped file under `logs/`, separate from console output, for
  debugging.
- **Fully tested** — 46 tests, 100% line *and* branch coverage of
  application code, enforced in CI (the build fails under 100%).
- **Statically typed** — fully annotated, passes `mypy --strict`.
- **Zero external runtime dependencies** — standard library only.
- **Continuous integration** — every push/PR runs ruff, mypy, and the
  full test suite across Python 3.9–3.12 (`.github/workflows/ci.yml`).

## Project structure

```
rule-based-ai-chatbot/
├── main.py                        # Entry point
├── chatbot/                       # Application package
│   ├── __init__.py
│   ├── config.py                  # Paths, constants, exit-command list
│   ├── exceptions.py              # ChatbotError, KnowledgeBaseError
│   ├── sanitizer.py               # Input normalization        (IPO: Input)
│   ├── knowledge_base.py          # Intent data + matching     (IPO: Process)
│   ├── response_engine.py         # Response resolution logic  (IPO: Process)
│   ├── conversation.py            # The continuous loop        (IPO: orchestrator)
│   └── logger.py                  # Session file logging
├── data/
│   └── knowledge_base.json        # Intents, triggers, responses (editable, no code changes needed)
├── tests/                         # 46 tests, 100% coverage of chatbot/
│   ├── test_sanitizer.py
│   ├── test_knowledge_base.py
│   ├── test_response_engine.py
│   ├── test_conversation.py
│   └── test_logger.py
├── docs/
│   └── ARCHITECTURE.md            # Design decisions & rationale, in depth
├── logs/                          # Session transcripts (git-ignored, dir tracked)
├── requirements.txt                # Runtime deps (none — stdlib only)
├── requirements-dev.txt            # pytest, pytest-cov, ruff, mypy
├── pyproject.toml                  # pytest / ruff / mypy / coverage config
├── conftest.py                     # Makes `chatbot` importable for tests
├── .github/workflows/ci.yml        # Lint + type-check + test on every push/PR
├── .gitignore
├── LICENSE                         # MIT
└── README.md
```

## Getting started

**Requirements:** Python 3.9+. No third-party runtime packages are needed.

```bash
git clone https://github.com/Intensity-Cloud/rule-based-ai-chatbot.git
cd rule-based-ai-chatbot

# Optional but recommended: create a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Optional — only needed to run the test suite / linter / type checker
pip install -r requirements-dev.txt
```

## Usage

```bash
python3 main.py
```

Type any message and press Enter. Type `exit`, `quit`, or `stop` (any
case, any surrounding whitespace) to leave. `Ctrl+C` and `Ctrl+D` also
exit cleanly.

## Extending the knowledge base

No Python changes required — just edit `data/knowledge_base.json`:

```json
"joke": {
  "triggers": ["tell me a joke", "make me laugh"],
  "responses": [
    "Why do programmers prefer dark mode? Because light attracts bugs."
  ]
}
```

The knowledge base is validated at startup — a malformed edit (a missing
`triggers` key, an empty `responses` list, or a trigger phrase reused
across two intents) fails immediately with a clear error message rather
than crashing mid-conversation.

## Testing & code quality

```bash
pip install -r requirements-dev.txt

pytest                                          # run the suite
pytest --cov=chatbot --cov-report=term-missing  # with a coverage report
ruff check .                                    # lint
mypy                                             # static type checking
```

**Current status:** 46 tests passing · 100% line + branch coverage of
`chatbot/` · zero lint warnings · `mypy --strict` clean.

## Architecture

The chatbot is built around an **Input → Process → Output** pipeline,
with a single orchestrator (`ChatbotSession`) coordinating independently
testable components (`InputSanitizer`, `KnowledgeBase`, `ResponseEngine`).

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full design
write-up, including the reasoning behind deliberately using **both**
if/else control flow (for the small, fixed exit-command decision) and
dictionary lookups (for the large, growing set of intent-matching rules)
— rather than the if-elif ladder that doesn't scale.

## Future improvements

- **More intents & synonyms** — trivial to add via `knowledge_base.json`.
- **Context/state across turns** — e.g. remembering the user's name once
  given, so later responses can reference it.
- **Nested/conditional responses** — e.g. time-of-day-aware greetings
  ("good morning" only before noon).
- **Personality presets** — swap in a different `knowledge_base.json`
  (formal, casual, sarcastic) without touching code.
- **LLM guardrail layer** — the `ResponseEngine`'s fallback branch is a
  clean seam for routing unmatched input to a language model, turning
  this project into a deterministic "guardrail" layer in front of a
  probabilistic model.
- **Web/GUI front end** — `ChatbotSession` is deliberately the only
  component coupled to the console; a Flask/FastAPI front end could
  reuse `KnowledgeBase` and `ResponseEngine` unchanged.

## Developer notes

- All application logic lives under `chatbot/`; `main.py` is intentionally
  a thin wiring layer so it stays easy to reason about.
- `KnowledgeBase` validates its data file exhaustively at load time (not
  lazily), so configuration errors surface at startup, not three turns
  into a conversation.
- Every public method has a docstring explaining *why*, not just *what*,
  where the reasoning isn't obvious from the code alone.
- Tests use `pytest`'s `tmp_path` fixture to build throwaway knowledge
  base files per test, so the suite never depends on — or risks
  corrupting — `data/knowledge_base.json`.

## Contributing

This started as a solo internship exercise, but it's structured like a
project that welcomes contributions:

1. Fork the repo and create a feature branch.
2. Make your change, keeping `chatbot/` at 100% coverage
   (`pytest --cov=chatbot --cov-report=term-missing`).
3. Run `ruff check .` and `mypy` before opening a PR — CI enforces both.
4. Open a pull request describing the change and the motivation behind it.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full guide.

## License

Released under the [MIT License](LICENSE).

---

Built as the foundation project of an AI engineering internship track —
a deliberate exercise in deterministic logic and clean architecture
before moving on to probabilistic, learning-based systems.
