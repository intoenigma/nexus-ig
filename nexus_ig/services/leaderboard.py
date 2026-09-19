"""Leaderboard calculation and formatting service."""

def build_leaderboard_card(rows: list[dict]) -> str:
    if not rows:
        return "🏆 LEADERBOARD 🏆\n━━━━━━━━━━━━━━━━━━━━\nAbhi tak koi activity record nahi hui hai!"
    lines = ["🏆 GROUP LEADERBOARD 🏆", "━━━━━━━━━━━━━━━━━━━━"]
    medals = ["🥇", "🥈", "🥉"]
    for idx, row in enumerate(rows):
        rank = medals[idx] if idx < 3 else f"#{idx+1}"
        uname = row.get("username", "User")
        lvl = row.get("level", 1)
        xp = row.get("xp", 0)
        badge = row.get("title_badge", "Novice")
        lines.append(f"{rank} @{uname} | Level {lvl} [{badge}] - {xp} XP")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 Keep chatting to climb the leaderboard!")
    return "\n".join(lines)
