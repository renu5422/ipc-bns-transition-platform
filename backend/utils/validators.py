import re

def validate_search_query(query: str) -> bool:
    """Reject empty or suspiciously long queries."""
    if not query or not query.strip():
        return False
    if len(query) > 200:
        return False
    return True

def validate_username(username: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9_]{3,32}$', username))
