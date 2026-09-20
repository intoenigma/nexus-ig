import os
import tempfile
from nexus_ig.instagram.login import clean_session_id, save_sessionid_to_env


def test_clean_session_id():
    assert clean_session_id(' "12345%3Aabc" ') == "12345:abc"
    assert clean_session_id("sessionid=6789%3Axyz; path=/") == "6789:xyz"
    assert clean_session_id("'9999:test'") == "9999:test"
    assert clean_session_id("") == ""


def test_save_sessionid_to_env():
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = os.path.join(tmpdir, ".env")
        save_sessionid_to_env("12345%3Aabc", env_file)

        with open(env_file, "r", encoding="utf-8") as f:
            content = f.read()

        assert "SESSIONID=12345:abc" in content

        # Re-save to ensure update works without creating duplicate keys
        save_sessionid_to_env("67890%3Adef", env_file)
        with open(env_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        matching = [l for l in lines if l.startswith("SESSIONID=")]
        assert len(matching) == 1
        assert matching[0].strip() == "SESSIONID=67890:def"


def test_console_log_activity():
    from nexus_ig.core import console
    # Test color determination
    color1 = console.get_user_color("swami")
    color2 = console.get_user_color("karan")
    assert isinstance(color1, str) and len(color1) > 0
    assert isinstance(color2, str) and len(color2) > 0

    # Ensure log_activity executes cleanly for all action types without throwing
    console.log_activity("Anime GC", "swami", "text", "Hello there")
    console.log_activity("Anime GC", "swami", "reel", "Meme video")
    console.log_activity("Anime GC", "swami", "photo")
    console.log_activity("Anime GC", "swami", "join")
    console.log_activity("Anime GC", "swami", "command", "oli help", is_admin=True)
    console.log_activity("Anime GC", "NexusBot", "reply", "Help menu sent", is_bot=True)


