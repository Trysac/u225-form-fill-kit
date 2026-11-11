# Architecture

## Purpose

`trysac-form-fill-kit` is a standard-library Python package that validates agent-proposed form values, produces an immutable `Draft` with a SHA-256 digest of the normalized values and a human summary, and submits the draft at most once after confirmation.

## Shape

```text
caller code -> form_fill_kit (public API in __init__.py)
                    |
                    +-- Field -> fill -> Draft -> submit -> sink
                    +-- propose_values -> LLMPort -> dict
```

- **Public API**: the names in `__all__` of `src/form_fill_kit/__init__.py`: `Confirmer`, `Draft`, `ErrorCode`, `FakeLLM`, `Field`, `FieldType`, `FormError`, `Issue`, `LLMPort`, `Message`, `RecordedLLM`, `RecordingExhaustedError`, `SubmitResult`, `fill`, `propose_values`, `submit`.
- **Validation**: `fill` checks field definitions, validates each value, normalizes stored values, collects `Issue`s sorted by field name and code, and computes the digest over canonical JSON.
- **Side effects**: the library performs no network, filesystem or browser I/O. `submit` calls the caller-supplied `sink` after marking the draft submitted, and `propose_values` calls the caller-supplied `LLMPort`. `on_event` receives only event, form_id and digest.
- **Errors**: `FormError` carries one of `invalid_form`, `invalid_proposal`, `already_submitted`, `input_too_large`. `RecordedLLM` raises `RecordingExhaustedError` when its replies run out.
- **Dependencies**: Python standard library only; the package ships `py.typed`.

## Quality contract

The supplied repository contains a pytest suite in `tests/test_form_fill_kit.py`. That suite exercises the public API, issue codes, digest binding, summary rendering, single-use submission, sink exceptions, and LLM proposal handling. No separate check script or factory metadata file is present in the supplied code.

## Decisions

No ADR files are included in the supplied repository. The behavioural decisions are embodied in the module docstrings, function docstrings and tests in `src/form_fill_kit/__init__.py` and `tests/test_form_fill_kit.py`.
