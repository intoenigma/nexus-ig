"""Reel Reaction Engine: Analyzes reel hashtags & captions and auto-reacts with contextual emojis."""

import json
import random
import re
from ..core import console


# 22 Deep Reaction Categories (Keywords & Emojis)
REACTION_CATEGORIES = [
    {
        "name": "love",
        "keywords": {
            "love", "romance", "couple", "crush", "cute", "heart", "mohabbat",
            "pyar", "pyaar", "ishq", "dil", "lovesong", "couplegoals", "romantic",
            "missyou", "hugs", "kisses", "sweet", "bae", "shona", "jaan", "meri",
            "forever", "soulmate", "shaadi", "wedding",
        },
        "emojis": ["❤️", "🥰", "💖", "💕", "😍"],
    },
    {
        "name": "funny",
        "keywords": {
            "funny", "comedy", "meme", "memes", "lol", "lmao", "roast", "joke",
            "jokes", "haso", "funnymemes", "chutkule", "laugh", "bakchodi", "dank",
            "sarcasm", "comedian", "standup", "relatable", "haha", "rofl", "ded",
            "lmfao", "hasna", "pagal", "clown",
        },
        "emojis": ["😂", "🤣", "💀", "😹", "🤡"],
    },
    {
        "name": "fire_attitude",
        "keywords": {
            "fire", "lit", "attitude", "swag", "savage", "gangster", "badass",
            "sigma", "chad", "op", "trending", "viral", "banger", "boss",
            "entry", "slowmo", "status", "reelsindia", "king", "queen", "mafia",
            "don", "alpha", "rule", "royal",
        },
        "emojis": ["🔥", "⚡", "😎", "💥", "💣"],
    },
    {
        "name": "sad_emotional",
        "keywords": {
            "sad", "broken", "emotional", "cry", "pain", "alone", "dard",
            "tanhai", "heartbreak", "heartbroken", "depressed", "hurt", "sadstatus",
            "shayari", "lonely", "tears", "goodbye", "dhokha", "cheat", "rona",
            "dukh", "peeda", "depression",
        },
        "emojis": ["🥺", "💔", "😢", "🥀", "😭"],
    },
    {
        "name": "anime",
        "keywords": {
            "anime", "manga", "naruto", "onepiece", "dbz", "goku", "otaku",
            "demonslayer", "jujutsukaisen", "gojo", "attackontitan", "weeb",
            "zenitsu", "luffy", "zoro", "sukuna", "kakashi", "itachi", "waifu",
            "senpai", "sasuke", "aot", "animation", "nostalgia",
        },
        "emojis": ["✨", "⚡", "🌸", "⚔️", "🎌"],
    },
    {
        "name": "music_dance",
        "keywords": {
            "music", "song", "dance", "party", "vibes", "dancer", "beats",
            "dj", "singing", "hiphop", "rap", "chill", "lofi", "remix",
            "bass", "concert", "tunes", "singer", "guitar", "bollywood", "hollywood",
        },
        "emojis": ["💃", "🕺", "🎶", "🎧", "🎵"],
    },
    {
        "name": "fitness_gym",
        "keywords": {
            "gym", "fitness", "workout", "bodybuilding", "motivation", "grind",
            "hustle", "fit", "muscle", "success", "chest", "biceps", "abs",
            "hardwork", "training", "calisthenics", "protein", "preworkout",
            "bulk", "cut", "aesthetics",
        },
        "emojis": ["💪", "🏋️", "🔥", "🏆", "😤"],
    },
    {
        "name": "gaming",
        "keywords": {
            "gaming", "gamer", "bgmi", "freefire", "pubg", "gta", "valorant",
            "minecraft", "cod", "playstation", "xbox", "headshot", "clutch",
            "esports", "pcgaming", "noob", "pro", "ping", "lag", "fps", "streamer",
        },
        "emojis": ["🎮", "👾", "🕹️", "🎯", "🖥️"],
    },
    {
        "name": "pets",
        "keywords": {
            "dog", "cat", "puppy", "kitten", "pets", "animal", "cuteanimals",
            "petlover", "doggo", "kitty", "birds", "wildlife", "meow", "bhow",
            "paws", "catsofinstagram", "dogsofinstagram",
        },
        "emojis": ["🐾", "🐶", "🐱", "🥺", "🦜"],
    },
    {
        "name": "food",
        "keywords": {
            "food", "foodie", "delicious", "yummy", "cooking", "streetfood",
            "recipe", "cake", "pizza", "burger", "biryani", "snack", "chai",
            "coffee", "tea", "momos", "maggi", "chocolate", "dessert", "bhookh", "hungry",
        },
        "emojis": ["😋", "🍕", "🤤", "🍔", "☕"],
    },
    {
        "name": "nature_wow",
        "keywords": {
            "wow", "amazing", "nature", "travel", "explore", "beauty",
            "scenery", "sunset", "aesthetic", "art", "mountain", "beach",
            "view", "wanderlust", "sky", "clouds", "beautiful", "gorgeous", "magic",
        },
        "emojis": ["🤩", "🤯", "✨", "🌈", "🌅"],
    },
    {
        "name": "study_motivation",
        "keywords": {
            "study", "exam", "upsc", "jee", "neet", "padhai", "books", "student",
            "college", "school", "topper", "fail", "pass", "syllabus", "assignment",
            "homework", "boardsexam", "result", "library", "notes",
        },
        "emojis": ["📚", "📖", "✍️", "🤓", "🧠"],
    },
    {
        "name": "sports",
        "keywords": {
            "cricket", "football", "virat", "dhoni", "ronaldo", "messi", "match",
            "ipl", "fifa", "goal", "sixer", "wicket", "sport", "tennis", "basketball",
            "kohli", "csk", "rcb", "worldcup", "champion",
        },
        "emojis": ["🏏", "⚽", "🏆", "🥇", "🔥"],
    },
    {
        "name": "tech_coding",
        "keywords": {
            "coding", "programmer", "developer", "hacker", "tech", "python", "bug",
            "error", "software", "ai", "hack", "pc", "laptop", "setup", "cyber",
            "code", "github", "linux", "windows", "apple",
        },
        "emojis": ["💻", "👨‍💻", "⚙️", "🚀", "🤖"],
    },
    {
        "name": "gossip_drama",
        "keywords": {
            "gossip", "tea", "lafda", "fight", "kalesh", "drama", "expose",
            "controversy", "biggboss", "snake", "fake", "toxic", "spill",
            "scandal", "rumor", "news", "viralvideo",
        },
        "emojis": ["☕", "🐍", "👀", "🍿", "🗣️"],
    },
    {
        "name": "money_wealth",
        "keywords": {
            "money", "rich", "paisa", "crypto", "bitcoin", "stock", "trading",
            "millionaire", "billionaire", "luxury", "ambani", "cash", "business",
            "entrepreneur", "investing", "wealth", "cars", "rolex",
        },
        "emojis": ["💸", "💰", "🤑", "📈", "💎"],
    },
    {
        "name": "angry_frustrated",
        "keywords": {
            "angry", "gussa", "irritated", "mad", "wtf", "annoy", "hate", "bhak",
            "irritating", "frustrated", "gali", "stfu", "shut", "bakwas", "bekar",
        },
        "emojis": ["😡", "🤬", "😤", "🤦‍♂️", "😠"],
    },
    {
        "name": "sleep_tired",
        "keywords": {
            "sleep", "neend", "tired", "thak", "exhaust", "boring", "yawn", "night",
            "gn", "goodnight", "lazy", "aalas", "bed", "dream", "sleeping",
        },
        "emojis": ["😴", "🥱", "💤", "🛌", "😪"],
    },
    {
        "name": "religious_devotional",
        "keywords": {
            "god", "allah", "ram", "shiva", "mahakal", "krishna", "bhagwan", "prayer",
            "temple", "masjid", "church", "blessing", "amen", "inshallah", "mahadev",
            "radheradhe", "ganesha", "bholenath", "faith", "peace",
        },
        "emojis": ["🙏", "🕉️", "🕌", "✝️", "✨"],
    },
    {
        "name": "festival_celebration",
        "keywords": {
            "happybirthday", "hbd", "party", "congrats", "congratulations", "cheers",
            "festival", "diwali", "eid", "christmas", "holi", "newyear", "celebrate",
            "gift", "cake", "treat",
        },
        "emojis": ["🎉", "🎊", "🎂", "🥂", "🎁"],
    },
    {
        "name": "travel_vacation",
        "keywords": {
            "travel", "trip", "goa", "flight", "airport", "vacation", "holiday",
            "hotel", "passport", "journey", "tour", "explore", "mountains", "trekking",
        },
        "emojis": ["✈️", "🏖️", "🧳", "🏝️", "🚂"],
    },
    {
        "name": "fashion_beauty",
        "keywords": {
            "makeup", "fashion", "outfit", "dress", "grwm", "beauty", "skincare",
            "handsome", "gorgeous", "model", "slay", "ootd", "style", "shopping",
            "sneakers", "shoes", "hair",
        },
        "emojis": ["👗", "💄", "💅", "✨", "👠"],
    },
]

