"""
PPSC Crack — XSS Prevention with Bleach
=========================================
Sanitizes all user-generated content to prevent XSS attacks.
"""

import bleach

# Allowed tags and attributes for rich text (e.g. admin notes)
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'a', 'blockquote', 'code', 'pre', 'span',
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'rel'],
    'span': ['class'],
}

ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def sanitize_html(dirty: str) -> str:
    """Sanitize HTML content, allowing only safe tags/attributes."""
    return bleach.clean(
        dirty,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )


def sanitize_plain_text(text: str) -> str:
    """Strip ALL HTML tags — for plain text fields like names, titles."""
    return bleach.clean(text, tags=[], strip=True).strip()


def sanitize_dict(data: dict, html_fields: set[str] | None = None) -> dict:
    """
    Sanitize all string values in a dict.
    Fields in `html_fields` keep safe HTML; others are stripped to plain text.
    """
    html_fields = html_fields or set()
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            if key in html_fields:
                sanitized[key] = sanitize_html(value)
            else:
                sanitized[key] = sanitize_plain_text(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, html_fields)
        else:
            sanitized[key] = value
    return sanitized
