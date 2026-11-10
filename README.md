# form-fill-kit

[![PyPI version](https://img.shields.io/pypi/v/trysac-form-fill-kit)](https://pypi.org/project/trysac-form-fill-kit/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-form-fill-kit)](LICENSE)
[![CI](https://github.com/Trysac/u225-form-fill-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u225-form-fill-kit/actions/workflows/ci.yml)

Fill forms from agent-proposed values with typed validation, a human confirmation summary bound to a SHA-256 digest of the exact values and single-use submission

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-form-fill-kit
# or
uv add trysac-form-fill-kit
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import form_fill_kit

# normalize() trims surrounding whitespace and lower-cases the text.
print(form_fill_kit.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    form_fill_kit.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
