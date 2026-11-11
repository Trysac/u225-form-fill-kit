# Stack

## Used

| Tool | Why |
|---|---|
| Python >= 3.10 | The code uses modern typing syntax, dataclasses, `MappingProxyType`, and standard-library modules only. |
| Python standard library | `hashlib`, `json`, `logging`, `re`, `unicodedata`, `collections.abc`, `dataclasses`, `datetime`, `types`, and `typing` implement validation, digesting, summaries and the LLM port. |
| pytest | The supplied test module `tests/test_form_fill_kit.py` is collected by pytest. |

## Discarded

No third-party runtime dependencies or alternative build, lint or formatting tools are declared in the supplied code. Email validation uses the implemented simple pattern rather than a full RFC 5322 parser.
