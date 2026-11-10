# trysac-form-fill-kit

[![PyPI version](https://badge.fury.io/py/trysac-form-fill-kit.svg)](https://pypi.org/project/trysac-form-fill-kit/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Agents that fill forms produce values that are almost right and submit them without a person seeing what is sent. This library validates proposed values against typed fields, renders a summary for a human, binds the confirmation to a SHA-256 digest of the exact normalized values, and submits a draft at most once. It uses only the Python standard library.

## Installation

```sh
pip install trysac-form-fill-kit
```

## Usage

```python
from form_fill_kit import Field, RecordedLLM, fill, propose_values, submit

fields = [
    Field("name", "text"),
    Field("email", "email"),
    Field("age", "int", min_value=18, max_value=120),
]
proposal = propose_values(
    fields, "Ana Lopez, 30, ana@example.com", RecordedLLM(['{"name": "Ana Lopez", "age": 30}'])
)
draft = fill(fields, {**proposal, "email": "ana@example.com"}, form_id="signup")


class Confirm:
    def ask(self, summary):
        return True


result = submit(draft, lambda values: None, Confirm())
print(result.status)  # submitted
```

`propose_values` only extracts candidate values; `fill` validates and normalizes them. `submit` calls `confirmer.ask(draft.summary())`, recomputes the digest from `draft.values`, marks the draft submitted, and then calls `sink(dict(values))` once.

## Public API

- `Field(name, type, required=True, label=None, choices=(), max_length=200, min_value=None, max_value=None, sensitive=False)` - field descriptor. `type` is one of `text`, `email`, `int`, `date`, `choice`, `bool`. Field names must match `^[a-z][a-z0-9_]{0,63}$` and be unique; at most 100 fields.
- `fill(fields, values, *, form_id)` - validates and normalizes `values`, returning an immutable `Draft`. Issues are sorted by field name, then code. Invalid field lists raise `FormError('invalid_form')`.
- `Draft` - exposes `form_id`, `values` (read-only mapping of normalized values), `issues`, `digest`, and `summary()`. `summary()` renders one `Label: value` line per present value; sensitive values show `****` plus their last four characters when longer than four, otherwise `****`; booleans render as `yes`/`no`.
- `submit(draft, sink, confirmer, *, on_event=None)` - returns `SubmitResult(status, digest)`. A draft with issues returns `'invalid'` without asking. A rejected confirmation returns `'rejected'`. A confirmed draft is marked submitted before `sink(dict(values))`; sink exceptions propagate, and the draft cannot be submitted again (`FormError('already_submitted')`). If the digest does not match the current values, raises `FormError('invalid_form')`.
- `propose_values(fields, source_text, llm, *, max_tokens=512)` - asks an `LLMPort` for a JSON object and drops keys that are not fields. Values are not validated here. `source_text` is limited to 20,000 characters; replies are limited to 100,000 characters and nesting depth 8.
- Protocols and helpers: `LLMPort.complete(messages, *, max_tokens) -> str`, `Confirmer.ask(summary) -> bool`, `RecordedLLM(replies)`, `FakeLLM(fn)`, `SubmitResult`, `Issue(field, code)`, `Message`.

### Validation issue codes

`required`, `unknown_field`, `invalid_text`, `too_long`, `invalid_email`, `invalid_type`, `out_of_range`, `invalid_date`, `invalid_choice`.

### Errors and limits

`FormError` carries a stable `code`: `invalid_form`, `invalid_proposal`, `already_submitted`, or `input_too_large`. `RecordedLLM` raises `RecordingExhaustedError` when its recorded replies run out. `propose_values` raises `input_too_large` above 20,000 source characters and `invalid_proposal` for replies that are not a usable JSON object. Email validation is deliberately a simple pattern, not full RFC 5322. Date values are validated as `YYYY-MM-DD` strings and kept as strings.

## Why not a plain approval gate

A plain approval gate confirms a summary but does not tie the confirmation to the values that are later submitted, and it does not make submission single-use. Here the confirmation is checked against a SHA-256 digest recomputed from the exact normalized values, and the draft is marked submitted before the sink runs. A second submit raises `FormError('already_submitted')`.

## Documentation

See [docs/PROJECT.md](docs/PROJECT.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/TESTING.md](docs/TESTING.md), and [docs/SECURITY.md](docs/SECURITY.md).
