import time

from ..services.archiver import MessageArchiver
from ..commands import CommandHandler
from .config import load_config
from . import console
from ..instagram.login import login_client
from ..instagram.groups import is_group_thread
from ..instagram.users import find_sender_name
from ..services.reel_reactor import handle_reel_reaction
from .scheduler import Scheduler
from .storage import Storage


def parse_message_action(msg) -> tuple[str, str]:
    """Extract (action_type, content_preview) from instagrapi DirectMessage."""
    item_type = getattr(msg, "item_type", "text")
    if item_type == "text":
        return "text", (getattr(msg, "text", "") or "").strip()
    elif item_type in ("clip", "reel_share"):
        caption = ""
        clip = getattr(msg, "clip", None) or getattr(msg, "reel_share", None)
        if clip:
            caption = getattr(clip, "caption_text", "") or getattr(clip, "title", "") or ""
        return "reel", caption.strip()
    elif item_type == "media_share":
        caption = ""
        share = getattr(msg, "media_share", None)
        if share:
            caption = getattr(share, "caption_text", "") or getattr(share, "title", "") or ""
        return "media_share", caption.strip()
    elif item_type == "media":
        media = getattr(msg, "media", None)
        media_type = getattr(media, "media_type", 1) if media else 1
        if media_type == 2:
            return "video", ""
        return "photo", ""
    elif item_type in ("voice_media", "voice"):
        return "voice", ""
    elif item_type in ("animated_media", "sticker"):
        return "sticker", ""
    elif item_type in ("story_share", "story"):
        return "story", ""
    elif item_type == "like":
        return "like", ""
    elif item_type == "link":
        link = getattr(msg, "link", None)
        url = getattr(link, "text", "") if link else ""
        return "link", url
    elif item_type == "placeholder":
        return "deleted", ""
    elif item_type == "action_log":
        log_type = getattr(getattr(msg, "action_log", None), "description", "")
        return "action", log_type
    return item_type or "text", (getattr(msg, "text", "") or "").strip()


