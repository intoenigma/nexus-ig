"""Utility commands (hi, hello, ping, rules)."""

def handle_greeting(sender_name: str) -> str:
    return f"Hello @{sender_name}! How are you doing today? 😊"

def handle_ping() -> str:
    return "🏓 Pong! Bot is active, ultra-fast & running smoothly! ⚡"

def handle_rules(rules_text: str = None) -> str:
    rules = rules_text or "1. Be respectful to all members.\n2. No spam or unauthorized link promotion.\n3. Keep conversations friendly!"
    return f"📜 GROUP RULES 📜\n━━━━━━━━━━━━━━━━━━━━\n{rules}"
