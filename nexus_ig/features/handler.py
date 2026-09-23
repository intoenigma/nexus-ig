"""Central Command Handler coordinating feature modules and bot actions."""
import random
from typing import Optional

from ..app import console
from .admin.commands import format_status_report, format_gc_info
from .fun.commands import (
    get_advice_card,
    get_joke_card,
    get_fact_card,
    get_bored_card,
    get_yesno_card,
    get_recipe_card,
)
from .games.commands import TruthAndDareGame
from .moderation import ModerationEngine
from .chatbot.chatbot import StrictNLPBot, ChatMessage
from ..instagram.users import fetch_user_profile, find_sender_name, extract_usernames, resolve_user_ids
from ..utils.formatting import format_profile_card


class CommandHandler:
    """Master Command Handler for Nexus IG Bot."""

    def __init__(self, cl, storage, config, my_pk: str):
        self.cl = cl
        self.storage = storage
        self.config = config
        self.my_pk = str(my_pk)
        self.moderation = ModerationEngine(storage, config)
        self.chatbot = StrictNLPBot(storage)
        self.td_game = TruthAndDareGame()

    def is_admin(self, thread, user_id: str) -> bool:
        """Check if user_id is an admin or group admin."""
        uid = str(user_id)
        if uid == self.my_pk:
            return True
        if self.config.owner_username:
            owner_clean = self.config.owner_username.strip().lstrip("@").lower()
            sender_name = find_sender_name(thread, user_id).lower()
            if sender_name == owner_clean:
                return True
        sender_name = find_sender_name(thread, user_id).lower()
        if sender_name in {u.lower() for u in self.config.admin_usernames}:
            return True
        for admin_id in getattr(thread, "admin_user_ids", []):
            if str(admin_id) == uid:
                return True
        return False

    def handle(self, thread, last_msg) -> bool:
        """Process incoming thread message."""
        if not last_msg or not getattr(last_msg, "id", None):
            return False

        msg_id = str(last_msg.id)
        thread_id = str(thread.pk)
        user_id = str(last_msg.user_id)
        sender_name = find_sender_name(thread, user_id)
        text = (getattr(last_msg, "text", "") or "").strip()

        # Prevent duplicate handling
        if self.storage.has_replied(msg_id):
            return False

        is_bot = (user_id == self.my_pk)
        is_admin_user = self.is_admin(thread, user_id)

        # 1. Moderation Inspection
        if not is_bot:
            mod_result = self.moderation.inspect(thread_id, user_id, text, is_admin=is_admin_user)
            if mod_result and mod_result.blocked:
                self.storage.mark_replied(msg_id)
                console.warning(f"Moderation trigger: {mod_result.reason} by @{sender_name}")
                if mod_result.admin_alert:
                    self._send_reply(thread_id, f"⚠️ @{sender_name} {mod_result.reason}")
                return True

        # Ignore bot's own messages
        if is_bot:
            return False

        # 2. Check Maintenance Mode
        text_lower = text.lower()
        prefix = self.config.command_prefix.lower()

        is_addressed = (
            text_lower.startswith(prefix)
            or text_lower.startswith("!")
            or text_lower.startswith("/")
            or "nexus" in text_lower
            or "oli" in text_lower
        )

        if getattr(self.config, "maintenance_mode", False):
            if is_addressed:
                self.storage.mark_replied(msg_id)
                reply = getattr(self.config, "maintenance_reply", "bot band hai kal aana")
                self._send_reply(thread_id, f"🤖 {reply}")
                return True
            return False

        if not is_addressed and not text:
            return False

        # Extract clean command payload
        tail = text
        if text_lower.startswith(prefix):
            tail = text[len(prefix):].strip()
        elif text_lower.startswith("!") or text_lower.startswith("/"):
            tail = text[1:].strip()
        elif text_lower.startswith("oli"):
            tail = text[3:].strip()
        elif text_lower.startswith("nexus"):
            tail = text[5:].strip()

        tail_lower = tail.lower()

        # 3. Command Dispatching
        if tail_lower in ("help", "commands"):
            self.storage.mark_replied(msg_id)
            self._send_reply(thread_id, self._get_help_card())
            return True

        if tail_lower in ("status", "botstatus"):
            self.storage.mark_replied(msg_id)
            report = format_status_report(self.config, self.cl.username if self.cl else "NexusBot", self.my_pk)
            self._send_reply(thread_id, report)
            return True

        if tail_lower in ("gc info", "gcinfo"):
            self.storage.mark_replied(msg_id)
            info = format_gc_info(thread)
            self._send_reply(thread_id, info)
            return True

        # User Profile Lookup (know @user)
        if tail_lower.startswith("know") or tail_lower.startswith("profile"):
            self.storage.mark_replied(msg_id)
            target_username = tail.split()[-1] if len(tail.split()) > 1 else sender_name
            prof_data = fetch_user_profile(target_username, cl=self.cl, thread=thread)
            if prof_data:
                pic_url = prof_data.get("profile_pic_url")
                card = format_profile_card(prof_data)
                if pic_url and prof_data.get("photo_path"):
                    try:
                        self.cl.send_photo(thread_id, prof_data["photo_path"])
                    except Exception:
                        pass
                self._send_reply(thread_id, card)
            else:
                self._send_reply(thread_id, f"❌ User details @{target_username} load nahi ho sake.")
            return True

        # Fun Cards
        if tail_lower == "advice":
            self.storage.mark_replied(msg_id)
            self._send_reply(thread_id, get_advice_card())
            return True

        if tail_lower == "joke":
            self.storage.mark_replied(msg_id)
            self._send_reply(thread_id, get_joke_card())
            return True

        if tail_lower == "fact":
            self.storage.mark_replied(msg_id)
            self._send_reply(thread_id, get_fact_card())
            return True

        if tail_lower == "bored":
            self.storage.mark_replied(msg_id)
            self._send_reply(thread_id, get_bored_card())
            return True

        if tail_lower in ("oracle", "yesno"):
            self.storage.mark_replied(msg_id)
            self._send_reply(thread_id, get_yesno_card())
            return True

        if tail_lower == "recipe":
            self.storage.mark_replied(msg_id)
            self._send_reply(thread_id, get_recipe_card())
            return True

        # Games: Truth & Dare
        if tail_lower.startswith("tdgame"):
            self.storage.mark_replied(msg_id)
            players = extract_usernames(tail[6:])
            res = self.td_game.create_lobby(thread_id, players, sender_name)
            self._send_reply(thread_id, res)
            return True

        if tail_lower in ("tdstart", "spin", "tdnext"):
            self.storage.mark_replied(msg_id)
            res = self.td_game.start_round(thread_id)
            self._send_reply(thread_id, res)
            return True

        if tail_lower in ("truth", "dare", "t", "d"):
            td_res = self.td_game.handle_choice(thread_id, tail_lower, sender_name)
            if td_res:
                self.storage.mark_replied(msg_id)
                self._send_reply(thread_id, td_res)
                return True

        if tail_lower == "tdstop":
            self.storage.mark_replied(msg_id)
            res = self.td_game.stop_game(thread_id)
            self._send_reply(thread_id, res)
            return True

        # Dice & Flip & 8ball
        if tail_lower == "dice":
            self.storage.mark_replied(msg_id)
            val = random.randint(1, 6)
            self._send_reply(thread_id, f"🎲 You rolled a {val}!")
            return True

        if tail_lower == "flip":
            self.storage.mark_replied(msg_id)
            res = random.choice(["HEADS 🪙", "TAILS 🪙"])
            self._send_reply(thread_id, f"🪙 Coin flip result: {res}")
            return True

        # 4. Fallback Chatbot Processing
        chat_msg = ChatMessage(
            text=text,
            message_id=msg_id,
            thread_id=thread_id,
            user_id=user_id,
            user_name=sender_name,
            is_bot_mentioned=is_addressed,
        )
        bot_resp = self.chatbot.process_message(chat_msg)
        if bot_resp and bot_resp.should_reply and bot_resp.reply_text:
            self.storage.mark_replied(msg_id)
            self._send_reply(thread_id, bot_resp.reply_text)
            return True

        return False

    def _send_reply(self, thread_id: str, text: str):
        """Helper to send text reply via instagrapi client."""
        try:
            if self.cl:
                self.cl.send_message(thread_id, text)
                console.success(f"Sent reply to thread {thread_id}")
        except Exception as exc:
            console.error(f"Failed to send message: {exc}")

    def _get_help_card(self) -> str:
        prefix = self.config.command_prefix
        return (
            "🤖 NEXUS IG BOT COMMANDS 🤖\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ {prefix} status - Check bot operational status\n"
            f"ℹ️ {prefix} gc info - Display group metadata\n"
            f"🔎 {prefix} know @user - Fetch public profile card\n"
            "\n"
            "🎉 FUN COMMANDS:\n"
            f"💡 {prefix} advice | 😂 {prefix} joke\n"
            f"📌 {prefix} fact | 🎉 {prefix} bored\n"
            f"🔮 {prefix} oracle | 🍲 {prefix} recipe\n"
            "\n"
            "🎯 GAMES:\n"
            f"🍾 {prefix} tdgame @p1 @p2 - Start Truth & Dare lobby\n"
            f"🎲 {prefix} dice | 🪙 {prefix} flip"
        )