class NexusBot:
    def __init__(self):
        self.config = load_config()
        self.storage = Storage(self.config.database_file)
        self.cl = None
        self.my_pk = None
        self.account_name = None
        self.handler = None
        self.scheduler = None
        self.archiver = None
        self.seen_msg_ids: set[str] = set()
        self.initialized_threads: set[str] = set()

    def reload_config(self):
        latest = load_config()
        if latest.database_file != self.config.database_file:
            console.warning("DATABASE_FILE changed. Restart required to switch SQLite database.")
        self.config = latest
        if self.handler:
            self.handler.config = latest
        if self.scheduler:
            self.scheduler.config = latest
        if self.cl:
            self.cl.apply_config(latest)

    def welcome_new_group(self, thread):
        if self.config.target_thread_id and str(thread.pk) != self.config.target_thread_id:
            return
        if not is_group_thread(thread) or self.storage.has_greeted(thread.pk):
            return
        grp_title = thread.thread_title or self.storage.get_group_title(thread.pk) or "Group"
        self.storage.upsert_group(thread.pk, grp_title)
        group = self.storage.get_group(thread.pk)
        if group and not group["welcome_enabled"]:
            return
        message = group["welcome_message"] if group and group["welcome_message"] else self.config.welcome_message
        self.cl.direct_send(message, thread_ids=[thread.pk])
        self.storage.mark_greeted(thread.pk, grp_title)
        console.log_activity(grp_title, self.account_name or "NexusBot", "reply", "Welcomed new group with rules", is_bot=True)
        if self.config.reply_delay_seconds > 0:
            time.sleep(self.config.reply_delay_seconds)

    def sync_members(self, thread):
        if self.config.target_thread_id and str(thread.pk) != self.config.target_thread_id:
            return
        if not is_group_thread(thread):
            return
        grp_title = thread.thread_title or self.storage.get_group_title(thread.pk) or "Group"
        known_group = self.storage.has_greeted(thread.pk)
        joined, left = self.storage.set_members_snapshot(thread.pk, thread.users)
        group = self.storage.get_group(thread.pk)
        welcome_enabled = not group or group["welcome_enabled"]
        welcome_message = group["welcome_message"] if group and group["welcome_message"] else self.config.welcome_message

        if known_group and len(joined) >= 5:
            self.storage.set_state(thread.pk, "slow_until", int(time.time()) + 1800)
            console.log_activity(grp_title, "Shield", "warn", "Raid protection suggested (5+ joins)")

        for user_id, username in joined:
            self.storage.touch_member(thread.pk, user_id, username, "joined")
            console.log_activity(grp_title, username, "join")
            if known_group and welcome_enabled:
                self.cl.direct_send(
                    f"Welcome @{username}\n\n{welcome_message}\n\nGroup rules\n{self.config.rules_message}",
                    thread_ids=[thread.pk],
                )
                console.log_activity(grp_title, self.account_name or "NexusBot", "reply", f"Welcomed @{username}", is_bot=True)
                if self.config.reply_delay_seconds > 0:
                    time.sleep(self.config.reply_delay_seconds)

        for _user_id, username in left:
            console.log_activity(grp_title, username, "left")

    def dump_session_cookies(self):
        try:
            self.cl.dump_settings(self.config.session_file)
        except Exception:
            pass

    def reauthenticate(self) -> bool:
        console.warning("Direct API session expired/locked. Backing off 10s before re-authenticating...")
        time.sleep(10)
        new_cl, new_pk, new_username = login_client(self.config)
        if new_cl:
            self.cl = new_cl
            self.my_pk = new_pk
            self.account_name = new_username
            self.handler.cl = new_cl
            self.scheduler.cl = new_cl
            self.archiver.cl = new_cl
            console.success("Auto-reauthentication successful! Active session refreshed.")
            return True
        return False

    def run(self):
        console.banner()
        self.cl, self.my_pk, self.account_name = login_client(self.config)
        if not self.cl:
            return

        self.handler = CommandHandler(self.cl, self.storage, self.config, self.my_pk)
        self.scheduler = Scheduler(self.cl, self.storage, self.config)
        self.archiver = MessageArchiver(self.cl, self.storage, self.config, self.my_pk)

        target_title = "All Connected Groups"
        if self.config.target_thread_id:
            target_title = self.storage.get_group_title(self.config.target_thread_id)
            if target_title == "Group":
                target_title = "Selected Target Group"

        console.startup(self.config, self.account_name, self.my_pk, target_group_name=target_title)

        while True:
            try:
                self.reload_config()
                if self.config.target_thread_id:
                    try:
                        target_t = self.cl.direct_thread(self.config.target_thread_id, amount=self.config.thread_fetch_amount)
                        threads = [target_t] if target_t else []
                    except Exception:
                        threads = self.cl.direct_threads(amount=10)
                else:
                    threads = self.cl.direct_threads(amount=10)

                for thread in threads:
                    if self.config.target_thread_id and str(thread.pk) != self.config.target_thread_id:
                        continue

                    grp_title = thread.thread_title or self.storage.get_group_title(thread.pk) or "Direct Chat"
                    self.storage.upsert_group(thread.pk, grp_title)
                    self.sync_members(thread)
                    self.archiver.sync_thread(thread)

                    # Populate seed messages on first sighting to prevent printing stale history
                    if str(thread.pk) not in self.initialized_threads:
                        self.initialized_threads.add(str(thread.pk))
                        if getattr(thread, "messages", None):
                            for old_msg in thread.messages:
                                self.seen_msg_ids.add(str(old_msg.id))

                    if getattr(thread, "messages", None):
                        for msg in reversed(thread.messages):
                            msg_id_str = str(msg.id)
                            # Live stream any new message received
                            if msg_id_str not in self.seen_msg_ids:
                                self.seen_msg_ids.add(msg_id_str)
                                sender_name = find_sender_name(thread, msg.user_id)
                                if str(msg.user_id) == str(self.my_pk):
                                    sender_name = self.account_name or "NexusBot"
                                is_bot = (str(msg.user_id) == str(self.my_pk))
                                is_admin = self.handler.is_admin(thread, msg.user_id)
                                act_type, act_content = parse_message_action(msg)
                                console.log_activity(
                                    grp_title,
                                    sender_name,
                                    act_type,
                                    act_content,
                                    is_bot=is_bot,
                                    is_admin=is_admin,
                                )

                                # 🎬 Auto-React to Reels based on Hashtags / Keywords
                                is_reel = (
                                    act_type in ("reel", "clip", "reel_share")
                                    or getattr(msg, "item_type", "") in ("clip", "reel_share")
                                    or (act_type == "link" and "instagram.com/reel" in act_content)
                                )
                                if not is_bot and is_reel:
                                    reacted_emoji = handle_reel_reaction(self.cl, thread.pk, msg)
                                    if reacted_emoji:
                                        console.log_activity(
                                            grp_title,
                                            self.account_name or "NexusBot",
                                            "reply",
                                            f"Reacted {reacted_emoji} to @{sender_name}'s Reel",
                                            is_bot=True,
                                        )

                            try:
                                self.handler.handle(thread, msg)
                            except Exception as exc:
                                console.warning(f"Error handling message: {exc}")

                    self.welcome_new_group(thread)
                    if is_group_thread(thread):
                        self.scheduler.run_for_thread(thread)

                self.storage.prune_replied(self.config.max_replied_messages)

                # Keep seen_msg_ids bounded to prevent unbounded memory growth
                if len(self.seen_msg_ids) > 5000:
                    self.seen_msg_ids = set(list(self.seen_msg_ids)[-2500:])

                # Periodically save refreshed session cookies (every 15 mins)
                if not hasattr(self, "_last_cookie_dump"):
                    self._last_cookie_dump = time.time()
                elif time.time() - self._last_cookie_dump > 900:
                    self._last_cookie_dump = time.time()
                    self.dump_session_cookies()

                time.sleep(self.config.poll_interval)
            except KeyboardInterrupt:
                console.warning("Bot stopped by user.")
                break
            except Exception as exc:
                err_str = str(exc).lower()
                if "login_required" in err_str or "loginrequired" in err_str:
                    console.warning(f"Session expired during polling: {exc}")
                    if self.reauthenticate():
                        time.sleep(1)
                        continue
                console.error(f"Polling failed: {exc}")
                console.warning("Retrying in 60 seconds")
                time.sleep(60)

        self.storage.close()


def main():
    NexusBot().run()


