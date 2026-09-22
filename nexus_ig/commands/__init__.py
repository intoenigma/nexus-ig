from ..instagram.users import fetch_user_profile_instaloader
from .help import generate_help_text
from .utility import handle_greeting, handle_ping, handle_rules
from .fun import get_advice_card, get_joke_card, get_fact_card, get_bored_card, get_yesno_card, get_recipe_card
from .economy import SHOP_CATALOG, get_shop_menu
from .admin import format_status_report, format_gc_info
from .moderation import format_lurkers_report
from .games import TruthAndDareGame, get_truth_question, get_dare_task
from ..utils.permissions import is_admin, is_owner
from pathlib import Path
import os
import random
import re
import time

import requests

from ..core import console
from ..instagram.users import clean_username, extract_usernames, find_sender_name, resolve_user_ids
from ..instagram.groups import is_group_thread
from ..services.moderation import ModerationEngine
from ..services.chatbot import StrictNLPBot, ChatMessage
from ..instagram.media import prepare_dm_image


class CommandHandler:
    def __init__(self, cl, storage, config, my_pk):
        self.cl = cl
        self.storage = storage
        self.config = config
        self.my_pk = str(my_pk)
        self.start_time = int(time.time())
        self.td_game = TruthAndDareGame()
        self.moderation = ModerationEngine(config, storage)
        self.chatbot = StrictNLPBot(storage=storage)

    def send_and_mark(self, thread_id, text, message_id):
        bot_msg_id = None
        try:
            sent = self.cl.direct_send(text, thread_ids=[thread_id])
            if sent:
                msg_obj = sent[0] if isinstance(sent, list) and sent else sent
                bot_msg_id = str(getattr(msg_obj, "id", None) or getattr(msg_obj, "item_id", None) or getattr(msg_obj, "pk", None) or "")
            self.storage.mark_replied(message_id, thread_id)
            grp_title = self.storage.get_group_title(thread_id)
            preview = text.strip().split("\n")[0][:60]
            console.log_activity(grp_title, "NexusBot", "reply", preview, is_bot=True)

            # Log bot reply into group_activity table with reference to original message
            orig_msg = self.storage.get_message(message_id) if message_id else None
            reply_to_uid = orig_msg.get("user_id") if orig_msg else None
            reply_to_uname = orig_msg.get("username") if orig_msg else None
            reply_to_text = orig_msg.get("text") if orig_msg else None

            self.storage.log_group_activity(
                thread_id=thread_id,
                group_title=grp_title,
                user_id=self.my_pk,
                username=getattr(self.cl, "username", None) or "NexusBot",
                action_type="bot_reply",
                content=text,
                reply_to_msg_id=message_id,
                reply_to_user_id=reply_to_uid,
                reply_to_username=reply_to_uname,
                reply_to_text=reply_to_text,
                message_id=bot_msg_id,
            )
        except Exception as exc:
            self.storage.mark_replied(message_id, thread_id)
            console.warning(f"Direct send error: {exc}")
        if self.config.reply_delay_seconds > 0:
            time.sleep(self.config.reply_delay_seconds)

    def is_admin(self, thread, user_id):
        user_id = str(user_id)
        sender = clean_username(find_sender_name(thread, user_id))
        if user_id == self.my_pk:
            return True
        if user_id in self.config.admin_user_ids or sender in self.config.admin_usernames:
            return True
        return False

    def help_text(self):
        return generate_help_text(getattr(self.config, 'command_prefix', 'oli'))

    def control_help(self):
        prefix = self.config.command_prefix
        return (
            "Control Commands\n"
            f"{prefix} welcome set <message> - Set group welcome\n"
            f"{prefix} welcome on/off - Enable or disable welcome\n"
            f"{prefix} rules - Send rules\n"
            f"{prefix} faq set <keyword> | <reply> - Add keyword auto-reply\n"
            f"{prefix} birthday set @user MM-DD | message - Save birthday\n"
            f"{prefix} event add <minutes> | <title> | <message> - Schedule event\n"
            f"{prefix} inactive - List inactive members\n"
            f"{prefix} report - Group activity report\n"
            f"{prefix} status - Show bot status\n"
            f"{prefix} gc list/info/create/add/title - Group controls"
        )


    def check_moderation(self, thread, last_msg, sender_name: str) -> bool:
        if not last_msg or last_msg.item_type != "text" or str(last_msg.user_id) == self.my_pk:
            return False

        # Admins bypass moderation
        if self.is_admin(thread, last_msg.user_id):
            return False

        msg_text = last_msg.text.strip()
        result = self.moderation.check_message(msg_text, last_msg.user_id, is_admin=False)

        if result["blocked"]:
            bad_word = result.get("word") or "forbidden content"
            new_warn_count = self.storage.add_warning(thread.pk, last_msg.user_id, sender_name, f"Used forbidden word: {bad_word}")
            grp_title = thread.thread_title or self.storage.get_group_title(thread.pk)
            console.log_activity(grp_title, sender_name, "warn", f"Detected forbidden word: '{bad_word}' ({new_warn_count}/3)")
            
            warn_msg = (
                "⚠️ FORBIDDEN WORD DETECTED! ⚠️\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 User: @{sender_name}\n"
                f"🚫 Detected word: '{bad_word}'\n"
                f"⚠️ Warning Count: {new_warn_count}/3\n\n"
                "Please follow group decorum!"
            )
            self.send_and_mark(thread.pk, warn_msg, last_msg.id)
            
            # Try to delete/unsend the flagged message
            try:
                self.cl.direct_media_share(thread.pk, last_msg.id)
            except Exception:
                pass
            return True

        return False

    def handle(self, thread, last_msg):
        if not last_msg:
            return False
        if self.storage.has_replied(last_msg.id) or str(last_msg.user_id) == self.my_pk:
            return False

        sender_name = find_sender_name(thread, last_msg.user_id)

        # 🛡️ Strict Moderation & Bad Word Check
        if self.check_moderation(thread, last_msg, sender_name):
            return True

        # 🌟 Award XP for every non-bot message
        if str(last_msg.user_id) != self.my_pk:
            self.process_xp_gain(thread, last_msg, sender_name)

        if last_msg.item_type != "text":
            return False

        msg_text = last_msg.text.strip()
        lower_text = msg_text.lower()
        prefix = self.config.command_prefix.lower()

        # Check if 'nexus', 'oli', 'chotu', or command prefix is mentioned anywhere in the message
        name_patterns = [r"\b" + re.escape(prefix) + r"\b", r"\bnexus\b", r"\bchotu\b", r"\boli\b"]
        is_name_mentioned = any(re.search(pat, lower_text) for pat in name_patterns)

        # Determine if message is a command via prefix, slash '/', or name mention anywhere
        is_command = False
        raw_tail = ""

        if lower_text.startswith(prefix):
            is_command = True
            raw_tail = msg_text[len(self.config.command_prefix):].strip()
        elif lower_text.startswith("/"):
            is_command = True
            raw_tail = msg_text[1:].strip()
        elif is_name_mentioned:
            is_command = True
            raw_tail = msg_text.strip()



        if not is_command:
            auto_reply = self.storage.keyword_reply(thread.pk, msg_text)
            if auto_reply:
                self.send_and_mark(thread.pk, auto_reply["reply"], last_msg.id)
                return True
            return False

        # Mark message as replied IMMEDIATELY to prevent double execution / loops
        self.storage.mark_replied(last_msg.id, thread.pk)

        # 🚧 Maintenance / Offline Mode Guard (.env MAINTENANCE_MODE=true)
        if getattr(self.config, "maintenance_mode", False):
            self.send_and_mark(thread.pk, getattr(self.config, "maintenance_message", "Bot band hai, kal aana! 😴"), last_msg.id)
            return True

        # Ignore old history command messages (older than 5 minutes)
        raw_ts = getattr(last_msg, "timestamp", 0)
        msg_time = 0
        if hasattr(raw_ts, "timestamp"):
            msg_time = int(raw_ts.timestamp())
        elif isinstance(raw_ts, (int, float)):
            val = int(raw_ts)
            msg_time = val // 1_000_000 if val > 2_000_000_000 else (val // 1000 if val > 2_000_000 else val)
        elif isinstance(raw_ts, str) and raw_ts.isdigit():
            val = int(raw_ts)
            msg_time = val // 1_000_000 if val > 2_000_000_000 else (val // 1000 if val > 2_000_000 else val)

        if msg_time > 0 and (int(time.time()) - msg_time) > 300:
            return False

        clean_tail = raw_tail.lower()
        grp_title = thread.thread_title or self.storage.get_group_title(thread.pk)
        console.log_activity(grp_title, sender_name, "command", raw_tail or 'ping', is_admin=self.is_admin(thread, last_msg.user_id))

        # Truth & Dare Game Commands
        if clean_tail.startswith("tdgame") or clean_tail.startswith("tdgame "):
            usernames = extract_usernames(raw_tail.replace("tdgame", "").strip())
            msg = self.td_game.create_lobby(thread.pk, usernames, sender_name)
            self.send_and_mark(thread.pk, msg, last_msg.id)
            return True

        if clean_tail in ("tdstart", "tdnext"):
            msg = self.td_game.start_round(thread.pk)
            self.send_and_mark(thread.pk, msg, last_msg.id)
            return True

        if clean_tail in ("truth", "t", "dare", "d") or lower_text in ("truth", "t", "dare", "d"):
            card = self.td_game.handle_choice(thread.pk, clean_tail if clean_tail in ("truth", "t", "dare", "d") else lower_text, sender_name)
            if card:
                self.send_and_mark(thread.pk, card, last_msg.id)
                return True

        if clean_tail in ("tdstop", "tdend"):
            msg = self.td_game.stop_game(thread.pk)
            self.send_and_mark(thread.pk, msg, last_msg.id)
            return True

        # Group jaago / oli jaago command
        if clean_tail in ("jaago", "group jaago", "group jago") or lower_text in ("group jaago", "group jago"):
            active_users = self.storage.get_active_members_7days(thread.pk)
            if not active_users and hasattr(thread, "users"):
                active_users = [{"username": u.username, "user_id": str(u.pk)} for u in thread.users if getattr(u, "username", "")]

            if not active_users:
                self.send_and_mark(thread.pk, "⏰ GROUP JAAGO! ⏰\nNo active members found to tag!", last_msg.id)
                return True

            mentions = " ".join([f"@{u['username']}" for u in active_users[:30] if u.get("username")])
            msg = (
                "⏰ GROUP JAAGO! ⏰\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"🔔 Calling active members:\n{mentions}\n\n"
                "Group active ho gaya hai! Sab aao aur chat karo! ⚡"
            )
            self.send_and_mark(thread.pk, msg, last_msg.id)
            return True

        # Group Activity Log Command
        if clean_tail in ("activity", "log", "logs", "activitylog"):
            recent_acts = self.storage.get_recent_group_activity(thread.pk, limit=10)
            if not recent_acts:
                self.send_and_mark(thread.pk, "📋 No activity logged yet in database.", last_msg.id)
                return True

            lines = ["📋 RECENT GROUP ACTIVITY LOG 📋", "━━━━━━━━━━━━━━━━━━━━"]
            for a in recent_acts:
                u_name = f"@{a['username']}" if a.get('username') else "User"
                act = a.get('action_type', 'action')
                cnt = a.get('content') or ''
                reply_txt = f" ↩️ (reply to @{a['reply_to_username']})" if a.get('reply_to_username') else ""
                bot_rx = f" [Reacted {a['bot_reaction']}]" if a.get('bot_reaction') else ""

                snippet = (cnt[:35] + "...") if len(cnt) > 35 else cnt
                lines.append(f"• {u_name} [{act}]: {snippet}{reply_txt}{bot_rx}")

            lines.append("━━━━━━━━━━━━━━━━━━━━")
            lines.append("💾 All activities stored in SQLite `group_activity` table!")
            self.send_and_mark(thread.pk, "\n".join(lines), last_msg.id)
            return True

        # oli know @user command
        if clean_tail.startswith("know"):
            target = raw_tail.replace("know", "").strip().lstrip("@")
            if not target:
                target = sender_name
            profile = fetch_user_profile_instaloader(target)
            if profile:
                self.storage.save_user_profile_details(
                    thread.pk, profile["user_id"], profile["username"], profile["full_name"],
                    profile["bio"], profile["followers_count"], profile["following_count"],
                    profile["posts_count"], profile["is_private"], profile["is_verified"]
                )
                card = (
                    "🔍 INSTAGRAM PROFILE DETAILS 🔍\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 Name: {profile['full_name']} (@{profile['username']})\n"
                    f"🆔 User ID: {profile['user_id']}\n"
                    f"📝 Bio: {profile['bio']}\n"
                    f"👥 Followers: {profile['followers_count']:,} | Following: {profile['following_count']:,}\n"
                    f"📸 Posts: {profile['posts_count']:,}\n"
                    f"🔒 Private: {'Yes' if profile['is_private'] else 'No'} | ✅ Verified: {'Yes' if profile['is_verified'] else 'No'}\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "💾 Profile details saved to database!"
                )
            else:
                card = f"❌ @{target} ki public profile details fetch nahi ho payi!"
            self.send_and_mark(thread.pk, card, last_msg.id)
            return True

        # Reaction command (Random emoji if none specified)
        if clean_tail.startswith("react"):
            raw_emoji = raw_tail.replace("react", "").strip()
            if not raw_emoji:
                random_emojis = ["❤️", "😂", "🔥", "👍", "😍", "✨", "💯", "🎉", "⚡", "🙌", "💀", "😎", "🤣", "👏", "🥳", "💥", "👑", "🚀", "🎯"]
                emoji = random.choice(random_emojis)
            else:
                emoji = raw_emoji

            target_msg_id = last_msg.id
            if hasattr(last_msg, "replied_to_message") and last_msg.replied_to_message:
                target_msg_id = getattr(last_msg.replied_to_message, "id", last_msg.id)

            try:
                self.cl.direct_send_reaction(thread.pk, target_msg_id, emoji)
            except Exception as exc:
                console.warning(f"Reaction failed: {exc}")
            return True

        # Warning & Moderation Admin commands
        if clean_tail.startswith("warn ") or clean_tail.startswith("warnings ") or clean_tail.startswith("warnadd ") or clean_tail.startswith("warnremove ") or clean_tail == "warnlist":
            if not self.is_admin(thread, last_msg.user_id):
                self.send_and_mark(thread.pk, "❌ Control access denied.", last_msg.id)
                return True

            if clean_tail.startswith("warnadd "):
                word = raw_tail[8:].strip()
                if word:
                    self.storage.add_forbidden_word(word)
                    self.send_and_mark(thread.pk, f"✅ Forbidden word '{word}' added to moderation list!", last_msg.id)
                return True

            if clean_tail.startswith("warnremove "):
                word = raw_tail[11:].strip()
                if word:
                    self.storage.remove_forbidden_word(word)
                    self.send_and_mark(thread.pk, f"✅ Forbidden word '{word}' removed from moderation list!", last_msg.id)
                return True

            if clean_tail == "warnlist":
                words = self.storage.get_forbidden_words()
                text = ", ".join(words) if words else "None"
                self.send_and_mark(thread.pk, f"🛑 FORBIDDEN MODERATION WORDS 🛑\n━━━━━━━━━━━━━━━━━━━━\n{text}", last_msg.id)
                return True

            if clean_tail.startswith("warn "):
                parts = raw_tail[5:].strip().split(maxsplit=1)
                target_user = parts[0].lstrip("@") if parts else ""
                reason = parts[1] if len(parts) > 1 else "Violation of group rules"
                new_count = self.storage.add_warning(thread.pk, target_user, target_user, reason)
                msg = f"⚠️ WARNING ISSUED! @{target_user}\nReason: {reason}\nTotal Warnings: {new_count}/3"
                if new_count >= 3:
                    msg += "\n🚨 3 WARNINGS REACHED! Admin intervention required!"
                self.send_and_mark(thread.pk, msg, last_msg.id)
                return True

            if clean_tail.startswith("warnings "):
                target_user = raw_tail[9:].strip().lstrip("@")
                info = self.storage.get_warnings(thread.pk, target_user)
                msg = f"📋 WARNINGS STATUS | @{target_user}\nTotal Warnings: {info['warn_count']}\nLast Reason: {info['last_reason']}"
                self.send_and_mark(thread.pk, msg, last_msg.id)
                return True

        if clean_tail == "":
            self.send_and_mark(thread.pk, f"Hello @{sender_name}! Send '{self.config.command_prefix} help' for all commands menu.", last_msg.id)
            return True



        if clean_tail in ("help", "menu", "commands"):
            self.send_and_mark(thread.pk, self.help_text(), last_msg.id)
            return True

        if clean_tail in ("daily", "claim"):
            self.handle_daily(thread, last_msg, sender_name)
            return True

        if clean_tail in ("balance", "profile", "wallet", "rank", "level"):
            self.handle_balance_or_rank(thread, last_msg, sender_name)
            return True

        if clean_tail == "shop":
            self.handle_shop(thread, last_msg)
            return True

        if clean_tail.startswith("buy"):
            self.handle_buy(thread, last_msg, raw_tail, sender_name)
            return True

        if clean_tail.startswith("gift"):
            self.handle_gift(thread, last_msg, raw_tail, sender_name)
            return True

        if clean_tail in ("top", "leaderboard"):
            self.handle_leaderboard(thread, last_msg)
            return True

        if clean_tail in ("ghosts", "ghost", "ghots", "ghot", "lurkers", "lurker", "seeners", "silent"):
            self.handle_lurkers(thread, last_msg)
            return True

        if clean_tail in ("advice", "advise"):
            return self.handle_advice(thread, last_msg)

        if clean_tail in ("joke", "jokes"):
            return self.handle_joke_api(thread, last_msg)

        if clean_tail in ("recipe", "meal", "food"):
            return self.handle_recipe(thread, last_msg)

        if clean_tail in ("bored", "activity"):
            return self.handle_bored(thread, last_msg)

        if clean_tail.startswith("yesno") or clean_tail.startswith("decide") or clean_tail.startswith("decision"):
            return self.handle_yesno(thread, last_msg, raw_tail)

        if clean_tail in ("fact", "facts"):
            return self.handle_fact(thread, last_msg)

        replied_text = None
        if hasattr(last_msg, "replied_to_message") and last_msg.replied_to_message:
            replied_text = getattr(last_msg.replied_to_message, "text", None)

        # 🤖 AI & NLP ChatBot Commands (13 NLP Libraries)
        if clean_tail.startswith(("chat ", "ai ", "ask ", "nlp ", "/chat ", "/ai ", "/ask ", "chat", "ai", "ask")):
            query = raw_tail
            for p in ["chat ", "ai ", "ask ", "nlp ", "/chat ", "/ai ", "/ask "]:
                if query.lower().startswith(p):
                    query = query[len(p):].strip()
            msg = ChatMessage(
                user_id=str(last_msg.user_id),
                user_name=sender_name,
                text=query or "hello",
                is_bot_mentioned=is_name_mentioned,
                replied_to_text=replied_text,
            )
            response = self.chatbot.process_message(msg)
            self.send_and_mark(thread.pk, response.reply_text, last_msg.id)
            return True

        if clean_tail.startswith(("feed ", "scrape ", "graph", "kb ")):
            msg = ChatMessage(
                user_id=str(last_msg.user_id),
                user_name=sender_name,
                text=raw_tail,
                is_bot_mentioned=is_name_mentioned,
                replied_to_text=replied_text,
            )
            response = self.chatbot.process_message(msg)
            self.send_and_mark(thread.pk, response.reply_text, last_msg.id)
            return True

        # Fallback: Process unknown command through 13-library NLP ChatBot engine
        msg = ChatMessage(
            user_id=str(last_msg.user_id),
            user_name=sender_name,
            text=raw_tail or msg_text,
            is_bot_mentioned=is_name_mentioned,
            replied_to_text=replied_text,
        )
        response = self.chatbot.process_message(msg)
        self.send_and_mark(thread.pk, response.reply_text, last_msg.id)
        return True

    def send_joke(self, thread, last_msg, sender_name):
        try:
            response = requests.get("https://v2.jokeapi.dev/joke/Any?safe-mode", timeout=5)
            response.raise_for_status()
            joke_data = response.json()
            if joke_data["type"] == "single":
                joke_text = f"Here is a joke for @{sender_name}:\n\n{joke_data['joke']}"
            else:
                joke_text = f"Here is a joke for @{sender_name}:\n\n{joke_data['setup']}\n...\n{joke_data['delivery']}"
        except Exception as exc:
            console.error(f"Joke API failed: {exc}")
            joke_text = "Error fetching joke right now."
        self.send_and_mark(thread.pk, joke_text, last_msg.id)

    def handle_admin(self, thread, last_msg, tail, lower_tail):
        if lower_tail == "controls":
            self.send_and_mark(thread.pk, self.control_help(), last_msg.id)
            return
        if lower_tail == "status":
            group = self.storage.get_group(thread.pk)
            welcome = "on" if not group or group["welcome_enabled"] else "off"
            self.send_and_mark(
                thread.pk,
                f"Bot status\nThread: {thread.pk}\nWelcome: {welcome}\nDatabase: active",
                last_msg.id,
            )
            return
        if lower_tail == "rules":
            self.send_and_mark(thread.pk, "Group rules\n" + self.config.rules_message, last_msg.id)
            return
        if lower_tail.startswith("welcome"):
            self.handle_welcome(thread, last_msg, tail, lower_tail)
            return
        if lower_tail.startswith("gc "):
            self.handle_group_command(thread, last_msg, tail, lower_tail)
            return
        self.handle_automation_command(thread, last_msg, tail, lower_tail)


    def handle_automation_command(self, thread, last_msg, tail, lower_tail):
        if lower_tail.startswith("faq set "):
            payload = tail[len("faq set ") :].strip()
            keyword, sep, reply = payload.partition("|")
            if not sep or not keyword.strip() or not reply.strip():
                self.send_and_mark(thread.pk, f"Usage: {self.config.command_prefix} faq set <keyword> | <reply>", last_msg.id)
                return
            self.storage.set_keyword_reply(thread.pk, keyword.strip(), reply.strip())
            self.send_and_mark(thread.pk, f"FAQ saved for: {keyword.strip()}", last_msg.id)
            return
        if lower_tail.startswith("faq remove "):
            keyword = tail[len("faq remove ") :].strip()
            self.storage.delete_keyword_reply(thread.pk, keyword)
            self.send_and_mark(thread.pk, f"FAQ removed for: {keyword}", last_msg.id)
            return
        if lower_tail.startswith("birthday set "):
            payload = tail[len("birthday set ") :].strip()
            left, _, message = payload.partition("|")
            parts = left.split()
            if len(parts) < 2 or "-" not in parts[1]:
                self.send_and_mark(thread.pk, f"Usage: {self.config.command_prefix} birthday set @user MM-DD | message", last_msg.id)
                return
            month, day = [int(item) for item in parts[1].split("-", 1)]
            self.storage.set_birthday(thread.pk, parts[0], month, day, message.strip() or None)
            self.send_and_mark(thread.pk, f"Birthday saved for {parts[0]}.", last_msg.id)
            return
        if lower_tail.startswith("event add "):
            payload = tail[len("event add ") :].strip()
            minutes, sep1, rest = payload.partition("|")
            title, sep2, message = rest.partition("|")
            if not sep1 or not sep2 or not minutes.strip().isdigit():
                self.send_and_mark(thread.pk, f"Usage: {self.config.command_prefix} event add <minutes> | <title> | <message>", last_msg.id)
                return
            self.storage.add_schedule(thread.pk, title.strip(), message.strip(), int(time.time()) + int(minutes.strip()) * 60)
            self.send_and_mark(thread.pk, f"Event scheduled: {title.strip()}", last_msg.id)
            return
        if lower_tail == "inactive":
            cutoff = int(time.time()) - self.config.inactive_days * 86400
            rows = self.storage.inactive_members(thread.pk, cutoff)
            names = ", ".join(f"@{row['username']}" for row in rows[:20]) or "none"
            self.send_and_mark(thread.pk, f"Inactive members ({self.config.inactive_days}d): {names}", last_msg.id)
            return
        if lower_tail == "report":
            since = int(time.time()) - self.config.report_hours * 3600
            events, top = self.storage.report_counts(thread.pk, since)
            counts = {row["event_type"]: row["count"] for row in events}
            top_text = ", ".join(f"@{row['username']}:{row['count']}" for row in top) or "none"
            self.send_and_mark(
                thread.pk,
                f"Group report\nMessages: {counts.get('message', 0)}\nTop active: {top_text}",
                last_msg.id,
            )
            return

    def handle_welcome(self, thread, last_msg, tail, lower_tail):
        if lower_tail == "welcome on":
            self.storage.set_welcome_enabled(thread.pk, True)
            self.send_and_mark(thread.pk, "Welcome messages enabled.", last_msg.id)
            return
        if lower_tail == "welcome off":
            self.storage.set_welcome_enabled(thread.pk, False)
            self.send_and_mark(thread.pk, "Welcome messages disabled.", last_msg.id)
            return
        if lower_tail.startswith("welcome set "):
            message = tail[len("welcome set ") :].strip()
            if not message:
                self.send_and_mark(thread.pk, f"Usage: {self.config.command_prefix} welcome set <message>", last_msg.id)
                return
            self.storage.set_welcome(thread.pk, message)
            self.send_and_mark(thread.pk, "Welcome message updated.", last_msg.id)
            return
        prefix = self.config.command_prefix
        self.send_and_mark(thread.pk, f"Usage: {prefix} welcome set <message> | {prefix} welcome on/off", last_msg.id)

    def handle_group_command(self, thread, last_msg, tail, lower_tail):
        if lower_tail == "gc info":
            users = ", ".join(f"@{user.username}" for user in thread.users[:20])
            title = thread.thread_title or "(no title)"
            self.send_and_mark(
                thread.pk,
                f"Group info\nTitle: {title}\nThread ID: {thread.pk}\nMembers shown: {users or 'none'}",
                last_msg.id,
            )
            return
        if lower_tail == "gc list":
            threads = self.cl.direct_threads(amount=20)
            groups = [item for item in threads if is_group_thread(item)]
            lines = ["Recent group chats"]
            lines.extend(f"- {item.thread_title or '(no title)'} | ID: {item.pk} | members: {len(item.users)}" for item in groups[:10])
            self.send_and_mark(thread.pk, "\n".join(lines) if groups else "No recent group chats found.", last_msg.id)
            return
        if lower_tail.startswith("gc create "):
            payload = tail[len("gc create ") :].strip()
            users_part, _, title_part = payload.partition("|")
            usernames = extract_usernames(users_part)
            if len(usernames) < 2:
                self.send_and_mark(thread.pk, f"Usage: {self.config.command_prefix} gc create @user1 @user2 | Group Title", last_msg.id)
                return
            user_ids, missing = resolve_user_ids(self.cl, usernames)
            if missing:
                self.send_and_mark(thread.pk, "Could not find: " + ", ".join(f"@{name}" for name in missing), last_msg.id)
                return
            title = title_part.strip() or "NEXUS Group"
            new_thread_id = self.cl.direct_thread_create(user_ids=user_ids, title=title)
            self.cl.direct_send(f"Group created: {title}", thread_ids=[new_thread_id])
            self.send_and_mark(thread.pk, f"Created group '{title}'. Thread ID: {new_thread_id}", last_msg.id)
            return
        if lower_tail.startswith("gc add "):
            if not is_group_thread(thread):
                self.send_and_mark(thread.pk, "This command works only inside a group chat.", last_msg.id)
                return
            usernames = extract_usernames(tail[len("gc add ") :])
            user_ids, missing = resolve_user_ids(self.cl, usernames)
            if missing:
                self.send_and_mark(thread.pk, "Could not find: " + ", ".join(f"@{name}" for name in missing), last_msg.id)
                return
            self.cl.direct_thread_add_users(thread_id=int(thread.pk), user_ids=user_ids)
            self.send_and_mark(thread.pk, "Added users: " + ", ".join(f"@{name}" for name in usernames), last_msg.id)
            return
        if lower_tail.startswith("gc title "):
            title = tail[len("gc title ") :].strip()
            if not title:
                self.send_and_mark(thread.pk, f"Usage: {self.config.command_prefix} gc title New Title", last_msg.id)
                return
            self.cl.direct_thread_update_title(thread_id=int(thread.pk), title=title)
            self.storage.upsert_group(thread.pk, title)
            self.send_and_mark(thread.pk, f"Group title updated to: {title}", last_msg.id)
            return
        self.send_and_mark(thread.pk, f"Unknown group command. Send {self.config.command_prefix} controls.", last_msg.id)


    # ------------------------------------------------------------------
    # Level & Economy Command Handlers
    # ------------------------------------------------------------------

    def process_xp_gain(self, thread, last_msg, sender_name):
        # Ignore backlog messages sent before bot startup
        raw_ts = getattr(last_msg, "timestamp", 0)
        msg_time = 0
        if hasattr(raw_ts, "timestamp"):
            msg_time = int(raw_ts.timestamp())
        elif isinstance(raw_ts, (int, float)):
            val = int(raw_ts)
            msg_time = val // 1_000_000 if val > 2_000_000_000 else (val // 1000 if val > 2_000_000 else val)
        elif isinstance(raw_ts, str) and raw_ts.isdigit():
            val = int(raw_ts)
            msg_time = val // 1_000_000 if val > 2_000_000_000 else (val // 1000 if val > 2_000_000 else val)

        if msg_time > 0 and msg_time < (self.start_time - 30):
            return

        res = self.storage.add_user_xp(
            thread.pk,
            last_msg.user_id,
            sender_name,
            self.config.xp_per_message,
            self.config.level2_xp,
            self.config.level3_xp,
        )
        if res["leveled_up"]:
            msg = f"🎉 LEVEL UP! @{sender_name}\n🌟 Level {res['level']} Achieved! Title: [{res['title']}]"
    # ------------------------------------------------------------------
    # External API Command Handlers
    # ------------------------------------------------------------------

    def handle_advice(self, thread, last_msg):
        try:
            res = requests.get("https://api.adviceslip.com/advice", timeout=10, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}).json()
            advice = res.get("slip", {}).get("advice", "")
            if advice:
                msg = f"💡 RANDOM ADVICE 💡\n━━━━━━━━━━━━━━━━━━━━\n\"{advice}\""
                self.send_and_mark(thread.pk, msg, last_msg.id)
                return True
        except Exception as exc:
            console.error(f"Advice API failed: {exc}")
        self.send_and_mark(thread.pk, "💡 Advice: Always do your best, what you plant now, you will harvest later!", last_msg.id)
        return True

    def handle_joke_api(self, thread, last_msg):
        try:
            res = requests.get("https://official-joke-api.appspot.com/random_joke", timeout=10, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}).json()
            setup = res.get("setup", "")
            punchline = res.get("punchline", "")
            if setup and punchline:
                msg = f"😂 RANDOM JOKE 😂\n━━━━━━━━━━━━━━━━━━━━\n❓ {setup}\n\n💬 {punchline}"
                self.send_and_mark(thread.pk, msg, last_msg.id)
                return True
        except Exception as exc:
            console.error(f"Joke API failed: {exc}")
        self.send_and_mark(thread.pk, "😂 Joke: Why don't scientists trust atoms? Because they make up everything!", last_msg.id)
        return True

    def handle_recipe(self, thread, last_msg):
        try:
            res = requests.get(
                "https://www.themealdb.com/api/json/v1/1/random.php",
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            ).json()

            meal = res.get("meals", [{}])[0]
            name = meal.get("strMeal", "Delicious Dish")
            category = meal.get("strCategory", "General")
            area = meal.get("strArea", "International")
            instructions = meal.get("strInstructions", "").strip()
            youtube = meal.get("strYoutube", "").strip()
            source = meal.get("strSource", "").strip()

            # Parse Ingredients & Measurements
            ingredients = []
            for i in range(1, 21):
                ing = meal.get(f"strIngredient{i}", "")
                meas = meal.get(f"strMeasure{i}", "")
                if ing and ing.strip():
                    ing_str = ing.strip()
                    if meas and meas.strip():
                        ing_str += f" ({meas.strip()})"
                    ingredients.append(f"• {ing_str}")

            ing_text = "\n".join(ingredients) if ingredients else "• Standard ingredients"

            if len(instructions) > 400:
                instructions = instructions[:397] + "..."

            msg_parts = [
                "🍳 RANDOM MEAL & RECIPE 🍳",
                "━━━━━━━━━━━━━━━━━━━━",
                f"🍱 Dish: {name}",
                f"📂 Category: {category} | Cuisine: {area}",
                "",
                "🛒 INGREDIENTS:",
                ing_text,
                "",
                f"📖 INSTRUCTIONS:\n{instructions}"
            ]

            if youtube:
                msg_parts.append(f"\n▶️ YouTube Video: {youtube}")
            if source:
                msg_parts.append(f"🔗 Full Recipe Source: {source}")

            msg = "\n".join(msg_parts)
            self.send_and_mark(thread.pk, msg, last_msg.id)
            return True
        except Exception as exc:
            console.error(f"Recipe API failed: {exc}")
        self.send_and_mark(thread.pk, "🍳 Recipe: Check out www.themealdb.com for amazing random recipes!", last_msg.id)
        return True

    def handle_bored(self, thread, last_msg):
        try:
            try:
                res = requests.get("https://bored-api.appbrewery.com/random", timeout=10, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}).json()
            except Exception:
                res = requests.get("https://www.boredapi.com/api/activity", timeout=10, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}).json()

            activity = res.get("activity", "")
            act_type = str(res.get("type", "general")).capitalize()
            participants = res.get("participants", 1)
            if activity:
                msg = f"🎯 BORED? TRY THIS ACTIVITY! 🎯\n━━━━━━━━━━━━━━━━━━━━\n💡 Activity: {activity}\n🏷️ Category: {act_type}\n👥 Participants: {participants}"
                self.send_and_mark(thread.pk, msg, last_msg.id)
                return True
        except Exception as exc:
            console.error(f"Bored API failed: {exc}")
        self.send_and_mark(thread.pk, "🎯 Bored? Try reading a book, learning 5 words in a new language, or playing chess!", last_msg.id)
        return True

    def handle_yesno(self, thread, last_msg, raw_tail=""):
        try:
            question = re.sub(r"^(yesno|decide|decision)\\s*", "", raw_tail, flags=re.IGNORECASE).strip()
            res = requests.get("https://yesno.wtf/api", timeout=10, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}).json()
            answer = str(res.get("answer", "maybe")).upper()
            image_url = res.get("image", "")

            q_str = f"❓ Question: {question}\n" if question else ""
            msg = f"🎲 DECISION MAKER (YES / NO) 🎲\n━━━━━━━━━━━━━━━━━━━━\n{q_str}🔮 Answer: {answer}!"

            if image_url:
                os.makedirs("data/media", exist_ok=True)
                temp_raw = "data/media/temp_yesno_raw.gif"
                if self.cl.download_file(image_url, temp_raw):
                    ready_jpeg = prepare_dm_image(temp_raw, "data/media/yesno_ready.jpg")
                    try:
                        self.cl.direct_send_photo(ready_jpeg, thread_ids=[thread.pk])
                    except Exception as exc:
                        console.warning(f"YesNo photo send failed: {exc}")

            self.send_and_mark(thread.pk, msg, last_msg.id)
            return True
        except Exception as exc:
            console.error(f"YesNo API failed: {exc}")
        self.send_and_mark(thread.pk, "🎲 Decision: YES! Go for it!", last_msg.id)
        return True

    def handle_fact(self, thread, last_msg):
        try:
            res = requests.get("https://uselessfacts.jsph.pl/api/v2/facts/random", timeout=10, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}).json()
            fact_text = res.get("text", "")
            if fact_text:
                msg = f"🤓 RANDOM USELESS FACT 🤓\n━━━━━━━━━━━━━━━━━━━━\n\"{fact_text}\""
                self.send_and_mark(thread.pk, msg, last_msg.id)
                return True
        except Exception as exc:
            console.error(f"Fact API failed: {exc}")
        self.send_and_mark(thread.pk, "🤓 Fact: Honey never spoils. Archaeologists have found 3000-year-old honey that is still edible!", last_msg.id)
        return True

    def handle_daily(self, thread, last_msg, sender_name):
        res = self.storage.claim_daily(
            thread.pk,
            last_msg.user_id,
            sender_name,
            reward_coins=self.config.daily_coins,
            cooldown_hours=self.config.daily_cooldown_hours,
        )
        if res["success"]:
            msg = (
                f"🎁 DAILY REWARD CLAIMED! @{sender_name}\n"
                f"+{res['reward']} Coins Added! 💰\n"
                f"Total Balance: {res['coins']} Coins"
            )
        else:
            msg = f"⏳ @{sender_name} - {res['reason']}"
        self.send_and_mark(thread.pk, msg, last_msg.id)

    def handle_balance_or_rank(self, thread, last_msg, sender_name):
        profile = self.storage.get_or_create_user_economy(thread.pk, last_msg.user_id, sender_name)
        xp = profile["xp"]
        level = profile["level"]
        coins = profile["coins"]
        badge = profile.get("title_badge") or "Novice"

        # Calculate progress to next level
        if level == 1:
            next_target = self.config.level2_xp
            next_name = "Level 2 (Elite)"
        elif level == 2:
            next_target = self.config.level3_xp
            next_name = "Level 3 (Legend)"
        else:
            next_target = xp
            next_name = "MAX LEVEL REACHED!"

        needed = max(0, next_target - xp) if level < 3 else 0

        msg = (
            f"👤 PLAYER PROFILE | @{sender_name}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎖️ Level: {level} [{badge}]\n"
            f"✨ XP: {xp} (Target: {next_target})\n"
            f"📈 Progress to {next_name}: {needed} XP needed\n"
            f"💰 Coins: {coins} Coins\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 Har 10 messages = +100 XP! Claim /daily every 24h!"
        )
        self.send_and_mark(thread.pk, msg, last_msg.id)

    def handle_shop(self, thread, last_msg):
        shop_msg = (
            "🛒 TITLE BADGE SHOP 🛒\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "1. 🌟 [VIP] - 500 Coins (Cmd: /buy 1)\n"
            "2. 🔥 [Master] - 1000 Coins (Cmd: /buy 2)\n"
            "3. 👑 [Royalty] - 2500 Coins (Cmd: /buy 3)\n"
            "4. ⚡ [Champion] - 5000 Coins (Cmd: /buy 4)\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💡 Balance check: /balance | Gift: /gift @user <amount>"
        )
        self.send_and_mark(thread.pk, shop_msg, last_msg.id)

    def handle_buy(self, thread, last_msg, tail, sender_name):
        parts = tail.replace("buy", "").strip().split()
        item_id = parts[0] if parts else ""
        items = {
            "1": ("VIP Title", 500, "VIP"),
            "2": ("Master Title", 1000, "Master"),
            "3": ("Royalty Title", 2500, "Royalty"),
            "4": ("Champion Title", 5000, "Champion"),
        }
        if item_id not in items:
            self.send_and_mark(thread.pk, f"❌ Invalid item ID! Use '{self.config.command_prefix} shop' or '/shop' to see item IDs (1, 2, 3, 4).", last_msg.id)
            return

        name, cost, badge = items[item_id]
        res = self.storage.buy_shop_item(thread.pk, last_msg.user_id, sender_name, name, cost, badge)
        if res["success"]:
            msg = (
                f"🎉 PURCHASE SUCCESSFUL! @{sender_name}\n"
                f"You unlocked badge: [{res['badge']}]! 🏅\n"
                f"Remaining Balance: {res['remaining_coins']} Coins"
            )
        else:
            msg = f"❌ @{sender_name} - {res['reason']}"
        self.send_and_mark(thread.pk, msg, last_msg.id)

    def handle_gift(self, thread, last_msg, tail, sender_name):
        parts = tail.replace("gift", "").strip().split()
        if len(parts) < 2:
            self.send_and_mark(thread.pk, f"Usage: {self.config.command_prefix} gift @user <amount> or /gift @user <amount>", last_msg.id)
            return

        target_name = parts[0].lstrip("@")
        try:
            amount = int(parts[1])
        except ValueError:
            self.send_and_mark(thread.pk, "❌ Amount ek integer number hona chahiye!", last_msg.id)
            return

        target_id = None
        for user in thread.users:
            if getattr(user, "username", "").lower() == target_name.lower():
                target_id = str(user.pk)
                break

        if not target_id:
            self.send_and_mark(thread.pk, f"❌ Member @{target_name} is group chat me nahi mila!", last_msg.id)
            return

        if target_id == str(last_msg.user_id):
            self.send_and_mark(thread.pk, "❌ Aap apne aap ko coins gift nahi kar sakte!", last_msg.id)
            return

        res = self.storage.transfer_coins(thread.pk, str(last_msg.user_id), target_id, target_name, amount)
        if res["success"]:
            msg = (
                f"🎁 GIFT TRANSFERRED! @{sender_name} ➔ @{target_name}\n"
                f"💰 {res['amount']} Coins transferred!\n"
                f"Your balance: {res['sender_balance']} Coins"
            )
        else:
            msg = f"❌ @{sender_name} - {res['reason']}"
        self.send_and_mark(thread.pk, msg, last_msg.id)

    def handle_leaderboard(self, thread, last_msg):
        rows = self.storage.get_leaderboard(thread.pk, limit=10)
        if not rows:
            self.send_and_mark(thread.pk, "🏆 Leaderboard empty hai! Abhi messages send karna start karein.", last_msg.id)
            return

        lines = ["🏆 GROUP LEADERBOARD 🏆", "━━━━━━━━━━━━━━━━━━━━"]
        medals = ["🥇", "🥈", "🥉"]
        for idx, row in enumerate(rows):
            rank_icon = medals[idx] if idx < 3 else f"#{idx+1}"
            uname = row["username"] or f"User-{row['user_id'][-4:]}"
            lines.append(f"{rank_icon} @{uname} | Lvl {row['level']} [{row['title_badge']}] - {row['xp']} XP | {row['coins']}💰")

        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append("💡 Earn XP by messaging & /daily!")
        self.send_and_mark(thread.pk, "\n".join(lines), last_msg.id)


    # ------------------------------------------------------------------
    # Polls & Lurker Commands
    # ------------------------------------------------------------------

    def handle_lurkers(self, thread, last_msg):
        lurkers = self.storage.track_group_activity_and_find_lurkers(thread.pk, thread.users, min_threshold=20, max_threshold=100)
        if not lurkers:
            self.send_and_mark(thread.pk, "✨ Koi 20-100 msgs se silent lurker nahi mila! Sab active hain.", last_msg.id)
            return

        lines = ["👀 SILENT READERS / LURKERS DETECTED (20-100 MSGs Silent)", "━━━━━━━━━━━━━━━━━━━━"]
        for l in lurkers[:10]:
            lines.append(f"👻 @{l['username']} - {l['msgs_missed']} messages se silent spectator bane ho! Kuch toh bolo! 😂")

        lines.append("━━━━━━━━━━━━━━━━━━━━")
        self.send_and_mark(thread.pk, "\n".join(lines), last_msg.id)
