# Testing

## Running

```sh
python -m pytest tests/test_form_fill_kit.py
```

## Policy

The suite in `tests/test_form_fill_kit.py` exercises the public API from `form_fill_kit`. It uses `fill`, `submit`, `propose_values`, `Field`, `Draft`, `Issue`, `FormError`, `RecordedLLM`, and `FakeLLM`, plus the local confirmer helpers `_YesConfirmer`, `_NoConfirmer`, and `_RaisingConfirmer`. Tests assert return values, issue tuples, digests, summary text, sink calls and raised `FormError` codes. They use no network and no wall clock.

The file contains these test functions:

- `test_fill_acceptance_valid` - acceptance example values, empty issues and exact digest.
- `test_fill_acceptance_issues_sorted` - required, invalid email, out-of-range and unknown-field issues sorted by field name.
- `test_summary_and_sensitive` - summary lines and sensitive-value masking.
- `test_submit_true_calls_sink_once_and_returns_submitted` - confirmation, one sink call, `SubmitResult`, and events.
- `test_submit_false_returns_rejected_and_does_not_call_sink` - rejection result and no sink call.
- `test_submit_invalid_draft_returns_invalid_without_asking` - invalid draft returns `invalid` and the confirmer is not asked.
- `test_submit_second_time_raises_already_submitted` - a second submit raises `FormError('already_submitted')`.
- `test_submit_sink_exception_marks_submitted` - sink exception propagates and the draft is marked submitted.
- `test_submit_rejects_draft_whose_digest_does_not_match_values` - a tampered digest raises `FormError('invalid_form')`.

## Tiers

Only the local pytest suite is present. No conformance-marked tests, external-tool downloads, `conftest.py`, or CI tier files are included in the supplied repository.

## Layout

- `tests/test_form_fill_kit.py` - all tests.
- `src/form_fill_kit/__init__.py` - package under test.
- `src/form_fill_kit/py.typed` - typing marker.
