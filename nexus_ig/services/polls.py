"""Group Polls service."""

def create_poll(title: str, options: list[str]) -> dict:
    return {
        "title": title,
        "options": options,
        "votes": {opt: 0 for opt in options}
    }
