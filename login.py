import os
from dotenv import load_dotenv

from nexus_ig.core import console
from nexus_ig.services.provider import InstagramProvider


def login_helper():
    load_dotenv()
    session_file = os.getenv("SESSION_FILE", "session.json")
    username_env = os.getenv("INSTAGRAM_USERNAME", "").strip()
    password_env = os.getenv("INSTAGRAM_PASSWORD", "").strip()
    sessionid_env = os.getenv("SESSIONID", "").strip()

    cl = InstagramProvider()

    # 1. Try username & password from .env first
    if username_env and password_env and not username_env.startswith("<"):
        console.status("LOGIN", f"Attempting automatic login for @{username_env} using .env credentials...")
        try:
            cl.login(username_env, password_env)
            cl.dump_settings(session_file)
            my_pk = str(getattr(cl, "user_id", "") or getattr(cl.client, "user_id", ""))
            my_user = str(getattr(cl, "username", "") or getattr(cl.client, "username", ""))
            console.success(f"Successfully logged in as @{my_user or username_env} (ID: {my_pk})!")
            console.success(f"Session saved to {session_file}")
            console.status("NEXT", "Run python main.py")
            return
        except Exception as exc:
            console.warning(f"Username/Password login failed: {exc}")
            console.status("FALLBACK", "Falling back to Session ID authentication...")

    # 2. Try SESSIONID from .env if present
    if sessionid_env and not sessionid_env.startswith("<"):
        console.status("SESSION", "Trying SESSIONID from .env...")
        try:
            cl.login_by_sessionid(sessionid_env)
            cl.dump_settings(session_file)
            my_user = str(getattr(cl, "username", "") or getattr(cl.client, "username", ""))
            console.success(f"Session saved to {session_file} (@{my_user})")
            console.status("NEXT", "Run python main.py")
            return
        except Exception as exc:
            console.warning(f"Session ID from .env failed: {exc}")

    # 3. Interactive prompt as final fallback
    console.login_screen()
    sessionid = input("\nPaste your sessionid here: ").strip()
    if not sessionid:
        console.error("No session ID provided.")
        return

    try:
        console.status("SESSION", "Validating session ID")
        cl.login_by_sessionid(sessionid)
        console.status("SESSION", "Verifying account")
        my_pk = str(getattr(cl, "user_id", "") or getattr(cl.client, "user_id", ""))
        username = str(getattr(cl, "username", "") or getattr(cl.client, "username", ""))
        cl.dump_settings(session_file)
        console.success(f"Session saved to {session_file} (@{username or my_pk})")
        console.status("NEXT", "Run python main.py")
    except Exception as exc:
        console.error(f"Session ID login failed: {exc}")
        console.warning("Make sure you copied the entire sessionid value correctly.")


if __name__ == "__main__":
    login_helper()
