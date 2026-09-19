"""API client for meal recipes and discussion topics."""
import requests

def fetch_recipe():
    try:
        res = requests.get("https://www.themealdb.com/api/json/v1/1/random.php", timeout=8, headers={"User-Agent": "Mozilla/5.0"}).json()
        meal = res.get("meals", [{}])[0]
        name = meal.get("strMeal", "Delicious Dish")
        category = meal.get("strCategory", "General")
        area = meal.get("strArea", "International")
        instructions = meal.get("strInstructions", "").strip()
        youtube = meal.get("strYoutube", "").strip()
        source = meal.get("strSource", "").strip()

        ingredients = []
        for i in range(1, 21):
            ing = meal.get(f"strIngredient{i}", "")
            meas = meal.get(f"strMeasure{i}", "")
            if ing and ing.strip():
                ing_str = ing.strip()
                if meas and meas.strip():
                    ing_str += f" ({meas.strip()})"
                ingredients.append(f"• {ing_str}")

        ing_text = "\n".join(ingredients) if ingredients else "• Standard ingredients"
        if len(instructions) > 400:
            instructions = instructions[:397] + "..."

        msg_parts = [
            "🍳 RANDOM MEAL & RECIPE 🍳",
            "━━━━━━━━━━━━━━━━━━━━",
            f"🍱 Dish: {name}",
            f"📂 Category: {category} | Cuisine: {area}",
            "",
            "🛒 INGREDIENTS:",
            ing_text,
            "",
            f"📖 INSTRUCTIONS:\n{instructions}"
        ]
        if youtube:
            msg_parts.append(f"\n▶️ YouTube Video: {youtube}")
        if source:
            msg_parts.append(f"🔗 Full Recipe Source: {source}")
        return "\n".join(msg_parts)
    except Exception:
        pass
    return "🍳 Recipe: Check out www.themealdb.com for amazing random recipes!"
