import sqlite3
import time
from pathlib import Path


class Storage:
    def __init__(self, database_file):
        self.database_file = database_file
        Path(database_file).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(database_file)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self.conn.execute("PRAGMA busy_timeout=10000;")
        self._replied_cache = set()
        self.setup()

    def setup(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS user_profiles (
                username TEXT PRIMARY KEY,
                thread_id TEXT DEFAULT '',
                user_id TEXT DEFAULT '',
                full_name TEXT,
                bio TEXT,
                followers_count INTEGER NOT NULL DEFAULT 0,
                following_count INTEGER NOT NULL DEFAULT 0,
                posts_count INTEGER NOT NULL DEFAULT 0,
                is_private INTEGER NOT NULL DEFAULT 0,
                is_verified INTEGER NOT NULL DEFAULT 0,
                updated_at INTEGER NOT NULL DEFAULT 0,
                fetched_at INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS forbidden_words (
                word TEXT PRIMARY KEY,
                created_at INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS user_economy (
                thread_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                username TEXT,
                xp INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 1,
                coins INTEGER NOT NULL DEFAULT 0,
                last_daily INTEGER NOT NULL DEFAULT 0,
                title_badge TEXT DEFAULT 'Novice',
                updated_at INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (thread_id, user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_economy_rank
                ON user_economy (thread_id, level DESC, xp DESC);

            CREATE TABLE IF NOT EXISTS greeted_threads (
                thread_id TEXT PRIMARY KEY,
                title TEXT,
                greeted_at INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS replied_messages (
                message_id TEXT PRIMARY KEY,
                thread_id TEXT,
                replied_at INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS group_settings (
                thread_id TEXT PRIMARY KEY,
                title TEXT,
                welcome_message TEXT,
                welcome_enabled INTEGER NOT NULL DEFAULT 1,
                commands_enabled INTEGER NOT NULL DEFAULT 1,
                updated_at INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS warnings (
                thread_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                username TEXT,
                count INTEGER NOT NULL DEFAULT 0,
                warn_count INTEGER NOT NULL DEFAULT 0,
                last_reason TEXT DEFAULT '',
                updated_at INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (thread_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS member_activity (
                thread_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                username TEXT,
                joined_at INTEGER,
                first_seen_at INTEGER NOT NULL DEFAULT 0,
                last_seen_at INTEGER NOT NULL DEFAULT 0,
                message_count INTEGER NOT NULL DEFAULT 0,
                msg_count INTEGER NOT NULL DEFAULT 0,
                reputation INTEGER NOT NULL DEFAULT 0,
                last_message_text TEXT,
                last_message_at INTEGER,
                PRIMARY KEY (thread_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS member_snapshots (
                thread_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                username TEXT,
                seen_at INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (thread_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT,
                event_type TEXT NOT NULL,
                user_id TEXT,
                username TEXT,
                detail TEXT,
                created_at INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS keyword_replies (
                thread_id TEXT NOT NULL,
                keyword TEXT NOT NULL,
                reply TEXT NOT NULL,
                updated_at INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (thread_id, keyword)
            );

            CREATE TABLE IF NOT EXISTS birthdays (
                thread_id TEXT NOT NULL,
                user_id TEXT,
                username TEXT NOT NULL,
                month INTEGER NOT NULL,
                day INTEGER NOT NULL,
                message TEXT,
                PRIMARY KEY (thread_id, username)
            );

            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                run_at INTEGER NOT NULL,
                repeat_seconds INTEGER NOT NULL DEFAULT 0,
                last_run_at INTEGER
            );

            CREATE TABLE IF NOT EXISTS thread_state (
                thread_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                updated_at INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (thread_id, key)
            );

            CREATE TABLE IF NOT EXISTS messages (
                message_id              TEXT PRIMARY KEY,
                thread_id               TEXT NOT NULL,
                thread_title            TEXT,
                user_id                 TEXT NOT NULL,
                username                TEXT,
                full_name               TEXT,
                is_bot_message          INTEGER NOT NULL DEFAULT 0,
                item_type               TEXT NOT NULL DEFAULT 'text',
                text                    TEXT,
                replied_to_message_id   TEXT,
                replied_to_user_id      TEXT,
                replied_to_text         TEXT,
                media_id                TEXT,
                media_subtype           TEXT,
                media_url               TEXT,
                media_thumbnail_url     TEXT,
                media_width             INTEGER,
                media_height            INTEGER,
                media_duration_ms       INTEGER,
                media_local_path        TEXT,
                voice_url               TEXT,
                voice_duration_ms       INTEGER,
                voice_waveform_json     TEXT,
                voice_local_path        TEXT,
                sticker_id              TEXT,
                sticker_url             TEXT,
                sticker_static_url      TEXT,
                sticker_local_path      TEXT,
                share_url               TEXT,
                share_caption           TEXT,
                share_type              TEXT,
                share_thumbnail_url     TEXT,
                link_url                TEXT,
                link_title              TEXT,
                link_description        TEXT,
                link_image_url          TEXT,
                reactions_json          TEXT,
                extra_json              TEXT,
                sent_at                 INTEGER NOT NULL DEFAULT 0,
                recorded_at             INTEGER NOT NULL DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_messages_thread
                ON messages (thread_id, sent_at DESC);

            CREATE INDEX IF NOT EXISTS idx_messages_user
                ON messages (user_id, sent_at DESC);

            CREATE TABLE IF NOT EXISTS message_reactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id  TEXT NOT NULL,
                thread_id   TEXT NOT NULL,
                user_id     TEXT NOT NULL,
                username    TEXT,
                emoji       TEXT NOT NULL,
                reacted_at  INTEGER,
                UNIQUE (message_id, user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_reactions_msg
                ON message_reactions (message_id);
            """
        )
        self.conn.commit()

    def close(self):
        self.conn.close()

    def backup_to(self, backup_dir):
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        target = Path(backup_dir) / f"nexus-{time.strftime('%Y%m%d-%H%M%S')}.db"
        backup_conn = sqlite3.connect(target)
        self.conn.backup(backup_conn)
        backup_conn.close()
        return str(target)


    def has_greeted(self, thread_id):
        row = self.conn.execute("SELECT 1 FROM greeted_threads WHERE thread_id = ?", (str(thread_id),)).fetchone()
        return row is not None

    def mark_greeted(self, thread_id, title):
        self.conn.execute(
            "INSERT OR IGNORE INTO greeted_threads(thread_id, title, greeted_at) VALUES (?, ?, ?)",
            (str(thread_id), title, int(time.time())),
        )
        self.conn.commit()

    def has_replied(self, message_id):
        mid = str(message_id)
        if mid in self._replied_cache:
            return True
        row = self.conn.execute("SELECT 1 FROM replied_messages WHERE message_id = ?", (mid,)).fetchone()
        if row is not None:
            self._replied_cache.add(mid)
            if len(self._replied_cache) > 20000:
                self._replied_cache.clear()
            return True
        return False

    def mark_replied(self, message_id, thread_id):
        mid = str(message_id)
        self._replied_cache.add(mid)
        self.conn.execute(
            "INSERT OR IGNORE INTO replied_messages(message_id, thread_id, replied_at) VALUES (?, ?, ?)",
            (mid, str(thread_id), int(time.time())),
        )
        self.conn.commit()

    def prune_replied(self, keep):
        self.conn.execute(
            """
            DELETE FROM replied_messages
            WHERE message_id NOT IN (
                SELECT message_id FROM replied_messages ORDER BY replied_at DESC LIMIT ?
            )
            """,
            (keep,),
        )
        self.conn.commit()

    def upsert_group(self, thread_id, title):
        self.conn.execute(
            """
            INSERT INTO group_settings(thread_id, title, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(thread_id) DO UPDATE SET title = excluded.title, updated_at = excluded.updated_at
            """,
            (str(thread_id), title, int(time.time())),
        )
        self.conn.commit()

    def get_group(self, thread_id):
        return self.conn.execute("SELECT * FROM group_settings WHERE thread_id = ?", (str(thread_id),)).fetchone()

    def get_group_title(self, thread_id: str) -> str:
        try:
            row = self.conn.execute("SELECT title FROM group_settings WHERE thread_id = ?", (str(thread_id),)).fetchone()
            if row and row["title"]:
                return row["title"]
            row_greet = self.conn.execute("SELECT title FROM greeted_threads WHERE thread_id = ?", (str(thread_id),)).fetchone()
            if row_greet and row_greet["title"]:
                return row_greet["title"]
        except Exception:
            pass
        return "Group"


    def set_welcome(self, thread_id, message):
        self.conn.execute(
            """
            INSERT INTO group_settings(thread_id, welcome_message, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(thread_id) DO UPDATE SET welcome_message = excluded.welcome_message, updated_at = excluded.updated_at
            """,
            (str(thread_id), message, int(time.time())),
        )
        self.conn.commit()

    def set_welcome_enabled(self, thread_id, enabled):
        self.conn.execute(
            """
            INSERT INTO group_settings(thread_id, welcome_enabled, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(thread_id) DO UPDATE SET welcome_enabled = excluded.welcome_enabled, updated_at = excluded.updated_at
            """,
            (str(thread_id), 1 if enabled else 0, int(time.time())),
        )
        self.conn.commit()

    def add_warning(self, thread_id, user_id, username):
        self.conn.execute(
            """
            INSERT INTO warnings(thread_id, user_id, username, count, updated_at)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(thread_id, user_id) DO UPDATE
            SET count = count + 1, username = excluded.username, updated_at = excluded.updated_at
            """,
            (str(thread_id), str(user_id), username, int(time.time())),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT count FROM warnings WHERE thread_id = ? AND user_id = ?",
            (str(thread_id), str(user_id)),
        ).fetchone()
        return int(row["count"])

    def log_event(self, thread_id, event_type, user_id=None, username=None, detail=None):
        self.conn.execute(
            "INSERT INTO events(thread_id, event_type, user_id, username, detail, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (str(thread_id) if thread_id else None, event_type, str(user_id) if user_id else None, username, detail, int(time.time())),
        )
        self.conn.commit()

    def touch_member(self, thread_id, user_id, username, text=None):
        now = int(time.time())
        current = self.conn.execute(
            "SELECT message_count FROM member_activity WHERE thread_id = ? AND user_id = ?",
            (str(thread_id), str(user_id)),
        ).fetchone()
        if current:
            self.conn.execute(
                """
                UPDATE member_activity
                SET username = ?, last_seen_at = ?, message_count = message_count + 1,
                    last_message_text = ?, last_message_at = ?
                WHERE thread_id = ? AND user_id = ?
                """,
                (username, now, text, now, str(thread_id), str(user_id)),
            )
        else:
            self.conn.execute(
                """
                INSERT INTO member_activity(
                    thread_id, user_id, username, joined_at, first_seen_at, last_seen_at,
                    message_count, last_message_text, last_message_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (str(thread_id), str(user_id), username, now, now, now, text, now),
            )
        self.conn.commit()

    def set_members_snapshot(self, thread_id, users):
        now = int(time.time())
        old_rows = self.conn.execute(
            "SELECT user_id, username FROM member_snapshots WHERE thread_id = ?",
            (str(thread_id),),
        ).fetchall()
        old = {row["user_id"]: row["username"] for row in old_rows}
        is_first_run = len(old) == 0

        new = {str(user.pk): user.username for user in users if getattr(user, "pk", None)}

        if is_first_run:
            # On first snapshot, seed database with existing members without triggering join events
            joined = []
            left = []
        else:
            joined = [(uid, name) for uid, name in new.items() if uid not in old]
            left = [(uid, name) for uid, name in old.items() if uid not in new]

        for uid, name in joined:
            self.log_event(thread_id, "join", uid, name)
        for uid, name in left:
            self.log_event(thread_id, "leave", uid, name)

        self.conn.execute("DELETE FROM member_snapshots WHERE thread_id = ?", (str(thread_id),))
        self.conn.executemany(
            "INSERT INTO member_snapshots(thread_id, user_id, username, seen_at) VALUES (?, ?, ?, ?)",
            [(str(thread_id), uid, name, now) for uid, name in new.items()],
        )
        self.conn.commit()
        return joined, left

    def recent_messages(self, thread_id, user_id, seconds):
        cutoff = int(time.time()) - seconds
        return self.conn.execute(
            """
            SELECT detail, created_at FROM events
            WHERE thread_id = ? AND user_id = ? AND event_type = 'message' AND created_at >= ?
            ORDER BY created_at DESC
            """,
            (str(thread_id), str(user_id), cutoff),
        ).fetchall()

    def set_state(self, thread_id, key, value):
        self.conn.execute(
            """
            INSERT INTO thread_state(thread_id, key, value, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(thread_id, key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (str(thread_id), key, str(value), int(time.time())),
        )
        self.conn.commit()

    def get_state(self, thread_id, key, default=None):
        row = self.conn.execute(
            "SELECT value FROM thread_state WHERE thread_id = ? AND key = ?",
            (str(thread_id), key),
        ).fetchone()
        return row["value"] if row else default

    def keyword_reply(self, thread_id, text):
        words = [word.strip(".,!?;:()[]{}").lower() for word in text.split()]
        if not words:
            return None
        placeholders = ",".join("?" for _ in words)
        params = [str(thread_id), *words]
        return self.conn.execute(
            f"SELECT keyword, reply FROM keyword_replies WHERE thread_id = ? AND lower(keyword) IN ({placeholders}) LIMIT 1",
            params,
        ).fetchone()

    def set_keyword_reply(self, thread_id, keyword, reply):
        self.conn.execute(
            """
            INSERT INTO keyword_replies(thread_id, keyword, reply, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(thread_id, keyword) DO UPDATE SET reply = excluded.reply, updated_at = excluded.updated_at
            """,
            (str(thread_id), keyword.lower(), reply, int(time.time())),
        )
        self.conn.commit()

    def delete_keyword_reply(self, thread_id, keyword):
        self.conn.execute("DELETE FROM keyword_replies WHERE thread_id = ? AND keyword = ?", (str(thread_id), keyword.lower()))
        self.conn.commit()

    def set_birthday(self, thread_id, username, month, day, message=None, user_id=None):
        self.conn.execute(
            """
            INSERT OR REPLACE INTO birthdays(thread_id, user_id, username, month, day, message)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (str(thread_id), str(user_id) if user_id else None, username.lstrip("@"), month, day, message),
        )
        self.conn.commit()

    def birthdays_today(self, thread_id, month, day):
        return self.conn.execute(
            "SELECT * FROM birthdays WHERE thread_id = ? AND month = ? AND day = ?",
            (str(thread_id), month, day),
        ).fetchall()

    def add_schedule(self, thread_id, title, message, run_at, repeat_seconds=0):
        self.conn.execute(
            "INSERT INTO schedules(thread_id, title, message, run_at, repeat_seconds) VALUES (?, ?, ?, ?, ?)",
            (str(thread_id), title, message, int(run_at), int(repeat_seconds)),
        )
        self.conn.commit()

    def due_schedules(self, now):
        return self.conn.execute("SELECT * FROM schedules WHERE run_at <= ?", (int(now),)).fetchall()

    def mark_schedule_run(self, schedule_id, next_run_at=None):
        if next_run_at:
            self.conn.execute(
                "UPDATE schedules SET run_at = ?, last_run_at = ? WHERE id = ?",
                (int(next_run_at), int(time.time()), schedule_id),
            )
        else:
            self.conn.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
        self.conn.commit()

    def inactive_members(self, thread_id, cutoff):
        return self.conn.execute(
            "SELECT username, user_id, last_seen_at FROM member_activity WHERE thread_id = ? AND last_seen_at < ? ORDER BY last_seen_at",
            (str(thread_id), int(cutoff)),
        ).fetchall()

    def report_counts(self, thread_id, since):
        events = self.conn.execute(
            """
            SELECT event_type, COUNT(*) AS count FROM events
            WHERE thread_id = ? AND created_at >= ?
            GROUP BY event_type
            """,
            (str(thread_id), int(since)),
        ).fetchall()
        top = self.conn.execute(
            """
            SELECT username, COUNT(*) AS count FROM events
            WHERE thread_id = ? AND event_type = 'message' AND created_at >= ?
            GROUP BY user_id, username ORDER BY count DESC LIMIT 5
            """,
            (str(thread_id), int(since)),
        ).fetchall()
        return events, top

    def top_members(self, thread_id, since, limit=5):
        return self.conn.execute(
            """
            SELECT username, COUNT(*) AS count FROM events
            WHERE thread_id = ? AND event_type = 'message' AND created_at >= ?
            GROUP BY user_id, username ORDER BY count DESC LIMIT ?
            """,
            (str(thread_id), int(since), int(limit)),
        ).fetchall()

    # ------------------------------------------------------------------
    # Message archive
    # ------------------------------------------------------------------

    def message_exists(self, message_id) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM messages WHERE message_id = ?",
            (str(message_id),),
        ).fetchone()
        return row is not None

    def archive_message(self, **kw):
        """Insert a complete message record.  All fields are keyword args.
        Required: message_id, thread_id, user_id, item_type, sent_at.
        Every other field defaults to None / 0 if omitted.
        """
        self.conn.execute(
            """
            INSERT OR IGNORE INTO messages (
                message_id, thread_id, thread_title,
                user_id, username, full_name, is_bot_message,
                item_type, text,
                replied_to_message_id, replied_to_user_id, replied_to_text,
                media_id, media_subtype, media_url, media_thumbnail_url,
                media_width, media_height, media_duration_ms, media_local_path,
                voice_url, voice_duration_ms, voice_waveform_json, voice_local_path,
                sticker_id, sticker_url, sticker_static_url, sticker_local_path,
                share_url, share_caption, share_type, share_thumbnail_url,
                link_url, link_title, link_description, link_image_url,
                reactions_json, extra_json,
                sent_at, recorded_at
            ) VALUES (
                ?,?,?,
                ?,?,?,?,
                ?,?,
                ?,?,?,
                ?,?,?,?,
                ?,?,?,?,
                ?,?,?,?,
                ?,?,?,?,
                ?,?,?,?,
                ?,?,?,?,
                ?,?,
                ?,?
            )
            """,
            (
                str(kw["message_id"]),
                str(kw["thread_id"]),
                kw.get("thread_title"),

                str(kw["user_id"]),
                kw.get("username"),
                kw.get("full_name"),
                int(kw.get("is_bot_message", 0)),

                kw["item_type"],
                kw.get("text"),

                kw.get("replied_to_message_id"),
                kw.get("replied_to_user_id"),
                kw.get("replied_to_text"),

                kw.get("media_id"),
                kw.get("media_subtype"),
                kw.get("media_url"),
                kw.get("media_thumbnail_url"),
                kw.get("media_width"),
                kw.get("media_height"),
                kw.get("media_duration_ms"),
                kw.get("media_local_path"),

                kw.get("voice_url"),
                kw.get("voice_duration_ms"),
                kw.get("voice_waveform_json"),
                kw.get("voice_local_path"),

                kw.get("sticker_id"),
                kw.get("sticker_url"),
                kw.get("sticker_static_url"),
                kw.get("sticker_local_path"),

                kw.get("share_url"),
                kw.get("share_caption"),
                kw.get("share_type"),
                kw.get("share_thumbnail_url"),

                kw.get("link_url"),
                kw.get("link_title"),
                kw.get("link_description"),
                kw.get("link_image_url"),

                kw.get("reactions_json"),
                kw.get("extra_json"),

                int(kw["sent_at"]),
                int(time.time()),
            ),
        )
        self.conn.commit()

    def upsert_reaction(
        self,
        message_id: str,
        thread_id: str,
        user_id: str,
        emoji: str,
        username: str | None = None,
        reacted_at: int | None = None,
    ):
        self.conn.execute(
            """
            INSERT INTO message_reactions (message_id, thread_id, user_id, username, emoji, reacted_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (message_id, user_id)
            DO UPDATE SET emoji = excluded.emoji, reacted_at = excluded.reacted_at, username = excluded.username
            """,
            (str(message_id), str(thread_id), str(user_id), username, emoji, reacted_at),
        )
        self.conn.commit()


    # ------------------------------------------------------------------
    # Economy & Leveling System
    # ------------------------------------------------------------------

    def get_or_create_user_economy(self, thread_id: str, user_id: str, username: str | None = None):
        row = self.conn.execute(
            "SELECT * FROM user_economy WHERE thread_id = ? AND user_id = ?",
            (str(thread_id), str(user_id)),
        ).fetchone()
        if not row:
            now = int(time.time())
            self.conn.execute(
                """
                INSERT INTO user_economy (thread_id, user_id, username, xp, level, coins, last_daily, title_badge, updated_at)
                VALUES (?, ?, ?, 0, 1, 0, 0, 'Novice', ?)
                """,
                (str(thread_id), str(user_id), username, now),
            )
            self.conn.commit()
            row = self.conn.execute(
                "SELECT * FROM user_economy WHERE thread_id = ? AND user_id = ?",
                (str(thread_id), str(user_id)),
            ).fetchone()
        elif username and row["username"] != username:
            self.conn.execute(
                "UPDATE user_economy SET username = ? WHERE thread_id = ? AND user_id = ?",
                (username, str(thread_id), str(user_id)),
            )
            self.conn.commit()
        return dict(row)

    def add_user_xp(self, thread_id: str, user_id: str, username: str | None, xp_gained: int, lvl2_xp: int = 500, lvl3_xp: int = 2000):
        profile = self.get_or_create_user_economy(thread_id, user_id, username)
        current_xp = profile["xp"] + xp_gained
        current_level = profile["level"]
        new_level = current_level
        title = profile.get("title_badge") or "Novice"

        if current_xp >= lvl3_xp:
            new_level = 3
            title = "Legend"
        elif current_xp >= lvl2_xp:
            new_level = 2
            title = "Elite"
        else:
            new_level = 1
            title = "Novice"

        leveled_up = new_level > current_level

        self.conn.execute(
            """
            UPDATE user_economy
            SET xp = ?, level = ?, title_badge = ?, updated_at = ?
            WHERE thread_id = ? AND user_id = ?
            """,
            (current_xp, new_level, title, int(time.time()), str(thread_id), str(user_id)),
        )
        self.conn.commit()
        return {
            "xp": current_xp,
            "level": new_level,
            "title": title,
            "leveled_up": leveled_up,
            "old_level": current_level
        }

    def claim_daily(self, thread_id: str, user_id: str, username: str | None, reward_coins: int = 100, cooldown_hours: int = 20):
        profile = self.get_or_create_user_economy(thread_id, user_id, username)
        now = int(time.time())
        cooldown_sec = cooldown_hours * 3600
        last_daily = profile["last_daily"]

        if now - last_daily < cooldown_sec:
            remaining_sec = cooldown_sec - (now - last_daily)
            hours = remaining_sec // 3600
            minutes = (remaining_sec % 3600) // 60
            return {
                "success": False,
                "reason": f"Aapne pehle hi claim kar liya hai. Dobara claim karne ke liye {hours}h {minutes}m wait karein.",
                "coins": profile["coins"]
            }

        new_coins = profile["coins"] + reward_coins
        self.conn.execute(
            """
            UPDATE user_economy
            SET coins = ?, last_daily = ?, updated_at = ?
            WHERE thread_id = ? AND user_id = ?
            """,
            (new_coins, now, now, str(thread_id), str(user_id)),
        )
        self.conn.commit()
        return {
            "success": True,
            "reward": reward_coins,
            "coins": new_coins
        }

    def transfer_coins(self, thread_id: str, from_user_id: str, to_user_id: str, to_username: str | None, amount: int):
        if amount <= 0:
            return {"success": False, "reason": "Amount 1 se zyada hona chahiye!"}

        sender = self.get_or_create_user_economy(thread_id, from_user_id)
        if sender["coins"] < amount:
            return {"success": False, "reason": f"Aapke paas kaafi coins nahi hain! Balance: {sender['coins']} coins"}

        receiver = self.get_or_create_user_economy(thread_id, to_user_id, to_username)

        now = int(time.time())
        self.conn.execute(
            "UPDATE user_economy SET coins = coins - ?, updated_at = ? WHERE thread_id = ? AND user_id = ?",
            (amount, now, str(thread_id), str(from_user_id)),
        )
        self.conn.execute(
            "UPDATE user_economy SET coins = coins + ?, updated_at = ? WHERE thread_id = ? AND user_id = ?",
            (amount, now, str(thread_id), str(to_user_id)),
        )
        self.conn.commit()
        return {
            "success": True,
            "amount": amount,
            "sender_balance": sender["coins"] - amount,
            "receiver_balance": receiver["coins"] + amount
        }

    def buy_shop_item(self, thread_id: str, user_id: str, username: str | None, item_name: str, cost: int, badge_name: str):
        profile = self.get_or_create_user_economy(thread_id, user_id, username)
        if profile["coins"] < cost:
            return {"success": False, "reason": f"Coins kam hain! Cost: {cost} coins, Balance: {profile['coins']} coins"}

        now = int(time.time())
        new_coins = profile["coins"] - cost
        self.conn.execute(
            """
            UPDATE user_economy
            SET coins = ?, title_badge = ?, updated_at = ?
            WHERE thread_id = ? AND user_id = ?
            """,
            (new_coins, badge_name, now, str(thread_id), str(user_id)),
        )
        self.conn.commit()
        return {"success": True, "badge": badge_name, "remaining_coins": new_coins}

    def get_leaderboard(self, thread_id: str, limit: int = 10):
        return self.conn.execute(
            """
            SELECT username, user_id, xp, level, coins, title_badge
            FROM user_economy
            WHERE thread_id = ?
            ORDER BY level DESC, xp DESC
            LIMIT ?
            """,
            (str(thread_id), int(limit)),
        ).fetchall()


    # ------------------------------------------------------------------
    # Interactive Polls & Lurker Detector
    # ------------------------------------------------------------------

    def track_group_activity_and_find_lurkers(self, thread_id: str, users: list, min_threshold: int = 20, max_threshold: int = 100):
        """Find users who haven't sent msgs in 20 to 100 group messages."""
        lurkers = []
        for user in users:
            uid = str(getattr(user, "pk", ""))
            uname = getattr(user, "username", "Unknown")
            if not uid:
                continue

            activity = self.conn.execute(
                "SELECT message_count, last_message_at FROM member_activity WHERE thread_id = ? AND user_id = ?",
                (str(thread_id), uid),
            ).fetchone()

            last_msg_at = activity["last_message_at"] if (activity and activity["last_message_at"]) else 0

            if last_msg_at == 0:
                msgs_since = self.conn.execute(
                    "SELECT COUNT(*) as count FROM messages WHERE thread_id = ?",
                    (str(thread_id),),
                ).fetchone()["count"]
            else:
                msgs_since = self.conn.execute(
                    "SELECT COUNT(*) as count FROM messages WHERE thread_id = ? AND sent_at > ?",
                    (str(thread_id), last_msg_at),
                ).fetchone()["count"]

            if min_threshold <= msgs_since < max_threshold:
                lurkers.append({
                    "user_id": uid,
                    "username": uname,
                    "msgs_missed": msgs_since
                })

        lurkers.sort(key=lambda x: x["msgs_missed"], reverse=True)
        return lurkers

    # ------------------------------------------------------------------
    # User Profile & Instaloader Details Upsert
    # ------------------------------------------------------------------
    def save_user_profile_details(self, thread_id: str, user_id: str, username: str, full_name: str, bio: str, followers: int, following: int, posts: int, is_private: bool, is_verified: bool):
        now = int(time.time())
        clean_user = str(username).lower().lstrip("@")
        with self.conn:
            self.conn.execute(
                '''INSERT INTO user_profiles (username, thread_id, user_id, full_name, bio, followers_count, following_count, posts_count, is_private, is_verified, updated_at, fetched_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(username) DO UPDATE SET
                   thread_id=excluded.thread_id,
                   user_id=excluded.user_id,
                   full_name=excluded.full_name,
                   bio=excluded.bio,
                   followers_count=excluded.followers_count,
                   following_count=excluded.following_count,
                   posts_count=excluded.posts_count,
                   is_private=excluded.is_private,
                   is_verified=excluded.is_verified,
                   updated_at=excluded.updated_at,
                   fetched_at=excluded.fetched_at''',
                (clean_user, str(thread_id), str(user_id), str(full_name), str(bio), int(followers), int(following), int(posts), 1 if is_private else 0, 1 if is_verified else 0, now, now)
            )

    # ------------------------------------------------------------------
    # Warnings & Bad Words Management
    # ------------------------------------------------------------------

    def add_warning(self, thread_id: str, user_id: str, username: str, reason: str = "Bad behavior") -> int:
        now = int(time.time())
        with self.conn:
            cursor = self.conn.execute(
                "SELECT warn_count FROM warnings WHERE thread_id = ? AND user_id = ?",
                (str(thread_id), str(user_id))
            )
            row = cursor.fetchone()
            new_count = (row["warn_count"] if row else 0) + 1
            self.conn.execute(
                '''INSERT INTO warnings (thread_id, user_id, username, warn_count, last_reason, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(thread_id, user_id) DO UPDATE SET
                   warn_count = excluded.warn_count,
                   last_reason = excluded.last_reason,
                   updated_at = excluded.updated_at''',
                (str(thread_id), str(user_id), str(username), new_count, str(reason), now)
            )
            return new_count

    def get_warnings(self, thread_id: str, user_id: str) -> dict:
        cursor = self.conn.execute(
            "SELECT warn_count, last_reason FROM warnings WHERE thread_id = ? AND user_id = ?",
            (str(thread_id), str(user_id))
        )
        row = cursor.fetchone()
        return {"warn_count": row["warn_count"], "last_reason": row["last_reason"]} if row else {"warn_count": 0, "last_reason": "None"}

    def add_forbidden_word(self, word: str):
        now = int(time.time())
        with self.conn:
            self.conn.execute("INSERT OR IGNORE INTO forbidden_words (word, created_at) VALUES (?, ?)", (word.lower().strip(), now))

    def remove_forbidden_word(self, word: str):
        with self.conn:
            self.conn.execute("DELETE FROM forbidden_words WHERE word = ?", (word.lower().strip(),))

    def get_forbidden_words(self) -> list[str]:
        cursor = self.conn.execute("SELECT word FROM forbidden_words")
        return [row["word"] for row in cursor.fetchall()]

    # ------------------------------------------------------------------
    # Group Revival Active Members (Last 7 Days)
    # ------------------------------------------------------------------

    def get_active_members_7days(self, thread_id: str) -> list[dict]:
        seven_days_ago = int(time.time()) - (7 * 86400)
        try:
            cursor = self.conn.execute(
                '''SELECT DISTINCT username, user_id FROM messages
                   WHERE thread_id = ? AND (sent_at >= ? OR recorded_at >= ?) AND username IS NOT NULL AND username != '' ''',
                (str(thread_id), seven_days_ago, seven_days_ago)
            )
            rows = cursor.fetchall()
        except Exception:
            rows = []

        if not rows:
            try:
                cursor = self.conn.execute(
                    '''SELECT DISTINCT username, user_id FROM member_activity
                       WHERE thread_id = ? AND last_seen_at >= ? AND username IS NOT NULL AND username != '' ''',
                    (str(thread_id), seven_days_ago)
                )
                rows = cursor.fetchall()
            except Exception:
                rows = []
        return [{"username": r["username"], "user_id": r["user_id"]} for r in rows if r["username"]]
