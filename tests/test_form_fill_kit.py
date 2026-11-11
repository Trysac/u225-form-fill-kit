"""Tests for form_fill_kit covering the acceptance criteria and edge cases."""

from __future__ import annotations

import json
from collections.abc import Sequence
from types import MappingProxyType

import pytest

from form_fill_kit import (
    Draft,
    FakeLLM,
    Field,
    FormError,
    Issue,
    Message,
    RecordedLLM,
    RecordingExhaustedError,
    SubmitResult,
    fill,
    propose_values,
    submit,
)


class _YesConfirmer:
    def __init__(self) -> None:
        self.seen: list[str] = []

    def ask(self, summary: str) -> bool:
        self.seen.append(summary)
        return True


class _NoConfirmer:
    def __init__(self) -> None:
        self.seen: list[str] = []

    def ask(self, summary: str) -> bool:
        self.seen.append(summary)
        return False


class _RaisingConfirmer:
    def ask(self, summary: str) -> bool:
        raise RuntimeError("confirmer boom")


def test_fill_acceptance_valid() -> None:
    fields = [
        Field("name", "text"),
        Field("email", "email"),
        Field("age", "int", min_value=18, max_value=120),
    ]
    draft = fill(
        fields, {"name": " Ana Lopez ", "email": "ana@example.com", "age": "30"}, form_id="signup"
    )
    assert dict(draft.values) == {"name": "Ana Lopez", "email": "ana@example.com", "age": 30}
    assert draft.issues == ()
    assert draft.digest == "21dfc1b097d17a24465193a57caa2e065b5e5998ea798dccf370e6e2797bf9a1"


def test_fill_acceptance_issues_sorted() -> None:
    fields = [
        Field("name", "text"),
        Field("email", "email"),
        Field("age", "int", min_value=18, max_value=120),
    ]
    draft = fill(
        fields,
        {"age": "17", "email": "ana@", "role": "admin"},
        form_id="signup",
    )
    assert draft.issues == (
        Issue("age", "out_of_range"),
        Issue("email", "invalid_email"),
        Issue("name", "required"),
        Issue("role", "unknown_field"),
    )


def test_summary_and_sensitive() -> None:
    fields = [
        Field("name", "text"),
        Field("email", "email"),
        Field("age", "int", min_value=18, max_value=120),
        Field("id_number", "text", sensitive=True),
    ]
    draft = fill(
        fields,
        {"name": "Ana Lopez", "email": "ana@example.com", "age": 30, "id_number": "AB123456"},
        form_id="signup",
    )
    expected = "Name: Ana Lopez\nEmail: ana@example.com\nAge: 30\nId number: ****3456"
    assert draft.summary() == expected

    short_draft = fill(fields, {"id_number": "AB"}, form_id="short")
    line = [ln for ln in short_draft.summary().splitlines() if ln.startswith("Id number")]
    assert line == ["Id number: ****"]


def test_submit_true_calls_sink_once_and_returns_submitted() -> None:
    fields = [Field("name", "text"), Field("email", "email"), Field("age", "int")]
    draft = fill(fields, {"name": "Ana", "email": "a@b.com", "age": 30}, form_id="signup")
    calls: list[dict[str, object]] = []
    confirmer = _YesConfirmer()
    events: list[dict[str, str]] = []

    result = submit(draft, calls.append, confirmer, on_event=events.append)

    assert result == SubmitResult(status="submitted", digest=draft.digest)
    assert calls == [{"name": "Ana", "email": "a@b.com", "age": 30}]
    assert confirmer.seen == [draft.summary()]
    assert len(events) == 1
    assert events[0] == {"event": "submitted", "form_id": "signup", "digest": draft.digest}


def test_submit_false_returns_rejected_and_does_not_call_sink() -> None:
    fields = [Field("name", "text")]
    draft = fill(fields, {"name": "Ana"}, form_id="signup")
    calls: list[dict[str, object]] = []
    events: list[dict[str, str]] = []
    confirmer = _NoConfirmer()

    result = submit(draft, calls.append, confirmer, on_event=events.append)

    assert result.status == "rejected"
    assert result.digest == draft.digest
    assert confirmer.seen == [draft.summary()]
    assert calls == []
    assert events == [{"event": "rejected", "form_id": "signup"}]


