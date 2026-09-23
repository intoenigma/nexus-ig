import random
import re
import time

from . import console


class Scheduler:
    def __init__(self, cl, storage, config):
        self.cl = cl
        self.storage = storage
        self.config = config

    def run_for_thread(self, thread):
        now = int(time.time())
        thread_id = thread.pk
        self._rules_reminder(thread_id, now)
        self._birthdays(thread_id, now)
        self._custom_schedules(now)
        self._reports(thread_id, now)
        self._dead_group_revive(thread_id, now)
        self._weekly_appreciation(thread_id, now)
        self._daily_backup(now)

    def _send(self, thread_id, text):
        self.cl.direct_send(text, thread_ids=[thread_id])
        console.success(f"Scheduled message sent | thread {thread_id}")
        if self.config.reply_delay_seconds > 0:
            time.sleep(self.config.reply_delay_seconds)

    def _rules_reminder(self, thread_id, now):
        key = "last_rules_reminder"
        last = int(self.storage.get_state(thread_id, key, "0") or "0")
        if now - last >= self.config.rules_reminder_hours * 3600:
            self._send(thread_id, "Group rules\n" + self.config.rules_message)
            self.storage.set_state(thread_id, key, now)

    def _birthdays(self, thread_id, now):
        today = time.localtime(now)
        key = f"birthday_sent:{today.tm_year}:{today.tm_mon}:{today.tm_mday}"
        if self.storage.get_state(thread_id, key):
            return
        rows = self.storage.birthdays_today(thread_id, today.tm_mon, today.tm_mday)
        for row in rows:
            message = row["message"] or f"Happy birthday @{row['username']}!"
            self._send(thread_id, message)
        if rows:
            self.storage.set_state(thread_id, key, "1")

    def _custom_schedules(self, now):
        for row in self.storage.due_schedules(now):
            self._send(row["thread_id"], row["message"])
            repeat = int(row["repeat_seconds"] or 0)
            next_run = now + repeat if repeat else None
            self.storage.mark_schedule_run(row["id"], next_run)

    def _reports(self, thread_id, now):
        key = "last_report"
        last = int(self.storage.get_state(thread_id, key, "0") or "0")
        if now - last < self.config.report_hours * 3600:
            return
        since = now - self.config.report_hours * 3600
        events, top = self.storage.report_counts(thread_id, since)
        counts = {row["event_type"]: row["count"] for row in events}
        top_text = ", ".join(f"@{row['username']}:{row['count']}" for row in top) or "none"
        text = (
            "Group report\n"
            f"Messages: {counts.get('message', 0)}\n"
            f"Top active: {top_text}"
        )
        self._send(thread_id, text)
        self.storage.set_state(thread_id, key, now)

    def _dead_group_revive(self, thread_id, now):
        if self.config.revive_minutes <= 0:
            return

        key = "last_revive"
        last_revive = int(self.storage.get_state(thread_id, key, "0") or "0")

        last_message = self.storage.conn.execute(
            "SELECT MAX(sent_at) AS last_at FROM messages WHERE thread_id = ?",
            (str(thread_id),),
        ).fetchone()

        last_at = int(last_message["last_at"]) if (last_message and last_message["last_at"]) else 0
        revive_sec = self.config.revive_minutes * 60

        if last_at > 0 and (now - last_at >= revive_sec) and (now - last_revive >= revive_sec):
            raw_msg = self.config.revive_message or "everyone kha ho saalo aa jao group mai"
            msg_list = [m.strip() for m in re.split(r"[,|;]", raw_msg) if m.strip()]
            selected_msg = random.choice(msg_list) if msg_list else raw_msg
            self._send(thread_id, selected_msg)
            self.storage.set_state(thread_id, key, now)

    def _weekly_appreciation(self, thread_id, now):
        key = "last_appreciation"
        last = int(self.storage.get_state(thread_id, key, "0") or "0")
        if now - last < 7 * 86400:
            return
        rows = self.storage.top_members(thread_id, now - 7 * 86400, 5)
        if not rows:
            return
        names = "\n".join(f"- @{row['username']} ({row['count']} msgs)" for row in rows)
        self._send(thread_id, "Weekly active members\n" + names)
        self.storage.set_state(thread_id, key, now)

    def _daily_backup(self, now):
        key = "last_backup"
        last = int(self.storage.get_state("global", key, "0") or "0")
        if now - last < 86400:
            return
        path = self.storage.backup_to(self.config.backup_dir)
        console.success(f"Database backup created: {path}")
        self.storage.set_state("global", key, now)
