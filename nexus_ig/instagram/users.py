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

def fetch_user_profile_instaloader(username: str) -> dict:
    """Fetch complete public profile details using instaloader."""
    try:
        clean_name = (username or "").strip().lstrip("@")
        if not clean_name:
            return None
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
        print(f"Instaloader profile lookup error for @{username}: {exc}")
        return None
