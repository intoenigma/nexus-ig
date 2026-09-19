"""Admin & Group Control commands."""

def format_status_report(config, account_name: str, my_pk: str) -> str:
    return (
        "📊 NEXUS BOT STATUS REPORT 📊\n"

        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 Account: @{account_name} (ID: {my_pk})\n"
        f"⚡ Poll Interval: {config.poll_interval}s\n"
        f"🎯 Target Group: {config.target_thread_id or 'All groups'}\n"
        f"🛡️ Admin Users: {len(config.admin_usernames)}\n"
        "🟢 Status: Operational & Healthy"
    )

def format_gc_info(thread) -> str:
    title = getattr(thread, "thread_title", "Group") or "Group"
    users_count = len(getattr(thread, "users", []))
    thread_id = getattr(thread, "pk", "Unknown")
    return (
        "ℹ️ GROUP CHAT INFO ℹ️\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 Title: {title}\n"
        f"🆔 Thread ID: {thread_id}\n"
        f"👥 Members Count: {users_count}"
    )
