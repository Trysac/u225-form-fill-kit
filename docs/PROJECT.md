# Project record

## Objective

Fill forms from agent-proposed values with typed validation, a human confirmation summary bound to a SHA-256 digest of the exact values, and single-use submission.

## Scope

In scope:

- `Field` descriptors for `text`, `email`, `int`, `date`, `choice`, and `bool`, with required, label, choices, max_length, min_value, max_value and sensitive options.
- `fill`, which validates and normalizes values into an immutable `Draft`, reports sorted `Issue`s and computes the SHA-256 digest over canonical JSON.
- `Draft.summary()` for human confirmation, including masking of sensitive fields.
- `submit`, which asks a `Confirmer`, verifies the digest against current values, marks the draft submitted, calls the sink once, and emits optional events.
- `propose_values` with the `LLMPort` protocol plus `RecordedLLM` and `FakeLLM` helpers; it extracts candidate values and drops unknown keys.
- `FormError` codes and typed protocols.

Out of scope:

- Rendering HTML forms.
- Browser automation.
- File uploads.
- Persistence of drafts.
- Runtime dependencies beyond the Python standard library.
- Full RFC 5322 email validation.

## Timeline

| Date | Event |
|---|---|
| 2026 | Repository created from the factory utility template. |

## Effort metrics

Only measured values are recorded; a value that has not been measured remains pending measurement.

| Metric | Value |
|---|---|
| Tokens (input / output) | 509431 / 53897 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.0844 |

## Factory run u225 (measured from API usage)

| Date (UTC) | Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| 2026-11-10 | generation | deepseek-v4-pro | yes | 2242 | 19881 | 0 | 3200 | 0.0409 |
| 2026-11-10 | fix-1 | deepseek-flash | no | 9754 | 528 | 0 | 22272 | 0.0018 |
| 2026-11-10 | audit | deepseek-flash | no | 19971 | 15236 | 0 | 182656 | 0.0127 |
| 2026-11-10 | fix-2 | deepseek-flash | no | 11544 | 4829 | 0 | 152064 | 0.0051 |
| 2026-11-10 | docs | deepseek-flash | no | 105472 | 13423 | 0 | 256 | 0.0239 |

Total: $0.0844. Prices: deepseek line, as measured by its adapter. Providers serve the current version of each model id, so the date tells which version answered; versions, launch stages and price sources per line are in the factory's model register (docs/MODELS.md).