def test_submit_invalid_draft_returns_invalid_without_asking() -> None:
    fields = [Field("name", "text", required=True)]
    draft = fill(fields, {}, form_id="signup")
    asked = False

    class Conf:
        def ask(self, summary: str) -> bool:
            nonlocal asked
            asked = True
            return True

    sink_called = False
    result = submit(draft, lambda data: None, Conf(), on_event=None)
    assert result.status == "invalid"
    assert result.digest == draft.digest
    assert asked is False
    assert sink_called is False


def test_submit_second_time_raises_already_submitted() -> None:
    fields = [Field("name", "text")]
    draft = fill(fields, {"name": "Ana"}, form_id="f")

    def sink(data: dict[str, object]) -> None:
        return None

    confirmer = _YesConfirmer()
    submit(draft, sink, confirmer)
    with pytest.raises(FormError) as exc_info:
        submit(draft, sink, confirmer)
    assert exc_info.value.code == "already_submitted"


def test_submit_sink_exception_marks_submitted() -> None:
    fields = [Field("name", "text")]
    draft = fill(fields, {"name": "Ana"}, form_id="f")

    def bad_sink(data: dict[str, object]) -> None:
        raise RuntimeError("sink boom")

    with pytest.raises(RuntimeError):
        submit(draft, bad_sink, _YesConfirmer())
    with pytest.raises(FormError) as exc_info:
        submit(draft, lambda data: None, _YesConfirmer())
    assert exc_info.value.code == "already_submitted"


def test_submit_rejects_draft_whose_digest_does_not_match_values() -> None:
    fields = [Field("name", "text")]
    shown = fill(fields, {"name": "Ana"}, form_id="f")
    tampered = Draft(
        form_id="f",
        values=MappingProxyType({"name": "Mallory"}),
        issues=(),
        digest=shown.digest,
        _fields=MappingProxyType({"name": fields[0]}),
    )
    calls: list[dict[str, object]] = []

    with pytest.raises(FormError) as exc_info:
        submit(tampered, calls.append, _YesConfirmer())

    assert exc_info.value.code == "invalid_form"
    assert calls == []


def test_submit_confirmer_exception_propagates_and_does_not_mark_submitted() -> None:
    fields = [Field("name", "text")]
    draft = fill(fields, {"name": "Ana"}, form_id="f")
    sink_called = False

    def sink(data: dict[str, object]) -> None:
        nonlocal sink_called
        sink_called = True

    with pytest.raises(RuntimeError):
        submit(draft, sink, _RaisingConfirmer())
    assert sink_called is False
    # Draft is not marked submitted; a subsequent submit with yes confirmer should work.
    submit(draft, sink, _YesConfirmer())
    assert sink_called is True


def test_propose_values_acceptance() -> None:
    fields = [Field("name", "text"), Field("age", "int"), Field("email", "email")]
    llm = RecordedLLM(['{"name": "Ana Lopez", "age": 30}'])
    result = propose_values(fields, "Hi, I am Ana Lopez, 30, ana@example.com", llm)
    assert result == {"name": "Ana Lopez", "age": 30}


def test_propose_values_invalid_json_raises() -> None:
    fields = [Field("name", "text")]
    llm = RecordedLLM(["not json"])
    with pytest.raises(FormError) as exc_info:
        propose_values(fields, "text", llm)
    assert exc_info.value.code == "invalid_proposal"


def test_propose_values_source_too_large() -> None:
    fields: list[Field] = []
    llm = RecordedLLM([])
    with pytest.raises(FormError) as exc_info:
        propose_values(fields, "a" * 20_001, llm)
    assert exc_info.value.code == "input_too_large"


def test_propose_values_code_fence_stripping() -> None:
    fields = [Field("name", "text")]
    llm = RecordedLLM(['```json\n{"name": "Ana"}\n```'])
    assert propose_values(fields, "text", llm) == {"name": "Ana"}


def test_propose_values_drops_unknown_keys() -> None:
    fields = [Field("name", "text")]
    llm = RecordedLLM(['{"name": "Ana", "evil": "x"}'])
    assert propose_values(fields, "text", llm) == {"name": "Ana"}


def test_propose_values_rejects_non_object() -> None:
    fields = [Field("name", "text")]
    llm = RecordedLLM(["[1,2,3]"])
    with pytest.raises(FormError) as exc_info:
        propose_values(fields, "text", llm)
    assert exc_info.value.code == "invalid_proposal"


