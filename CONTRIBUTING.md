# Contributing to DecodeBot

Thanks for taking a look. This project is small by design, but it's
maintained with the same discipline as a larger codebase — a green CI
run is required before anything merges.

## Getting set up

```bash
git clone <this-repository-url>
cd rule-based-ai-chatbot
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

## Before opening a pull request

Run the full local check locally — it's exactly what CI runs:

```bash
ruff check .                                              # lint
mypy                                                        # static types
pytest --cov=chatbot --cov-report=term-missing --cov-fail-under=100  # tests
```

All three must pass. Coverage is enforced at 100% (line and branch) for
the `chatbot/` package, so any new code path needs a matching test.

## Guidelines

- Keep `chatbot/` free of I/O where possible — components should stay
  independently unit-testable without a terminal attached (see
  [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)).
- Prefer extending `data/knowledge_base.json` over adding new
  conditionals when the change is just "more vocabulary."
- Every public method should have a docstring explaining *why* the
  design choice was made, not just what the code does.
- Match the existing style — `ruff` and `mypy --strict` are the source
  of truth, not personal preference.

## Reporting issues

Open an issue with a clear description, the input that triggered the
problem (if applicable), and what you expected to happen instead.
