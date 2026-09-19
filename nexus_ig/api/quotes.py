"""API client for advice/quotes."""
import requests

def fetch_advice():
    try:
        res = requests.get("https://api.adviceslip.com/advice", timeout=8, headers={"User-Agent": "Mozilla/5.0"}).json()
        advice = res.get("slip", {}).get("advice", "")
        if advice:
            return f"💡 RANDOM ADVICE 💡\n━━━━━━━━━━━━━━━━━━━━\n\"{advice}\""
    except Exception:
        pass
    return "💡 Advice: Always do your best, what you plant now, you will harvest later!"
