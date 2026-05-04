import secrets
import html

def generate_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)

def sanitize_input(text: str) -> str:
    """Escape HTML special characters to prevent XSS."""
    return html.escape(text)
