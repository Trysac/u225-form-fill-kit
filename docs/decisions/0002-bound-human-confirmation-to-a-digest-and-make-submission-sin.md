# Bound human confirmation to a digest and make submission single-use

Status: accepted (generated, pending human review)

## Context

Agents produce form values that are almost right and may submit without human review. A confirmation step only protects if the submitted values are exactly the ones confirmed and a draft cannot be reused.

## Decision

Implement typed field validation, an immutable Draft whose summary is presented to a human, a SHA-256 digest computed over the canonical JSON of form_id and normalized values, and a submit function that asks the confirmer, marks the draft submitted before calling the sink, and raises on any second submit.

## Consequences

Drafts are tamper-evident within the library's flow, submission is at-most-once even if the sink raises, and events never contain field values. LLM-proposed values are kept separate from validation and submission.
