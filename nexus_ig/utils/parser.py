"""Command argument parser."""

def parse_command_tail(text: str, prefix: str) -> str:
    lower_text = text.strip().lower()
    prefix_lower = prefix.strip().lower()
    if lower_text.startswith(prefix_lower):
        return text.strip()[len(prefix_lower):].strip()
    return text.strip()
