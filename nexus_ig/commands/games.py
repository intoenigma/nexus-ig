"""Stateful Truth & Dare Game Engine (Explicit Lobby Mode)."""
import json
import random
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets"

def load_truth_questions() -> list[str]:
    try:
        path = ASSETS_DIR / "truth.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return [
        "Aapki life ka sabse embarrassing moment kya tha?",
        "Kya aapka kisi par secret crush hai?",
        "Aapki sabse weird habit kya hai?"
    ]

def load_dare_tasks() -> list[str]:
    try:
        path = ASSETS_DIR / "dare.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return [
        "Group mein 10 seconds ka voice note bhejo singing a song!",
        "Group mein kisiko 3 romantic lines dedicate karo!",
        "Next 3 messages tak sirf Emojis se baat karo!"
    ]

def get_truth_question() -> str:
    return random.choice(load_truth_questions())

def get_dare_task() -> str:
    return random.choice(load_dare_tasks())

class TruthAndDareGame:
    def __init__(self):
        self.lobbies = {}
        self.truths = load_truth_questions()
        self.dares = load_dare_tasks()

    def create_lobby(self, thread_id: str, players: list[str], creator_name: str) -> str:
        clean_players = list(dict.fromkeys([p.strip().lstrip("@") for p in players if p.strip()]))
        if not clean_players:
            clean_players = [creator_name]

        self.lobbies[str(thread_id)] = {
            "players": clean_players,
            "current_player": None,
            "state": "LOBBY"
        }
        player_list = "\n".join([f"{idx+1}. @{name}" for idx, name in enumerate(clean_players)])
        return (
            "🎯 TRUTH & DARE LOBBY CREATED! 🎯\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 Registered Players ({len(clean_players)}):\n"
            f"{player_list}\n\n"
            "🍾 Type 'oli tdstart' to spin the bottle and begin!"
        )

    def start_round(self, thread_id: str) -> str:
        tid = str(thread_id)
        if tid not in self.lobbies or not self.lobbies[tid]["players"]:
            return "❌ Koi active lobby nahi mili! Pehle 'oli tdgame @user1 @user2' type karke lobby banaayein."

        lobby = self.lobbies[tid]
        chosen = random.choice(lobby["players"])
        lobby["current_player"] = chosen
        lobby["state"] = "WAITING_CHOICE"

        return (
            "🍾 THE BOTTLE IS SPINNING... 🍾\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👉 The bottle points to: @{chosen}! ✨\n\n"
            f"@{chosen}, choose your fate! Reply with:\n"
            "• 'truth' or 'oli truth'\n"
            "• 'dare' or 'oli dare'"
        )

    def handle_choice(self, thread_id: str, choice: str, sender_name: str) -> str:
        tid = str(thread_id)
        if tid not in self.lobbies:
            return None

        lobby = self.lobbies[tid]
        clean_choice = choice.strip().lower()
        target = lobby.get("current_player") or sender_name

        if clean_choice in ("truth", "t", "oli truth"):
            q = random.choice(self.truths)
            lobby["state"] = "LOBBY"
            return (
                f"✨ TRUTH QUESTION FOR @{target} ✨\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"❓ {q}\n\n"
                "💬 Answer truthfully in group! Type 'oli tdstart' or 'oli tdnext' for next round! 🍾"
            )

        if clean_choice in ("dare", "d", "oli dare"):
            d = random.choice(self.dares)
            lobby["state"] = "LOBBY"
            return (
                f"🔥 DARE TASK FOR @{target} 🔥\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 {d}\n\n"
                "⚡ Complete the dare now! Type 'oli tdstart' or 'oli tdnext' for next round! 🍾"
            )

        return None

    def stop_game(self, thread_id: str) -> str:
        tid = str(thread_id)
        if tid in self.lobbies:
            del self.lobbies[tid]
            return "🛑 Truth & Dare game stopped! Send 'oli tdgame @user1 @user2' to start a new game anytime."
        return "❌ Koi active game nahi chal raha hai."