# Fallback pool: guarantees a cool reaction for every single reel
DEFAULT_EMOJIS = ["🔥", "❤️", "✨", "💯", "👏", "🙌", "😍"]


def is_reel_message(msg) -> bool:
    """Detect if a DirectMessage represents an Instagram Reel, Clip, or shared video."""
    if not msg:
        return False

    item_type = getattr(msg, "item_type", "")
    if item_type in ("xma_clip", "clip", "reel_share", "felix_share"):
        return True

    if item_type == "media_share":
        return True

    if item_type == "generic_xma":
        raw = getattr(msg, "raw_xma", {}) or {}
        if isinstance(raw, dict) and ("xma_clip" in raw or "clip" in raw):
            return True
        xma = getattr(msg, "xma_share", None)
        if xma:
            url = str(getattr(xma, "video_url", "") or getattr(xma, "target_url", "") or "")
            if "instagram.com/reel" in url or "/reels/" in url or "/p/" in url:
                return True

    # Check text / link for reel URLs
    text = getattr(msg, "text", "") or ""
    if "instagram.com/reel" in text or "/reels/" in text or "instagram.com/p/" in text or "/share/" in text:
        return True

    link = getattr(msg, "link", None)
    if link:
        l_text = getattr(link, "text", "") or ""
        if "instagram.com/reel" in l_text or "/reels/" in l_text or "instagram.com/p/" in l_text:
            return True

    return False


