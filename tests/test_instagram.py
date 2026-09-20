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


def test_reel_reaction_selection():
    from nexus_ig.services.reel_reactor import get_reel_reaction_emoji, handle_reel_reaction, is_reel_message
    from unittest.mock import MagicMock

    # Love category
    love_emoji = get_reel_reaction_emoji("Check out this cute couple video #love #romance")
    assert love_emoji in ["❤️", "🥰", "💖", "💕", "😍"]

    # Funny category
    funny_emoji = get_reel_reaction_emoji("Lmao so true 😂 #memes #funny #roast")
    assert funny_emoji in ["😂", "🤣", "💀", "😹", "🤡"]

    # Fire category
    fire_emoji = get_reel_reaction_emoji("Sigma male entry #attitude #savage #fire")
    assert fire_emoji in ["🔥", "⚡", "😎", "💥", "💣"]

    # Sad category
    sad_emoji = get_reel_reaction_emoji("Heartbroken alone in the rain #sad #broken #cry")
    assert sad_emoji in ["🥺", "💔", "😢", "🥀", "😭"]

    # Anime category
    anime_emoji = get_reel_reaction_emoji("Gojo domain expansion #anime #jujutsukaisen")
    assert anime_emoji in ["✨", "⚡", "🌸", "⚔️", "🎌"]

    # Tech coding category
    coding_emoji = get_reel_reaction_emoji("Debugging python bug in vscode #developer #coding")
    assert coding_emoji in ["💻", "👨‍💻", "⚙️", "🚀", "🤖"]

    # Sports category
    sports_emoji = get_reel_reaction_emoji("Virat Kohli masterclass batting #cricket #ipl")
    assert sports_emoji in ["🏏", "⚽", "🏆", "🥇", "🔥"]

    # Fallback for unclassified reel (guaranteed reaction)
    default_emoji = get_reel_reaction_emoji("")
    assert isinstance(default_emoji, str) and len(default_emoji) > 0

    # Test is_reel_message with xma_clip, media_share, generic_xma
    m_xma = MagicMock()
    m_xma.item_type = "xma_clip"
    assert is_reel_message(m_xma) is True

    m_share = MagicMock()
    m_share.item_type = "media_share"
    assert is_reel_message(m_share) is True

    m_link = MagicMock()
    m_link.item_type = "text"
    m_link.text = "Check this out https://www.instagram.com/reel/Dao9M0Ss9zh/"
    assert is_reel_message(m_link) is True

    # Test handle_reel_reaction with mock client
    mock_cl = MagicMock()
    mock_cl.direct_send_reaction.return_value = True
    mock_msg = MagicMock()
    mock_msg.id = "msg_123"
    mock_msg.text = "#love cute moments"
    mock_msg.reel_share = None
    mock_msg.clip = None
    mock_msg.media_share = None
    mock_msg.xma_share = None
    mock_msg.raw_xma = None
    mock_msg.link = None
    mock_msg.thread_id = None
    mock_msg.client_context = None
    mock_msg.item_type = "clip"

    res = handle_reel_reaction(mock_cl, "thread_999", mock_msg)
    assert res in ["❤️", "🥰", "💖", "💕", "😍"]
    mock_cl.direct_send_reaction.assert_called_once()



