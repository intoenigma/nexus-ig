import os
import urllib.parse

from ..app import console
from ..services.provider import InstagramProvider


def clean_session_id(val: str) -> str:
    """Clean sessionid from quotes, whitespace, key=value, or URL-encoding."""
    if not val:
        return ""
    val = val.strip().strip('"').strip("'")
    if "sessionid=" in val:
        parts = val.split("sessionid=")
        if len(parts) > 1:
            val = parts[1].split(";")[0].strip()
    val = urllib.parse.unquote(val).strip().strip('"').strip("'")
    return val


def save_sessionid_to_env(sessionid: str, env_path: str = ".env"):
    """Automatically persist SESSIONID to .env file so the user is never prompted again."""
    clean_id = clean_session_id(sessionid)
    if not clean_id:
        return
    try:
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

        updated = False
        new_lines = []
        for line in lines:
            if line.startswith("SESSIONID="):
                new_lines.append(f"SESSIONID={clean_id}\n")
                updated = True
            else:
                new_lines.append(line)

        if not updated:
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines.append("\n")
            new_lines.append(f"SESSIONID={clean_id}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception as exc:
        console.warning(f"Could not update .env: {exc}")


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
    sessionid_env = clean_session_id(os.getenv("SESSIONID", "").strip())

    # 1. Try saved session.json first
    if os.path.exists(session_path):
        console.status("SESSION", f"Loading session settings from {session_path}")
        try:
            cl.load_settings(session_path)
            my_pk, my_username = get_account_identity(cl)
            if my_pk and my_pk != "bot":
                console.success(f"Session loaded successfully for @{my_username} (ID: {my_pk})")
                # Auto-sync sessionid to .env if available
                if cl.sessionid:
                    save_sessionid_to_env(cl.sessionid)
                return cl, my_pk, my_username
        except Exception as exc:
            console.error(f"Saved session loading failed: {exc}")

    # 2. Try SESSIONID from .env
    if sessionid_env and not sessionid_env.startswith("<"):
        console.status("SESSION", "Authenticating via SESSIONID from .env...")
        try:
            cl.login_by_sessionid(sessionid_env)
            cl.dump_settings(session_path)
            save_sessionid_to_env(sessionid_env)
            my_pk, my_username = get_account_identity(cl)
            if my_pk and my_pk != "bot":
                console.success(f"Session saved to {session_path} for @{my_username}")
                return cl, my_pk, my_username
        except Exception as exc:
            console.warning(f"SESSIONID from .env failed: {exc}")

    # 3. Try Username/Password from .env
    if username_env and password_env and not username_env.startswith("<"):
        console.warning(f"Attempting credential login for '@{username_env}'...")
        try:
            cl.login(username_env, password_env)
            cl.dump_settings(session_path)
            if cl.sessionid:
                save_sessionid_to_env(cl.sessionid)
            my_pk, my_username = get_account_identity(cl)
            console.success(f"Fresh session saved to {session_path}")
            return cl, my_pk, my_username
        except Exception as exc:
            console.error(f"Credential login failed: {exc}")

    console.error("Authentication failed. Session expired or missing.")
    console.warning("Run 'python login.py' to log in interactively.")
    return None, None, None


