"""Behavior tests for the public API of form_fill_kit."""

from __future__ import annotations

import pytest

import form_fill_kit


def test_normalize_trims_and_lowercases() -> None:
    assert form_fill_kit.normalize("  Hello World ") == "hello world"


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_normalize_rejects_blank_input(value: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        form_fill_kit.normalize(value)


def test_version_is_semver() -> None:
    parts = form_fill_kit.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
