import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _csv(value):
    return [item.strip().lstrip("@") for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Config:
    session_file: str
    database_file: str
    backup_dir: str
    target_thread_id: str
    poll_interval: int
    thread_fetch_amount: int
    reply_delay_seconds: float
    instagram_delay_min: float
    instagram_delay_max: float
    welcome_message: str
    command_prefix: str
    admin_usernames: set[str]
    admin_user_ids: set[str]
    owner_username: str
    max_replied_messages: int
    rules_message: str
    rules_reminder_hours: int
    inactive_days: int
    report_hours: int
    revive_hours: int
    revive_minutes: int
    revive_message: str
    media_dir: str
    # Economy / Level system
    xp_per_message: int
    daily_coins: int
    daily_cooldown_hours: int
    level2_xp: int
    level3_xp: int
    # Maintenance / Offline mode
    maintenance_mode: bool
    maintenance_message: str
    # Leave & Remove Notification Messages
    leave_message: str
    remove_message: str


def load_config():
    load_dotenv(override=True)
    data_dir = Path(os.getenv("DATA_DIR", "data"))
    data_dir.mkdir(exist_ok=True)

    owner_username = os.getenv("OWNER_USERNAME", "").strip().lstrip("@")
    admin_usernames = set(_csv(os.getenv("ADMIN_USERNAMES", "")))
    if owner_username:
        admin_usernames.add(owner_username)

    m_mode_raw = os.getenv("MAINTENANCE_MODE", os.getenv("BOT_OFFLINE_MODE", "false")).strip().lower()
    m_mode = m_mode_raw in ("true", "1", "yes", "on")
    m_msg = os.getenv("MAINTENANCE_MESSAGE", os.getenv("BOT_OFFLINE_MESSAGE", "Bot band hai, kal aana! 😴")).strip()

    return Config(
        session_file=os.getenv("SESSION_FILE", "session.json"),
        database_file=os.getenv("DATABASE_FILE", str(data_dir / "nexus.db")),
        backup_dir=os.getenv("BACKUP_DIR", str(data_dir / "backups")),
        target_thread_id=os.getenv("TARGET_THREAD_ID", "").strip(),
        poll_interval=float(os.getenv("CHECK_INTERVAL", "1")),
        thread_fetch_amount=int(os.getenv("THREAD_FETCH_AMOUNT", "20")),
        reply_delay_seconds=float(os.getenv("REPLY_DELAY_SECONDS", "0")),
        instagram_delay_min=float(os.getenv("INSTAGRAM_DELAY_MIN", "0")),
        instagram_delay_max=float(os.getenv("INSTAGRAM_DELAY_MAX", "0")),
        welcome_message=os.getenv("WELCOME_MESSAGE", "hi Im NEXUS"),
        command_prefix=os.getenv("COMMAND_PREFIX", "nexus").strip() or "nexus",

        admin_usernames=admin_usernames,
        admin_user_ids={item.strip() for item in os.getenv("ADMIN_USER_IDS", "").split(",") if item.strip()},
        owner_username=owner_username,
        max_replied_messages=int(os.getenv("MAX_REPLIED_MESSAGES", "5000")),
        rules_message=os.getenv("RULES_MESSAGE", "Respect everyone. No spam, scams, or unknown links."),
        rules_reminder_hours=int(os.getenv("RULES_REMINDER_HOURS", "12")),
        inactive_days=int(os.getenv("INACTIVE_DAYS", "7")),
        report_hours=int(os.getenv("REPORT_HOURS", "24")),
        revive_hours=int(os.getenv("REVIVE_HOURS", "24")),
        revive_minutes=int(os.getenv("REVIVE_MINUTES", "10")),
        revive_message=os.getenv("REVIVE_MESSAGE", "everyone kha ho saalo aa jao group mai"),
        media_dir=os.getenv("MEDIA_DIR", str(data_dir / "media")),
        xp_per_message=int(os.getenv("XP_PER_MESSAGE", "10")),
        daily_coins=int(os.getenv("DAILY_COINS", "100")),
        daily_cooldown_hours=int(os.getenv("DAILY_COOLDOWN_HOURS", "20")),
        level2_xp=int(os.getenv("LEVEL2_XP", "500")),
        level3_xp=int(os.getenv("LEVEL3_XP", "2000")),
        maintenance_mode=m_mode,
        maintenance_message=m_msg,
        leave_message=os.getenv("LEAVE_MESSAGE", "🚪 @username group chhod ke chala gaya hai! Bye 👋").strip(),
        remove_message=os.getenv("REMOVE_MESSAGE", "🚫 @username ko group se remove kar diya gaya hai! 🚨").strip(),
    )
