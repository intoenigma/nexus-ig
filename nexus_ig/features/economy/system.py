"""Economy catalog and shop system."""

SHOP_CATALOG = {
    "1": {"name": "👑 VIP Title", "cost": 500, "badge": "VIP"},
    "2": {"name": "🔥 Legend Title", "cost": 1000, "badge": "Legend"},
    "3": {"name": "⭐ Star Title", "cost": 250, "badge": "Star"},
    "4": {"name": "🛡️ Guardian Title", "cost": 750, "badge": "Guardian"},
}

def get_shop_menu() -> str:
    return (
        "🛒 BOT ECONOMY SHOP 🛒\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "1. 👑 VIP Title - 500 Coins\n"
        "2. 🔥 Legend Title - 1000 Coins\n"
        "3. ⭐ Star Title - 250 Coins\n"
        "4. 🛡️ Guardian Title - 750 Coins\n\n"
        "Type 'nexus buy <id>' to purchase an item!"
    )
