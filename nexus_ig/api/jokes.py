"""API client for jokes."""
import requests

def fetch_joke():
    try:
        res = requests.get("https://official-joke-api.appspot.com/random_joke", timeout=8, headers={"User-Agent": "Mozilla/5.0"}).json()
        setup = res.get("setup", "")
        punchline = res.get("punchline", "")
        if setup and punchline:
            return f"😂 RANDOM JOKE 😂\n━━━━━━━━━━━━━━━━━━━━\n❓ {setup}\n\n💬 {punchline}"
    except Exception:
        pass
    return "😂 Joke: Why don't scientists trust atoms? Because they make up everything!"
