"""XP & Level calculations service."""

def calculate_xp_gain(message_len: int, base_xp: int = 10) -> int:
    bonus = min(20, message_len // 10)
    return base_xp + bonus

def check_level_up(current_xp: int, current_level: int, level2_xp: int = 500, level3_xp: int = 1500) -> dict:
    if current_level < 2 and current_xp >= level2_xp:
        return {"leveled_up": True, "new_level": 2, "title": "Elite Chatting Titan"}
    if current_level < 3 and current_xp >= level3_xp:
        return {"leveled_up": True, "new_level": 3, "title": "Legendary Grandmaster"}
    return {"leveled_up": False, "new_level": current_level, "title": "Novice"}
