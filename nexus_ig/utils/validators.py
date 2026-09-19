"""Validation helpers."""

def is_valid_thread_id(thread_id: str) -> bool:
    return bool(thread_id and str(thread_id).isdigit())
