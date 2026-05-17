import bleach

ALLOWED_TAGS = {
    "a",
    "b",
    "blockquote",
    "br",
    "code",
    "div",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "hr",
    "i",
    "img",
    "li",
    "ol",
    "p",
    "pre",
    "span",
    "strong",
    "u",
    "ul",
}

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title"],
    "*": ["class"],
}

ALLOWED_PROTOCOLS = {"http", "https", "mailto", "tel"}


def sanitize_html(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = bleach.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    return bleach.linkify(cleaned)
