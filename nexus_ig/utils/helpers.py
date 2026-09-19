"""Common string & formatting helpers."""
import datetime

def clean_username(username: str) -> str:
    return (username or "").strip().lstrip("@")

def extract_usernames(text: str) -> list[str]:
    return [clean_username(part) for part in text.replace(",", " ").split() if part.strip()]

def find_sender_name(thread, user_id) -> str:
    for user in getattr(thread, "users", []):
        if str(user.pk) == str(user_id):
            return user.username
    return "User"

def format_timestamp(ts: float = None) -> str:
    now = datetime.datetime.fromtimestamp(ts) if ts else datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")
