"""Custom validators for Pydantic models."""

import re
from typing import Any

from pydantic_core import PydanticCustomError


EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)


def validate_email(value: Any) -> str:
    """Validate email, allowing .local and other non-standard domains."""
    if not isinstance(value, str):
        raise PydanticCustomError("email_type", "Value must be a string")
    if not EMAIL_PATTERN.match(value):
        raise PydanticCustomError("email_format", "Invalid email format")
    return value.lower().strip()
