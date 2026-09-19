"""Economy & Coin management service."""

SHOP_ITEMS = {
    "1": {"name": "VIP Title", "cost": 500, "badge": "VIP"},
    "2": {"name": "Master Title", "cost": 1000, "badge": "Master"},
    "3": {"name": "Royalty Title", "cost": 2500, "badge": "Royalty"},
    "4": {"name": "Champion Title", "cost": 5000, "badge": "Champion"},
}

def validate_transfer(amount: int, sender_balance: int) -> tuple[bool, str]:
    if amount <= 0:
        return False, "Transfer amount 1 se bada hona chahiye!"
    if sender_balance < amount:
        return False, f"Aapke paas पर्याप्त coins nahi hain! (Balance: {sender_balance} Coins)"
    return True, "Valid"
