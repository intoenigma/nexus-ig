"""Formatting utilities for Profile card display."""

def format_profile_card(data: dict) -> str:
    """Format clean, short profile overview card."""
    username = data.get("username", "Unknown")
    full_name = data.get("full_name") or username
    user_id = data.get("user_id", "N/A")
    biography = (data.get("biography") or "").strip()
    followers = data.get("followers", 0)
    following = data.get("following", 0)
    posts = data.get("posts", 0)
    is_private = "Yes" if data.get("is_private") else "No"
    is_verified = "Yes" if data.get("is_verified") else "No"
    pic_url = data.get("profile_pic_url", "")

    bio_str = f"📝 Bio: {biography}\n" if biography else ""
    pic_str = f"🖼️ Profile Pic:\n{pic_url}\n" if pic_url else ""

    return (
        "🔍 INSTAGRAM PROFILE DETAILS 🔍\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Name: {full_name} (@{username})\n"
        f"🆔 User ID: {user_id}\n"
        f"{bio_str}"
        f"👥 Followers: {followers:,} | Following: {following:,}\n"
        f"📸 Posts: {posts:,}\n"
        f"🔒 Private: {is_private} | ✅ Verified: {is_verified}\n"
        f"{pic_str}"
        "━━━━━━━━━━━━━━━━━━━━"
    )
