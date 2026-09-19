"""API client for facts."""
import requests

def fetch_fact():
    try:
        res = requests.get("https://uselessfacts.jsph.pl/api/v2/facts/random?language=en", timeout=8, headers={"User-Agent": "Mozilla/5.0"}).json()
        fact = res.get("text", "")
        if fact:
            return f"📌 RANDOM FACT 📌\n━━━━━━━━━━━━━━━━━━━━\n{fact}"
    except Exception:
        pass
    return "📌 Fact: Honey never spoils. Authentic honey found in ancient Egyptian tombs is still edible!"
