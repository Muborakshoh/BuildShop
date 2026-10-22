import json
from typing import Any

from pydantic import field_validator


def validate_translations_json(value: str | None) -> str | None:
    if value in (None, ""):
        return None
    try:
        parsed: Any = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError("translations must be valid JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("translations must be a JSON object")
    for key, text in parsed.items():
        if not isinstance(key, str) or not isinstance(text, str):
            raise ValueError("translations keys and values must be strings")
    return json.dumps(parsed, ensure_ascii=False)


def translations_validator(*fields: str):
    @field_validator(*fields)
    @classmethod
    def _validate(cls, value: str | None) -> str | None:
        return validate_translations_json(value)

    return _validate
