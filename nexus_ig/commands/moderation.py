"""Moderation commands & Lurker detector."""

def format_lurkers_report(lurkers: list[dict], threshold_days: int = 7) -> str:
    if not lurkers:
        return f"👻 LURKER REPORT 👻\n━━━━━━━━━━━━━━━━━━━━\nAwesome! No silent lurkers found (silent for >{threshold_days} days)."
    lines = [f"👻 SILENT LURKERS (No msgs >{threshold_days} days) 👻", "━━━━━━━━━━━━━━━━━━━━"]
    for l in lurkers[:25]:
        uname = l.get("username", "User")
        days = l.get("inactive_days", 0)
        lines.append(f"• @{uname} - {days}d silent")
    return "\n".join(lines)
