"""Instagram Group thread helpers."""

def is_group_thread(thread) -> bool:
    return getattr(thread, "thread_type", None) == "group" or len(getattr(thread, "users", [])) > 1
