# Architecture

Design decisions and rationale for DecodeBot. For a feature overview and
setup instructions, see the [root README](../README.md).

## Contents

- [The IPO model](#the-ipo-model)
- [Component responsibilities](#component-responsibilities)
- [Design decision: if-else *and* dictionaries, deliberately](#design-decision-if-else-and-dictionaries-deliberately)
- [Why the knowledge base lives in JSON, not Python](#why-the-knowledge-base-lives-in-json-not-python)
- [Two-stage intent matching](#two-stage-intent-matching)
- [Error handling strategy](#error-handling-strategy)
- [Forward-looking note: this *is* a guardrail layer](#forward-looking-note-this-is-a-guardrail-layer)

## The IPO model

The chatbot is built around the **Input → Process → Output** model, mapped
directly onto three components:

```
┌──────────────┐      ┌───────────────────┐      ┌──────────────────┐
│   INPUT       │      │     PROCESS        │      │     OUTPUT        │
│               │      │                     │      │                    │
│ InputSanitizer│ ───▶ │ KnowledgeBase +     │ ───▶ │ print() to console │
│ .sanitize()   │      │ ResponseEngine      │      │ + logger.info()    │
│               │      │ .generate_response()│      │  (feedback loop)   │
└──────────────┘      └───────────────────┘      └──────────────────┘
```

`ChatbotSession` (`chatbot/conversation.py`) is the only component that
knows about *all three* stages — it is the orchestrator. Every other
component only knows about its own stage, which is what makes each of
them independently unit-testable without a terminal attached.

## Component responsibilities

| Component | File | Responsibility |
|---|---|---|
| `InputSanitizer` | `sanitizer.py` | Normalize raw text: lowercase, strip, collapse whitespace, strip punctuation. Pure functions, no state. |
| `KnowledgeBase` | `knowledge_base.py` | Load + validate `data/knowledge_base.json`; expose O(1) exact matching and token-overlap matching; own response/fallback selection. |
| `ResponseEngine` | `response_engine.py` | Decide *what to say*, given sanitized text and a `KnowledgeBase`. No I/O. |
| `ChatbotSession` | `conversation.py` | Run the continuous loop; read input, detect exit commands, delegate to the engine, print/log output. |
| `logger.py` | `logger.py` | Configure a per-session file logger (separate from the console conversation). |
| `main.py` | (root) | Wire everything together; handle startup failures without a raw traceback. |

## Design decision: if-else *and* dictionaries, deliberately

The project brief contains what reads like two competing instructions:

1. The requirements bullet list says **"Use if-else logic for responses."**
2. Several later slides ("The Anti-Pattern: The If-Elif Ladder",
   "Algorithmic Efficiency", "Implementation: The `.get()` Method")
   explicitly show a long `if/elif` chain as **O(n)**, "high technical
   debt", and **"UNSTABLE"** — and present a dictionary `.get()` lookup
   as **"The Professional Approach"**, O(1) regardless of how many rules
   exist.

Rather than pick one and ignore the other, this project uses **both, in
the place each is actually good at**:

- **Control flow** (`ChatbotSession._read_input` / `run`): a small,
  fixed, binary decision — "should the loop keep going, or stop?" — uses
  an explicit `if sanitized in EXIT_COMMANDS:` check. This is exactly the
  `while True: ... if user_input == 'exit': break` pattern shown in the
  "Heartbeat" diagram. An if-else chain here is not just acceptable, it's
  the right tool: there are only three exit synonyms and they never grow
  in an unbounded way.

- **Intent / response resolution** (`KnowledgeBase.match_exact`,
  `ResponseEngine.generate_response`): an open-ended, growing set of
  rules — this is exactly the case the deck warns will turn into an
  unmaintainable if-elif ladder as it scales. It uses dictionary lookups
  (`self._trigger_index.get(...)`), matching the "Professional Approach"
  slide's `.get()` pattern, generalized to map a trigger phrase to an
  intent name.

This reflects an explicit engineering judgment: **if-else for a small,
stable set of control decisions; dictionary lookup for a large, growing
set of data-driven rules.** It satisfies the letter of the "use if-else"
requirement without shipping the exact anti-pattern the same document
spends four slides warning against.

## Why the knowledge base lives in JSON, not Python

`data/knowledge_base.json` is data, not code. Keeping it out of the
Python source means:

- The conclusion slide's suggestion to "expand the bot's vocabulary" is a
  one-file edit, not a code change — no risk of introducing a bug in
  `response_engine.py` just to add a new greeting synonym.
- The knowledge base is validated once, at load time
  (`KnowledgeBase._load`), so a malformed edit fails fast with a clear
  error message instead of causing a silent `KeyError` mid-conversation.
- It sets up a natural extension point (see "Future Improvements" in the
  README) — e.g. swapping in a different JSON file for a different bot
  personality without touching any Python.

## Two-stage intent matching

1. **Exact match** (`match_exact`): the sanitized input, verbatim, is a
   registered trigger phrase. O(1) dictionary lookup.
2. **Keyword match** (`match_keywords`): used only if (1) misses. Splits
   the input into tokens and looks for an intent where *all* the words of
   one of its trigger phrases appear in the input (e.g. trigger `"good
   morning"` matches input `"good morning everyone"`). Among intents that
   qualify, the one whose matching trigger has the most words wins, which
   naturally prefers more specific phrases over generic ones.
3. **Fallback**: if neither stage matches, a default "I don't understand"
   response is returned. The chatbot is guaranteed to never have "nothing
   to say."

## Error handling strategy

- `KnowledgeBase` raises `KnowledgeBaseError` (a `ChatbotError` subclass)
  for every way the data file can be wrong: missing file, invalid JSON,
  missing keys, empty trigger/response lists, or two intents claiming the
  same trigger phrase. Validation happens once, at startup.
- `main.py` catches `ChatbotError` specifically at startup and prints a
  clean, user-facing message instead of a stack trace, then exits with a
  non-zero status code (so the failure is scriptable/CI-detectable).
- `ChatbotSession` catches `EOFError` and `KeyboardInterrupt` around the
  single `input()` call and turns both into a graceful farewell message
  instead of letting either propagate as an unhandled exception.
- A top-level `except Exception` in `main.py` is a last-resort safety net
  around `session.run()`, logging the full traceback to the session log
  file while showing the user a short, non-technical message.

## Forward-looking note: this *is* a guardrail layer

One of the later slides ("The Modern Application: AI Guardrails") frames
a rule-based engine like this one as the deterministic filter that sits
in front of a probabilistic LLM in production systems (the same role
played by frameworks like NVIDIA NeMo Guardrails or Llama Guard). The
`ResponseEngine` in this project is structured so that its "no match"
branch — currently a canned fallback string — is the exact seam where a
future LLM call would plug in, without changing anything about how exact
or keyword matches are resolved. That extension is deliberately *not*
implemented here (it's out of scope for Project 1), but the separation
between `KnowledgeBase` (rules), `ResponseEngine` (decision), and
`ChatbotSession` (I/O) is what makes it a clean addition later rather
than a rewrite.
