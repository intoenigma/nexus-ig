"""Fun API commands & random generator cards."""
import requests

def get_advice_card() -> str:
    try:
        res = requests.get("https://api.adviceslip.com/advice", timeout=8, headers={"User-Agent": "Mozilla/5.0"}).json()
        advice = res.get("slip", {}).get("advice", "")
        if advice:
            return f"💡 ADVICE FOR YOU 💡\n━━━━━━━━━━━━━━━━━━━━\n{advice}"
    except Exception:
        pass
    return "💡 Advice: Take a deep breath and keep going!"

def get_joke_card() -> str:
    try:
        res = requests.get("https://official-joke-api.appspot.com/random_joke", timeout=8, headers={"User-Agent": "Mozilla/5.0"}).json()
        setup = res.get("setup", "")
        punchline = res.get("punchline", "")
        if setup and punchline:
            return f"😂 RANDOM JOKE 😂\n━━━━━━━━━━━━━━━━━━━━\n❓ {setup}\n\n💬 {punchline}"
    except Exception:
        pass
    return "😂 Joke: Why don't scientists trust atoms? Because they make up everything!"

def get_fact_card() -> str:
    try:
        res = requests.get("https://uselessfacts.jsph.pl/api/v2/facts/random?language=en", timeout=8, headers={"User-Agent": "Mozilla/5.0"}).json()
        fact = res.get("text", "")
        if fact:
            return f"📌 RANDOM FACT 📌\n━━━━━━━━━━━━━━━━━━━━\n{fact}"
    except Exception:
        pass
    return "📌 Fact: Honey never spoils. Authentic honey found in ancient Egyptian tombs is still edible!"

def get_bored_card() -> str:
    try:
        res = requests.get("https://bored.api.lewagon.com/api/activity", timeout=8, headers={"User-Agent": "Mozilla/5.0"}).json()
        activity = res.get("activity", "")
        if activity:
            return f"🎉 BORED ACTIVITY 🎉\n━━━━━━━━━━━━━━━━━━━━\n{activity}"
    except Exception:
        pass
    return "🎉 Activity: Go for a 15-minute walk outside!"

def get_yesno_card() -> str:
    try:
        res = requests.get("https://yesno.wtf/api", timeout=8, headers={"User-Agent": "Mozilla/5.0"}).json()
        answer = res.get("answer", "").upper()
        if answer:
            return f"🔮 THE ORACLE SAYS 🔮\n━━━━━━━━━━━━━━━━━━━━\n✨ {answer}"
    except Exception:
        pass
    return "🔮 Oracle: YES!"

def get_recipe_card() -> str:
    try:
        res = requests.get("https://www.themealdb.com/api/json/v1/1/random.php", timeout=8, headers={"User-Agent": "Mozilla/5.0"}).json()
        meals = res.get("meals", [])
        if meals:
            m = meals[0]
            title = m.get("strMeal", "")
            cat = m.get("strCategory", "")
            area = m.get("strArea", "")
            return f"🍲 RANDOM RECIPE 🍲\n━━━━━━━━━━━━━━━━━━━━\n🍽️ {title} ({cat}, {area})"
    except Exception:
        pass
    return "🍲 Recipe: Delicious Butter Chicken!"
