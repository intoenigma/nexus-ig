import os
import tempfile
import unittest
from nexus_ig.instagram.login import clean_session_id, save_sessionid_to_env


class TestInstagramBot(unittest.TestCase):
    def test_clean_session_id(self):
        self.assertEqual(clean_session_id(' "12345%3Aabc" '), "12345:abc")
        self.assertEqual(clean_session_id("sessionid=6789%3Axyz; path=/"), "6789:xyz")
        self.assertEqual(clean_session_id("'9999:test'"), "9999:test")
        self.assertEqual(clean_session_id(""), "")

    def test_save_sessionid_to_env(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, ".env")
            save_sessionid_to_env("12345%3Aabc", env_file)

            with open(env_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("SESSIONID=12345:abc", content)

            # Re-save to ensure update works without creating duplicate keys
            save_sessionid_to_env("67890%3Adef", env_file)
            with open(env_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            matching = [l for l in lines if l.startswith("SESSIONID=")]
            self.assertEqual(len(matching), 1)
            self.assertEqual(matching[0].strip(), "SESSIONID=67890:def")

    def test_console_log_activity(self):
        from nexus_ig.core import console
        # Test color determination
        color1 = console.get_user_color("swami")
        color2 = console.get_user_color("karan")
        self.assertTrue(isinstance(color1, str) and len(color1) > 0)
        self.assertTrue(isinstance(color2, str) and len(color2) > 0)

        # Ensure log_activity executes cleanly for all action types without throwing
        console.log_activity("Anime GC", "swami", "text", "Hello there")
        console.log_activity("Anime GC", "swami", "reel", "Meme video")
        console.log_activity("Anime GC", "swami", "photo")
        console.log_activity("Anime GC", "swami", "join")
        console.log_activity("Anime GC", "swami", "command", "oli help", is_admin=True)
        console.log_activity("Anime GC", "NexusBot", "reply", "Help menu sent", is_bot=True)

    def test_reel_reaction_selection(self):
        from nexus_ig.services.reel_reactor import get_reel_reaction_emoji, handle_reel_reaction, is_reel_message
        from unittest.mock import MagicMock

        # Love category
        love_emoji = get_reel_reaction_emoji("Check out this cute couple video #love #romance")
        self.assertIn(love_emoji, ["❤️", "🥰", "💖", "💕", "😍"])

        # Funny category
        funny_emoji = get_reel_reaction_emoji("Lmao so true 😂 #memes #funny #roast")
        self.assertIn(funny_emoji, ["😂", "🤣", "💀", "😹", "🤡"])

        # Fire category
        fire_emoji = get_reel_reaction_emoji("Sigma male entry #attitude #savage #fire")
        self.assertIn(fire_emoji, ["🔥", "⚡", "😎", "💥", "💣"])

        # Sad category
        sad_emoji = get_reel_reaction_emoji("Heartbroken alone in the rain #sad #broken #cry")
        self.assertIn(sad_emoji, ["🥺", "💔", "😢", "🥀", "😭"])

        # Anime category
        anime_emoji = get_reel_reaction_emoji("Gojo domain expansion #anime #jujutsukaisen")
        self.assertIn(anime_emoji, ["✨", "⚡", "🌸", "⚔️", "🎌"])

        # Tech coding category
        coding_emoji = get_reel_reaction_emoji("Debugging python bug in vscode #developer #coding")
        self.assertIn(coding_emoji, ["💻", "👨‍💻", "⚙️", "🚀", "🤖"])

        # Sports category
        sports_emoji = get_reel_reaction_emoji("Virat Kohli masterclass batting #cricket #ipl")
        self.assertIn(sports_emoji, ["🏏", "⚽", "🏆", "🥇", "🔥"])

        # Fallback for unclassified reel (guaranteed reaction)
        default_emoji = get_reel_reaction_emoji("")
        self.assertTrue(isinstance(default_emoji, str) and len(default_emoji) > 0)

        # Test is_reel_message with xma_clip, media_share, generic_xma
        m_xma = MagicMock()
        m_xma.item_type = "xma_clip"
        self.assertTrue(is_reel_message(m_xma))

        m_share = MagicMock()
        m_share.item_type = "media_share"
        self.assertTrue(is_reel_message(m_share))

        m_link = MagicMock()
        m_link.item_type = "text"
        m_link.text = "Check this out https://www.instagram.com/reel/Dao9M0Ss9zh/"
        self.assertTrue(is_reel_message(m_link))

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
        self.assertIn(res, ["❤️", "🥰", "💖", "💕", "😍"])
        mock_cl.direct_send_reaction.assert_called_once()

    def test_group_activity_storage(self):
        from nexus_ig.core.storage import Storage
        with tempfile.TemporaryDirectory() as tmpdir:
            db_file = os.path.join(tmpdir, "test_nexus.db")
            storage = Storage(db_file)

            # 1. Log group activity with reply_to context
            row_id = storage.log_group_activity(
                thread_id="1545935720262832",
                group_title="MortalS",
                user_id="1001",
                username="alex",
                action_type="text",
                content="Hello everyone!",
                reply_to_msg_id="msg_000",
                reply_to_user_id="1000",
                reply_to_username="bot",
                reply_to_text="Welcome guys!",
                message_id="msg_001",
            )
            self.assertGreater(row_id, 0)

            # 2. Update reaction
            storage.update_activity_reactions("msg_001", '[{"username":"dev","emoji":"🔥"}]')

            # 3. Retrieve recent activity
            acts = storage.get_recent_group_activity("1545935720262832", limit=5)
            self.assertEqual(len(acts), 1)
            self.assertEqual(acts[0]["username"], "alex")
            self.assertEqual(acts[0]["reply_to_username"], "bot")
            self.assertEqual(acts[0]["reactions_json"], '[{"username":"dev","emoji":"🔥"}]')

            # 4. User activity query
            user_acts = storage.get_user_activity("1545935720262832", "1001")
            self.assertEqual(len(user_acts), 1)
            self.assertEqual(user_acts[0]["content"], "Hello everyone!")

            storage.close()


if __name__ == "__main__":
    unittest.main()




