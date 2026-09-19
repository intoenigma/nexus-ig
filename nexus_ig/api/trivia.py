"""API client for trivia and bored activities."""
import requests

def fetch_bored_activity():
    try:
        try:
            res = requests.get("https://bored-api.appbrewery.com/random", timeout=8, headers={"User-Agent": "Mozilla/5.0"}).json()
        except Exception:
            res = requests.get("https://www.boredapi.com/api/activity", timeout=8, headers={"User-Agent": "Mozilla/5.0"}).json()
        act = res.get("activity", "")
        typ = res.get("type", "general").capitalize()
        if act:
            return f"🎯 BORED ACTIVITY 🎯\n━━━━━━━━━━━━━━━━━━━━\n💡 Activity: {act}\n📂 Type: {typ}"
    except Exception:
        pass
    return "🎯 Bored? Try learning a new keyboard shortcut today!"

def fetch_yesno():
    try:
        res = requests.get("https://yesno.wtf/api", timeout=8, headers={"User-Agent": "Mozilla/5.0"}).json()
        ans = res.get("answer", "yes").upper()
        return f"🔮 THE ORACLE SAYS 🔮\n━━━━━━━━━━━━━━━━━━━━\n✨ Answer: {ans} ✨"
    except Exception:
        pass
    return "🔮 Oracle: YES!"
