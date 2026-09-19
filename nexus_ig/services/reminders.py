"""Scheduled events and birthday reminders service."""
import time

def process_due_reminders(storage) -> list[dict]:
    now = int(time.time())
    due = storage.get_due_schedules(now) if hasattr(storage, "get_due_schedules") else []
    return due
