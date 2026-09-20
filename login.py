import getpass
import os
from dotenv import load_dotenv

from nexus_ig.core import console
from nexus_ig.instagram.login import clean_session_id, get_account_identity, save_sessionid_to_env
from nexus_ig.services.provider import InstagramProvider


def login_helper():
    load_dotenv()
    session_file = os.getenv("SESSION_FILE", "session.json")
    username_env = os.getenv("INSTAGRAM_USERNAME", "").strip()
    password_env = os.getenv("INSTAGRAM_PASSWORD", "").strip()
    sessionid_env = clean_session_id(os.getenv("SESSIONID", "").strip())

    cl = InstagramProvider()

    # 0. Check if an active session already exists in session.json
    if os.path.exists(session_file):
        console.status("SESSION", f"Checking existing session file '{session_file}'...")
        try:
            cl.load_settings(session_file)
            my_pk, my_user = get_account_identity(cl)
            if my_pk and my_pk != "bot":
                console.success(f"Active session found for @{my_user} (ID: {my_pk})!")
                choice = input("\nUse existing active session? (Y/n): ").strip().lower()
                if choice not in ("n", "no"):
                    console.success("Using existing session! You can run 'python main.py' anytime.")
                    # Ensure SESSIONID is synced to .env
                    if cl.sessionid:
                        save_sessionid_to_env(cl.sessionid)
                    return
        except Exception as exc:
            console.warning(f"Existing session invalid: {exc}")

    # 1. Try SESSIONID from .env if present
    if sessionid_env and not sessionid_env.startswith("<"):
        console.status("SESSION", "Validating SESSIONID from .env...")
        try:
            cl.login_by_sessionid(sessionid_env)
            cl.dump_settings(session_file)
            save_sessionid_to_env(sessionid_env)
            my_pk, my_user = get_account_identity(cl)
            console.success(f"Session validated & saved to {session_file} (@{my_user})")
            console.status("NEXT", "Run 'python main.py' to start the bot.")
            return
        except Exception as exc:
            console.warning(f"Session ID from .env failed: {exc}")

    # 2. Try Username & Password from .env
    if username_env and password_env and not username_env.startswith("<"):
        console.status("LOGIN", f"Attempting automatic login for @{username_env} using .env credentials...")
        try:
            cl.login(username_env, password_env)
            cl.dump_settings(session_file)
            if cl.sessionid:
                save_sessionid_to_env(cl.sessionid)
            my_pk, my_user = get_account_identity(cl)
            console.success(f"Successfully logged in as @{my_user or username_env} (ID: {my_pk})!")
            console.success(f"Session saved to {session_file} & SESSIONID updated in .env")
            console.status("NEXT", "Run 'python main.py' to start the bot.")
            return
        except Exception as exc:
            console.warning(f"Username/Password login failed: {exc}")
            console.status("FALLBACK", "Switching to interactive login...")

    # 3. Interactive prompt fallback
    console.login_screen()
    raw_input = input("\nPaste sessionid (or press Enter for Username & Password): ").strip()
    sessionid = clean_session_id(raw_input)

    if sessionid:
        try:
            console.status("SESSION", "Validating session ID...")
            cl.login_by_sessionid(sessionid)
            console.status("SESSION", "Verifying account identity...")
            my_pk, my_user = get_account_identity(cl)
            cl.dump_settings(session_file)
            save_sessionid_to_env(sessionid)
            console.success(f"Successfully authenticated as @{my_user} (ID: {my_pk})!")
            console.success(f"Session saved permanently to '{session_file}' & '.env'!")
            console.status("NEXT", "Now you can run 'python main.py' anytime without logging in again!")
            return
        except Exception as exc:
            console.error(f"Session ID login failed: {exc}")
            console.warning("Please check if you copied the sessionid value correctly.")

    # Username & Password interactive prompt
    console.section("CREDENTIAL LOGIN")
    user = input("Instagram Username: ").strip().lstrip("@")
    pwd = getpass.getpass("Instagram Password: ").strip()

    if not user or not pwd:
        console.error("Username and password cannot be empty.")
        return

    try:
        console.status("LOGIN", f"Authenticating as @{user}...")
        cl.login(user, pwd)
        my_pk, my_user = get_account_identity(cl)
        cl.dump_settings(session_file)
        if cl.sessionid:
            save_sessionid_to_env(cl.sessionid)
        console.success(f"Successfully logged in as @{my_user or user} (ID: {my_pk})!")
        console.success(f"Session saved permanently to '{session_file}' & '.env'!")
        console.status("NEXT", "Run 'python main.py' to start the bot.")
    except Exception as exc:
        console.error(f"Credential login failed: {exc}")


if __name__ == "__main__":
    login_helper()


