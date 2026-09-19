import time

from ..services.archiver import MessageArchiver
from ..commands import CommandHandler
from .config import load_config
from . import console
from ..instagram.login import login_client
from ..instagram.groups import is_group_thread
from .scheduler import Scheduler
from .storage import Storage


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
        self.storage.upsert_group(thread.pk, thread.thread_title or "")
        group = self.storage.get_group(thread.pk)
        if group and not group["welcome_enabled"]:
            return
        message = group["welcome_message"] if group and group["welcome_message"] else self.config.welcome_message
        console.success(f"New group greeted: {thread.thread_title or thread.pk}")
        self.cl.direct_send(message, thread_ids=[thread.pk])
        self.storage.mark_greeted(thread.pk, thread.thread_title or "")
        if self.config.reply_delay_seconds > 0:
            time.sleep(self.config.reply_delay_seconds)

    def sync_members(self, thread):
        if self.config.target_thread_id and str(thread.pk) != self.config.target_thread_id:
            return
        if not is_group_thread(thread):
            return
        known_group = self.storage.has_greeted(thread.pk)
        joined, left = self.storage.set_members_snapshot(thread.pk, thread.users)
        group = self.storage.get_group(thread.pk)
        welcome_enabled = not group or group["welcome_enabled"]
        welcome_message = group["welcome_message"] if group and group["welcome_message"] else self.config.welcome_message

        if known_group and len(joined) >= 5:
            self.storage.set_state(thread.pk, "slow_until", int(time.time()) + 1800)
            console.warning(f"Raid protection suggested for {thread.thread_title or thread.pk}")

        for user_id, username in joined:
            self.storage.touch_member(thread.pk, user_id, username, "joined")
            if known_group and welcome_enabled:
                self.cl.direct_send(
                    f"Welcome @{username}\n\n{welcome_message}\n\nGroup rules\n{self.config.rules_message}",
                    thread_ids=[thread.pk],
                )
                console.success(f"New member welcomed: @{username}")
                if self.config.reply_delay_seconds > 0:
                    time.sleep(self.config.reply_delay_seconds)

        for _user_id, username in left:
            console.status("LEFT", f"@{username} left {thread.thread_title or thread.pk}")

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
        console.startup(self.config, self.account_name, self.my_pk)

        while True:
            try:
                self.reload_config()
                console.status("CHECK", f"Target group {self.config.target_thread_id}")
                if self.config.target_thread_id:
                    try:
                        target_t = self.cl.direct_thread(self.config.target_thread_id, amount=self.config.thread_fetch_amount)
                        threads = [target_t] if target_t else []
                    except Exception:
                        threads = self.cl.direct_threads(amount=10)
                else:
                    threads = self.cl.direct_threads(amount=10)
                handled = 0
                for thread in threads:
                    if self.config.target_thread_id and str(thread.pk) != self.config.target_thread_id:
                        continue
                    self.storage.upsert_group(thread.pk, thread.thread_title or "")
                    self.sync_members(thread)
                    self.archiver.sync_thread(thread)
                    if thread.messages:
                        for msg in reversed(thread.messages):
                            try:
                                if self.handler.handle(thread, msg):
                                    handled += 1
                            except Exception as exc:
                                console.warning(f"Error handling message {getattr(msg, 'id', 'unknown')}: {exc}")
                    self.welcome_new_group(thread)
                    if is_group_thread(thread):
                        self.scheduler.run_for_thread(thread)
                self.storage.prune_replied(self.config.max_replied_messages)
                # Periodically save refreshed session cookies (every 15 mins) to keep session alive without password logins
                if not hasattr(self, "_last_cookie_dump"):
                    self._last_cookie_dump = time.time()
                elif time.time() - self._last_cookie_dump > 900:
                    self._last_cookie_dump = time.time()
                    self.dump_session_cookies()

                console.status("IDLE", f"Target actions: {handled}")
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

