# Security notes

## Threat model

The library performs no network, filesystem or browser I/O itself; `sink`, `Confirmer`, and `LLMPort` are caller-supplied. The relevant risks and the limits implemented in `src/form_fill_kit/__init__.py` are:

Defended:

- Invalid field definitions: `fill` rejects more than 100 fields, names that do not match `^[a-z][a-z0-9_]{0,63}$`, and duplicate names with `FormError('invalid_form')`.
- Untrusted values: text is stripped, control characters in Unicode category `Cc` are rejected, and length after stripping is limited by `max_length` (default 200); email must match a simple pattern and be at most 254 characters; ints accept an int or a string of at most 18 digits and respect `min_value`/`max_value`; dates must be valid `YYYY-MM-DD` strings; choices must be exact members; bool accepts only `True` or `False`.
- Confirmation binding: `submit` recomputes the SHA-256 digest from the draft's current normalized values and compares it with `draft.digest` before calling the sink. A mismatch raises `FormError('invalid_form')`, so the confirmed summary and the submitted values cannot diverge through a draft mutated outside `fill`.
- Single-use submission: the draft is marked submitted before `sink(dict(values))` is called. A second submit raises `FormError('already_submitted')`, and sink exceptions propagate after the draft is marked submitted (at-most-once behaviour).
- LLM proposal handling: `propose_values` limits source text to 20,000 characters, escapes `&`, `<` and `>` inside the `<source>` block, strips one surrounding code fence, checks the reply length at 100,000 characters, rejects replies that are not JSON objects, checks nesting depth with an iterative limit of 8, and drops keys that do not match a field. Values from the LLM are not trusted and are not submitted directly.
- Observability: `on_event` payloads contain only `event`, `form_id` and `digest`, never field values. `FormError` messages contain only the stable code, not values.
- Dependencies: the package uses only the Python standard library and installs a `NullHandler` on its logger.

Not defended:

- Transport, authentication, encryption, persistence and access control are outside the library. The caller is responsible for the sink, the confirmer implementation and any LLM port implementation.
- The digest is a content binding, not a secret or a MAC. It does not prove who created a draft and does not prevent an attacker who can already run code from constructing a `Draft` with matching values and digest.
- Sensitive fields are masked in `summary()` by showing `****` plus the last four characters when the value is longer than four, otherwise `****`. The full value remains in `draft.values` and is passed to the sink.
- Email validation is deliberately not full RFC 5322 and accepts only the implemented simple pattern.
- Prompt injection is mitigated by escaping the source text and by the system instruction that `<source>` content is data, but an LLM can still return misleading values. `propose_values` does not validate values; callers must use `fill` and human confirmation.
- Size limits are checked after the LLM reply is received. A malicious `LLMPort` implementation can allocate a large reply before `propose_values` checks its length.
- The draft's submitted flag is not protected by a lock. Concurrent `submit` calls on the same draft are not synchronized.
- HTML form rendering, browser automation, file uploads and draft persistence are out of scope.

## Publishing

The package has no runtime dependencies. The supplied repository contains no publishing credentials. Report vulnerabilities through the repository maintainers; do not include real form values in a report.