def test_propose_values_rejects_too_deep() -> None:
    fields = [Field("name", "text")]
    deep = '{"a":' * 9 + "1" + "}" * 9
    llm = RecordedLLM([deep])
    with pytest.raises(FormError) as exc_info:
        propose_values(fields, "text", llm)
    assert exc_info.value.code == "invalid_proposal"


def test_propose_values_rejects_deeply_nested_reply() -> None:
    fields = [Field("name", "text")]
    llm = RecordedLLM(["[" * 2000 + "]" * 2000])
    with pytest.raises(FormError) as exc_info:
        propose_values(fields, "text", llm)
    assert exc_info.value.code == "invalid_proposal"


def test_propose_values_rejects_too_long_reply() -> None:
    fields = [Field("name", "text")]
    long_json = '{"name": "' + "a" * 100_000 + '"}'
    llm = RecordedLLM([long_json])
    with pytest.raises(FormError) as exc_info:
        propose_values(fields, "text", llm)
    assert exc_info.value.code == "invalid_proposal"


def test_recorded_llm_exhausts() -> None:
    llm = RecordedLLM(["one", "two"])
    assert llm.complete([], max_tokens=1) == "one"
    assert llm.complete([], max_tokens=1) == "two"
    with pytest.raises(RecordingExhaustedError):
        llm.complete([], max_tokens=1)


def test_fake_llm() -> None:
    def fn(messages: Sequence[Message]) -> str:
        return messages[0]["content"]

    llm = FakeLLM(fn)
    msgs: list[Message] = [{"role": "system", "content": "hello"}]
    assert llm.complete(msgs, max_tokens=1) == "hello"


def test_field_validation_edges() -> None:
    # too long text
    fields = [Field("txt", "text")]
    draft = fill(fields, {"txt": "a" * 201}, form_id="f")
    assert Issue("txt", "too_long") in draft.issues

    # control character
    draft = fill(fields, {"txt": "abc\x00def"}, form_id="f")
    assert Issue("txt", "invalid_text") in draft.issues

    # int bool
    fields_int = [Field("n", "int")]
    draft = fill(fields_int, {"n": True}, form_id="f")
    assert Issue("n", "invalid_type") in draft.issues


def test_optional_field_omitted_and_choice_and_invalid_date() -> None:
    fields = [
        Field("name", "text"),
        Field("nickname", "text", required=False),
        Field("color", "choice", choices=("red", "blue")),
        Field("dob", "date"),
    ]
    draft = fill(fields, {"name": "Ana", "color": "red", "dob": "2026-02-30"}, form_id="f")
    assert "nickname" not in draft.values
    assert "color" in draft.values
    assert Issue("dob", "invalid_date") in draft.issues


def test_unicode_digest_ensure_ascii_false() -> None:
    fields = [Field("value", "text")]
    draft = fill(fields, {"value": "héllo"}, form_id="f")
    expected_payload = json.dumps(
        {"form_id": "f", "values": {"value": "héllo"}},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    import hashlib

    expected = hashlib.sha256(expected_payload.encode("utf-8")).hexdigest()
    assert draft.digest == expected


def test_invalid_form_conditions() -> None:
    with pytest.raises(FormError) as exc_info:
        fill([Field("Name", "text")], {}, form_id="f")
    assert exc_info.value.code == "invalid_form"

    with pytest.raises(FormError) as exc_info:
        fill([Field("a", "text"), Field("a", "text")], {}, form_id="f")
    assert exc_info.value.code == "invalid_form"

    many_fields = [Field(f"f{i}", "text") for i in range(101)]
    with pytest.raises(FormError) as exc_info:
        fill(many_fields, {}, form_id="f")
    assert exc_info.value.code == "invalid_form"


def test_on_event_payloads_do_not_contain_values() -> None:
    fields = [Field("name", "text", sensitive=True)]
    draft = fill(fields, {"name": "secret"}, form_id="f")
    events: list[dict[str, str]] = []
    submit(draft, lambda data: None, _YesConfirmer(), on_event=events.append)
    assert events
    for event in events:
        assert "secret" not in json.dumps(event)

    # rejected
    fields2 = [Field("name", "text")]
    draft2 = fill(fields2, {"name": "secret"}, form_id="f2")
    events.clear()
    submit(draft2, lambda data: None, _NoConfirmer(), on_event=events.append)
    assert "secret" not in json.dumps(events[0])
