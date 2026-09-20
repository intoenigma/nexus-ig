"""Reel Reaction Engine: Analyzes reel hashtags & captions and auto-reacts with contextual emojis."""

import random
import re


# Category keyword & hashtag maps
REACTION_CATEGORIES = [
    {
        "name": "love",
        "keywords": {
            "love", "romance", "couple", "crush", "cute", "heart", "mohabbat",
            "pyar", "pyaar", "ishq", "dil", "lovesong", "couplegoals", "romantic",
            "missyou", "hugs", "kisses", "sweet", "bae", "shona", "jaan",
        },
        "emojis": ["❤️", "🥰", "💖", "💕", "😍"],
    },
    {
        "name": "funny",
        "keywords": {
            "funny", "comedy", "meme", "memes", "lol", "lmao", "roast", "joke",
            "jokes", "haso", "funnymemes", "chutkule", "laugh", "bakchodi", "dank",
            "sarcasm", "comedian", "standup", "relatable",
        },
        "emojis": ["😂", "🤣", "💀", "😹"],
    },
    {
        "name": "fire_attitude",
        "keywords": {
            "fire", "lit", "attitude", "swag", "savage", "gangster", "badass",
            "sigma", "chad", "op", "trending", "viral", "banger", "boss",
            "entry", "slowmo", "status", "reelsindia", "king", "queen",
        },
        "emojis": ["🔥", "⚡", "😎", "💥", "💣"],
    },
    {
        "name": "sad_emotional",
        "keywords": {
            "sad", "broken", "emotional", "cry", "pain", "alone", "dard",
            "tanhai", "heartbreak", "heartbroken", "depressed", "hurt", "sadstatus", "shayari",
            "lonely", "tears", "goodbye",
        },
        "emojis": ["🥺", "💔", "😢", "🥀"],
    },
    {
        "name": "anime",
        "keywords": {
            "anime", "manga", "naruto", "onepiece", "dbz", "goku", "otaku",
            "demonslayer", "jujutsukaisen", "gojo", "attackontitan", "weeb",
            "zenitsu", "luffy", "zoro", "sukuna", "kakashi", "itachi",
        },
        "emojis": ["✨", "⚡", "🌸", "⚔️", "🔥"],
    },
    {
        "name": "music_dance",
        "keywords": {
            "music", "song", "dance", "party", "vibes", "dancer", "beats",
            "dj", "singing", "hiphop", "rap", "chill", "lofi", "remix",
            "bass", "concert", "tunes",
        },
        "emojis": ["💃", "🕺", "🎶", "🎧", "🎵"],
    },
    {
        "name": "fitness_gym",
        "keywords": {
            "gym", "fitness", "workout", "bodybuilding", "motivation", "grind",
            "hustle", "fit", "muscle", "success", "chest", "biceps", "abs",
            "hardwork", "training", "calisthenics",
        },
        "emojis": ["💪", "🏋️", "🔥", "🏆"],
    },
    {
        "name": "gaming",
        "keywords": {
            "gaming", "gamer", "bgmi", "freefire", "pubg", "gta", "valorant",
            "minecraft", "cod", "playstation", "xbox", "headshot", "clutch",
            "esports", "pcgaming",
        },
        "emojis": ["🎮", "👾", "🕹️", "🎯"],
    },
    {
        "name": "pets",
        "keywords": {
            "dog", "cat", "puppy", "kitten", "pets", "animal", "cuteanimals",
            "petlover", "doggo", "kitty", "birds", "wildlife",
        },
        "emojis": ["🐾", "🐶", "🐱", "🥺"],
    },
    {
        "name": "food",
        "keywords": {
            "food", "foodie", "delicious", "yummy", "cooking", "streetfood",
            "recipe", "cake", "pizza", "burger", "biryani", "snack",
        },
        "emojis": ["😋", "🍕", "🤤", "🍔"],
    },
    {
        "name": "nature_wow",
        "keywords": {
            "wow", "amazing", "nature", "travel", "explore", "beauty",
            "scenery", "sunset", "aesthetic", "art", "mountain", "beach",
            "view", "wanderlust",
        },
        "emojis": ["🤩", "🤯", "✨", "🌈", "👏"],
    },
]

# Fallback pool: guarantees a cool reaction for every single reel
DEFAULT_EMOJIS = ["🔥", "❤️", "✨", "💯", "👏", "🙌", "😍"]


def extract_reel_text(msg) -> str:
    """Extract all caption, hashtags, and title text from an instagrapi reel/share message."""
    parts = []

    # Accompanying message text
    if getattr(msg, "text", None):
        parts.append(str(msg.text))

    # reel_share
    reel_share = getattr(msg, "reel_share", None)
    if reel_share:
        if getattr(reel_share, "text", None):
            parts.append(str(reel_share.text))
        media = getattr(reel_share, "media", None)
        if media:
            cap = getattr(media, "caption_text", None) or getattr(getattr(media, "caption", None), "text", None)
            if cap:
                parts.append(str(cap))

    # clip
    clip_obj = getattr(msg, "clip", None)
    if clip_obj:
        cap = getattr(clip_obj, "caption_text", None) or getattr(clip_obj, "title", None)
        if cap:
            parts.append(str(cap))
        media = getattr(clip_obj, "clip", None)
        if media:
            cap = getattr(media, "caption_text", None) or getattr(getattr(media, "caption", None), "text", None)
            if cap:
                parts.append(str(cap))

    # media_share
    media_share = getattr(msg, "media_share", None)
    if media_share:
        cap = getattr(media_share, "caption_text", None) or getattr(getattr(media_share, "caption", None), "text", None)
        if cap:
            parts.append(str(cap))

    # xma_share (if reel link was shared)
    xma = getattr(msg, "xma_share", None) or getattr(msg, "link", None)
    if xma:
        title = getattr(xma, "title", "") if not isinstance(xma, dict) else xma.get("title", "")
        desc = getattr(xma, "description", "") if not isinstance(xma, dict) else xma.get("description", "")
        if title:
            parts.append(str(title))
        if desc:
            parts.append(str(desc))

    return " ".join(parts).strip()


def get_reel_reaction_emoji(text: str) -> str:
    """Select the best matching emoji based on reel hashtags and keywords."""
    if not text:
        return random.choice(DEFAULT_EMOJIS)

    lower_text = text.lower()
    # Extract all words and hashtags as clean tokens
    tokens = set(re.findall(r"\b\w+\b", lower_text))

    for category in REACTION_CATEGORIES:
        # Check if any keyword/hashtag matches against the token set
        if any(kw in tokens for kw in category["keywords"]):
            return random.choice(category["emojis"])

    # Fallback guaranteed reaction
    return random.choice(DEFAULT_EMOJIS)


def handle_reel_reaction(cl, thread_id: str, msg) -> str | None:
    """Detect reel, choose hashtag-based emoji, and react via Instagram Direct."""
    try:
        reel_text = extract_reel_text(msg)
        emoji = get_reel_reaction_emoji(reel_text)
        success = cl.direct_send_reaction(thread_id, msg.id, emoji)
        return emoji if success is not False else emoji
    except Exception:
        # Fallback like reaction
        try:
            cl.direct_send_reaction(thread_id, msg.id, "❤️")
            return "❤️"
        except Exception:
            return None
