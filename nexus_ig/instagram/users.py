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


def fetch_user_profile(username: str, cl=None) -> dict:
    """Fetch complete public profile details using instagrapi session or instaloader fallback."""
    clean_name = (username or "").strip().lstrip("@")
    if not clean_name:
        return None

    # Try authenticated instagrapi client first if available
    if cl is not None:
        try:
            info = cl.user_info_by_username(clean_name)
            if info:
                return {
                    "user_id": str(getattr(info, "pk", "")),
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

    # Fallback to Instaloader
    try:
        L = instaloader.Instaloader()
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
        print(f"Profile lookup error for @{username}: {exc}")
        return None


fetch_user_profile_instaloader = fetch_user_profile

