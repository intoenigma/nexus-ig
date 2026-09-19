import os

from ..core import console
from ..services.provider import InstagramProvider


def clean_username(username):
    return (username or "").strip().lstrip("@")


def is_group_thread(thread):
    return getattr(thread, "thread_type", None) == "group" or len(getattr(thread, "users", [])) > 1


def find_sender_name(thread, user_id):
    for user in getattr(thread, "users", []):
        if str(user.pk) == str(user_id):
            return user.username
    return "User"


def extract_usernames(text):
    return [clean_username(part) for part in text.replace(",", " ").split() if part.strip()]


def resolve_user_ids(cl, usernames):
    user_ids = []
    missing = []
    for username in usernames:
        if not username:
            continue
        try:
            user_ids.append(int(cl.user_id_from_username(username)))
        except Exception:
            missing.append(username)
    return user_ids, missing


def get_account_identity(cl):
    my_pk = str(getattr(cl, "user_id", "") or getattr(cl.client, "user_id", "") or "")
    username = str(getattr(cl, "username", "") or getattr(cl.client, "username", "") or "")
    return (my_pk if my_pk != "None" else "bot"), (username if username != "None" else "bot")


def login_client(config):
    """Smart Session Loader: Loads & syncs session settings smoothly."""
    cl = InstagramProvider(config)
    session_path = config.session_file
    username_env = os.getenv("INSTAGRAM_USERNAME", "").strip()
    password_env = os.getenv("INSTAGRAM_PASSWORD", "").strip()

    if os.path.exists(session_path):
        console.status("SESSION", f"Loading session settings from {session_path}")
        try:
            cl.load_settings(session_path)
            if hasattr(cl, "sessionid") and cl.sessionid:
                try:
                    cl.login_by_sessionid(cl.sessionid)
                except Exception:
                    pass
            my_pk, my_username = get_account_identity(cl)
            if my_pk and my_pk != "bot":
                console.success(f"Session loaded successfully for @{my_username} (ID: {my_pk})")
                return cl, my_pk, my_username
        except Exception as exc:
            console.error(f"Saved session loading failed: {exc}")

    if username_env and password_env and not username_env.startswith("<"):
        console.warning(f"Attempting credential login for '{username_env}'...")
        try:
            cl.login(username_env, password_env)
            cl.dump_settings(session_path)
            my_pk, my_username = get_account_identity(cl)
            console.success(f"Fresh session saved to {session_path}")
            return cl, my_pk, my_username
        except Exception as exc:
            console.error(f"Credential login failed: {exc}")

    console.error("Authentication failed. Session expired or missing.")
    console.warning("Run 'python login.py' to refresh your sessionid cookie.")
    return None, None, None
