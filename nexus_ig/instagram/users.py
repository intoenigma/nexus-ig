"""Instagram User resolution helpers."""

def clean_username(username: str) -> str:
    return (username or "").strip().lstrip("@")

def find_sender_name(thread, user_id) -> str:
    for user in getattr(thread, "users", []):
        if str(user.pk) == str(user_id):
            return user.username
    return "User"

def extract_usernames(text: str) -> list[str]:
    return [clean_username(part) for part in text.replace(",", " ").split() if part.strip()]

def resolve_user_ids(cl, usernames: list[str]):
    user_ids = []
    missing = []
    for username in usernames:
        if not username:
            continue
        try:
            user_ids.append(int(cl.user_id_from_username(username)))
        except Exception:
            missing.append(username)
    return user_ids, missing


import instaloader
import requests
from ..app import console


def fetch_user_profile(username: str, cl=None, thread=None) -> dict:
    """Fetch complete public profile details using instagrapi session, thread cache, Instagram web API, or instaloader fallback."""
    clean_name = (username or "").strip().lstrip("@")
    if not clean_name:
        return None

    # Layer 1: Authenticated instagrapi client (Primary)
    if cl is not None:
        try:
            info = cl.user_info_by_username(clean_name)
            if info:
                return {
                    "user_id": str(getattr(info, "pk", "") or getattr(info, "id", "")),
                    "username": getattr(info, "username", clean_name),
                    "full_name": getattr(info, "full_name", "") or "N/A",
                    "bio": getattr(info, "biography", "") or "No bio set",
                    "followers_count": getattr(info, "follower_count", 0),
                    "following_count": getattr(info, "following_count", 0),
                    "posts_count": getattr(info, "media_count", 0),
                    "is_private": getattr(info, "is_private", False),
                    "is_verified": getattr(info, "is_verified", False),
                    "profile_pic_url": str(getattr(info, "profile_pic_url", "") or ""),
                }
        except Exception as exc:
            console.warning(f"cl.user_info_by_username failed for @{clean_name}: {exc}")

        # Try user_id lookup fallback via instagrapi
        try:
            user_id = cl.user_id_from_username(clean_name)
            if user_id:
                info = cl.user_info(user_id)
                if info:
                    return {
                        "user_id": str(getattr(info, "pk", user_id)),
                        "username": getattr(info, "username", clean_name),
                        "full_name": getattr(info, "full_name", "") or "N/A",
                        "bio": getattr(info, "biography", "") or "No bio set",
                        "followers_count": getattr(info, "follower_count", 0),
                        "following_count": getattr(info, "following_count", 0),
                        "posts_count": getattr(info, "media_count", 0),
                        "is_private": getattr(info, "is_private", False),
                        "is_verified": getattr(info, "is_verified", False),
                        "profile_pic_url": str(getattr(info, "profile_pic_url", "") or ""),
                    }
        except Exception:
            pass

    # Layer 2: Group Thread Member Match (Local Thread Data)
    if thread is not None:
        for u in getattr(thread, "users", []):
            if getattr(u, "username", "").lower() == clean_name.lower():
                return {
                    "user_id": str(getattr(u, "pk", "")),
                    "username": getattr(u, "username", clean_name),
                    "full_name": getattr(u, "full_name", "") or "N/A",
                    "bio": getattr(u, "biography", "") or "Group Thread Member",
                    "followers_count": getattr(u, "follower_count", 0),
                    "following_count": getattr(u, "following_count", 0),
                    "posts_count": getattr(u, "media_count", 0),
                    "is_private": getattr(u, "is_private", False),
                    "is_verified": getattr(u, "is_verified", False),
                    "profile_pic_url": str(getattr(u, "profile_pic_url", "") or ""),
                }

    # Layer 3: Instagram Web Profile API Endpoint
    try:
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={clean_name}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "X-IG-App-ID": "936619743392459",
        }
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json().get("data", {}).get("user", {})
            if data:
                return {
                    "user_id": str(data.get("id", "")),
                    "username": data.get("username", clean_name),
                    "full_name": data.get("full_name", "") or "N/A",
                    "bio": data.get("biography", "") or "No bio set",
                    "followers_count": data.get("edge_followed_by", {}).get("count", 0),
                    "following_count": data.get("edge_follow", {}).get("count", 0),
                    "posts_count": data.get("edge_owner_to_timeline_media", {}).get("count", 0),
                    "is_private": data.get("is_private", False),
                    "is_verified": data.get("is_verified", False),
                    "profile_pic_url": str(data.get("profile_pic_url_hd", "") or data.get("profile_pic_url", "")),
                }
    except Exception:
        pass

    # Layer 4: Instaloader Fallback
    try:
        L = instaloader.Instaloader(max_connection_attempts=1)
        profile = instaloader.Profile.from_username(L.context, clean_name)
        return {
            "user_id": str(profile.userid),
            "username": profile.username,
            "full_name": profile.full_name or "N/A",
            "bio": profile.biography or "No bio set",
            "followers_count": profile.followers,
            "following_count": profile.followees,
            "posts_count": profile.mediacount,
            "is_private": profile.is_private,
            "is_verified": profile.is_verified,
            "profile_pic_url": str(profile.profile_pic_url or ""),
        }
    except Exception as exc:
        console.warning(f"Profile lookup error for @{clean_name}: {exc}")
        return None


fetch_user_profile_instaloader = fetch_user_profile