def extract_reel_info(msg, cl=None) -> tuple[str, str | None]:
    """
    Extract (all_text_tokens, reel_url_or_id) from any format of Instagram reel/clip message:
    - xma_clip (modern Direct reel share)
    - clip (DirectMessage clip)
    - reel_share (legacy reel share)
    - media_share (feed video/reel shared to Direct)
    - generic_xma (cutout/media/story XMA)
    - text / link containing instagram.com/reel/ or /p/
    """
    parts: list[str] = []
    target_url: str | None = None
    media_igid: str | None = None

    # 1. Accompanying message text
    text_val = getattr(msg, "text", None)
    if text_val:
        parts.append(str(text_val))
        urls = re.findall(r"https?://(?:www\.)?instagram\.com/(?:reel|reels|p|share)/[A-Za-z0-9_-]+/?", str(text_val))
        if urls:
            target_url = urls[0]

    # 2. xma_share
    xma_share = getattr(msg, "xma_share", None)
    if xma_share:
        if isinstance(xma_share, dict):
            for k in ("title", "header_title_text", "caption_body_text", "subtitle_text"):
                val = xma_share.get(k)
                if val:
                    parts.append(str(val))
            target_url = target_url or xma_share.get("target_url") or xma_share.get("video_url")
        else:
            for k in ("title", "header_title_text", "caption_body_text", "subtitle_text"):
                val = getattr(xma_share, k, None)
                if val:
                    parts.append(str(val))
            target_url = target_url or getattr(xma_share, "target_url", None) or getattr(xma_share, "video_url", None)

    # 3. raw_xma / generic_xma
    raw_xma = getattr(msg, "raw_xma", None) or {}
    if isinstance(raw_xma, dict):
        for key in ("xma_clip", "generic_xma", "xma_media_share"):
            items = raw_xma.get(key) or []
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        for k in ("title_text", "header_title_text", "caption_body_text", "subtitle_text"):
                            val = item.get(k)
                            if val:
                                parts.append(str(val))
                        if not target_url:
                            target_url = item.get("target_url")
                        # Parse serialized_content_ref if present
                        s_ref = item.get("serialized_content_ref")
                        if s_ref and isinstance(s_ref, str):
                            try:
                                s_data = json.loads(s_ref)
                                if not target_url and s_data.get("target_url"):
                                    target_url = s_data["target_url"]
                                if not media_igid and s_data.get("fetch_params", {}).get("media_igid"):
                                    media_igid = str(s_data["fetch_params"]["media_igid"])
                                if s_data.get("username"):
                                    parts.append(s_data["username"])
                            except Exception:
                                pass

    # 4. clip
    clip_obj = getattr(msg, "clip", None)
    if clip_obj:
        for k in ("caption_text", "title"):
            val = getattr(clip_obj, k, None)
            if val:
                parts.append(str(val))
        media = getattr(clip_obj, "clip", None)
        if media:
            cap = getattr(media, "caption_text", None) or getattr(getattr(media, "caption", None), "text", None)
            if cap:
                parts.append(str(cap))

    # 5. reel_share
    reel_share = getattr(msg, "reel_share", None)
    if reel_share:
        if getattr(reel_share, "text", None):
            parts.append(str(reel_share.text))
        media = getattr(reel_share, "media", None)
        if media:
            cap = getattr(media, "caption_text", None) or getattr(getattr(media, "caption", None), "text", None)
            if cap:
                parts.append(str(cap))

    # 6. media_share
    media_share = getattr(msg, "media_share", None)
    if media_share:
        cap = getattr(media_share, "caption_text", None) or getattr(getattr(media_share, "caption", None), "text", None)
        if cap:
            parts.append(str(cap))
        title = getattr(media_share, "title", None)
        if title:
            parts.append(str(title))

    # 7. link
    link = getattr(msg, "link", None)
    if link:
        url_text = getattr(link, "text", "") or ""
        parts.append(url_text)
        if not target_url and ("instagram.com/reel" in url_text or "/reels/" in url_text or "/p/" in url_text):
            target_url = url_text

    # 8. Deep Reel Media Info Fetch via Instagram API
    if cl and (media_igid or target_url):
        try:
            mid = media_igid
            if not mid and target_url:
                mid = cl.media_pk_from_url(target_url)
            if mid:
                info = cl.media_info(mid)
                if info and getattr(info, "caption_text", None):
                    parts.append(str(info.caption_text))
        except Exception:
            pass

    return " ".join(parts).strip(), (target_url or media_igid)


def extract_reel_text(msg) -> str:
    """Backward-compatible helper returning extracted text without media lookup."""
    text, _ = extract_reel_info(msg, cl=None)
    return text


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
        reel_text, _ = extract_reel_info(msg, cl=cl)
        emoji = get_reel_reaction_emoji(reel_text)
        success = cl.direct_send_reaction(thread_id, msg.id, emoji)
        return emoji if success is not False else emoji
    except Exception as exc:
        console.warning(f"Reel reaction error: {exc}")
        # Guaranteed fallback like reaction
        try:
            cl.direct_send_reaction(thread_id, msg.id, "❤️")
            return "❤️"
        except Exception:
            return None
