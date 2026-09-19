"""Permission verifiers."""

def is_owner(user_id: str, owner_username: str, thread=None) -> bool:
    return str(user_id) == str(owner_username)

def is_admin(user_id: str, admin_usernames: set, owner_username: str, thread=None) -> bool:
    uid_str = str(user_id).lower()
    if owner_username and uid_str == str(owner_username).lower():
        return True
    if admin_usernames and uid_str in {str(u).lower() for u in admin_usernames}:
        return True
    if thread:
        sender_name = ""
        for u in getattr(thread, "users", []):
            if str(u.pk) == str(user_id):
                sender_name = (u.username or "").lower()
                break
        if sender_name and sender_name in {str(u).lower() for u in admin_usernames}:
            return True
        if sender_name and owner_username and sender_name == str(owner_username).lower():
            return True
    return False
