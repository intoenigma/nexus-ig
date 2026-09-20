from instagrapi import Client
import requests
import time
from ..core import console

class InstagramProvider:
    """Enhanced adapter around instagrapi Client with device header hardening and request pacing."""

    def __init__(self, config=None):
        self.client = Client()
        self._configure_device_settings()
        self.apply_config(config)

    def _configure_device_settings(self):
        """Configure authentic Android device signatures to prevent 403 blocks."""
        try:
            self.client.set_country("US")
            self.client.set_locale("en_US")
            self.client.set_timezone_offset(-5 * 3600)
        except Exception:
            pass

    def __getattr__(self, name):
        """Delegate missing methods directly to underlying instagrapi Client."""
        return getattr(self.client, name)

    def apply_config(self, config):
        if not config:
            self.client.delay_range = [0, 0]
            return
        self.client.delay_range = [
            max(0, config.instagram_delay_min),
            max(0, config.instagram_delay_max),
        ]

    @property
    def sessionid(self):
        return self.client.sessionid

    def load_settings(self, session_file):
        return self.client.load_settings(session_file)

    def dump_settings(self, session_file):
        return self.client.dump_settings(session_file)

    def login(self, username, password):
        return self.client.login(username, password)

    def login_by_sessionid(self, sessionid):
        return self.client.login_by_sessionid(sessionid)

    def account_info(self):
        return self.client.account_info()

    def direct_threads(self, amount):
        return self.client.direct_threads(amount=amount)

    def direct_thread(self, thread_id, amount=20, cursor=None):
        """Fetch a DirectThread with its message history."""
        kwargs = {"thread_id": int(thread_id), "amount": amount}
        if cursor:
            kwargs["cursor"] = cursor
        return self.client.direct_thread(**kwargs)

    def direct_send(self, text, thread_ids):
        if isinstance(thread_ids, (str, int)):
            thread_ids = [thread_ids]

        now = time.time()
        if hasattr(self, "_last_send_time"):
            elapsed = now - self._last_send_time
            if elapsed < 0.2:
                time.sleep(0.2 - elapsed)
        self._last_send_time = time.time()

        last_exc = None
        for tid in thread_ids:
            try:
                return self.client.direct_answer(int(tid), text)
            except Exception as exc:
                err_msg = str(exc).lower()
                if "pleasewaitfewminutes" in err_msg or "wait" in err_msg or "something went wrong" in err_msg:
                    console.warning("Instagram DM rate limit hit (PleaseWaitFewMinutes). Pausing 5 seconds...")
                    time.sleep(5)
                    try:
                        return self.client.direct_answer(int(tid), text)
                    except Exception as inner_exc:
                        last_exc = inner_exc
                else:
                    last_exc = exc

            # Secondary fallback using direct_send
            try:
                return self.client.direct_send(text, thread_ids=[int(tid)])
            except Exception as exc:
                last_exc = exc

        if last_exc:
            raise last_exc

    def direct_send_photo(self, path, thread_ids):
        try:
            from ..instagram.media import prepare_dm_image
            formatted_path = prepare_dm_image(path)
            return self.client.direct_send_photo(formatted_path, thread_ids=thread_ids)
        except Exception as exc:
            print(f"Direct photo send error: {exc}")
            return None

    def user_id_from_username(self, username):
        return self.client.user_id_from_username(username)

    def direct_thread_create(self, user_ids, title):
        return self.client.direct_thread_create(user_ids=user_ids, title=title)

    def direct_thread_add_users(self, thread_id, user_ids):
        return self.client.direct_thread_add_users(thread_id=thread_id, user_ids=user_ids)

    def direct_thread_update_title(self, thread_id, title):
        return self.client.direct_thread_update_title(thread_id=thread_id, title=title)

    def try_delete_message(self, thread_id, message_id):
        for method_name in ("direct_message_delete", "direct_thread_message_delete"):
            method = getattr(self.client, method_name, None)
            if not method:
                continue
            try:
                method(thread_id, message_id)
                return True
            except Exception:
                pass
        return False

    def download_file(self, url: str, dest_path: str) -> bool:
        """Stream-download url to dest_path."""
        try:
            session = getattr(self.client, "private", None) or getattr(self.client, "session", None) or requests
            resp = session.get(
                url,
                stream=True,
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            resp.raise_for_status()
            with open(dest_path, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=65_536):
                    fh.write(chunk)
            return True
        except Exception:
            try:
                resp = requests.get(
                    url,
                    stream=True,
                    timeout=30,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                resp.raise_for_status()
                with open(dest_path, "wb") as fh:
                    for chunk in resp.iter_content(chunk_size=65_536):
                        fh.write(chunk)
                return True
            except Exception:
                return False


    def direct_send_reaction(
        self,
        thread_id: str,
        message_id: str,
        emoji: str = "❤️",
        client_context: str | None = None,
        target_item_type: str | None = None,
    ) -> bool:
        """Send emoji reaction to a specific direct message."""
        try:
            if hasattr(self.client, "direct_send_reaction"):
                # 1. Try with int(thread_id)
                try:
                    res = self.client.direct_send_reaction(
                        int(thread_id),
                        str(message_id),
                        emoji=emoji,
                        client_context=client_context,
                        target_item_type=target_item_type,
                    )
                    if res:
                        return True
                except Exception:
                    pass

                # 2. Try with str(thread_id)
                try:
                    res = self.client.direct_send_reaction(
                        str(thread_id),
                        str(message_id),
                        emoji=emoji,
                        client_context=client_context,
                        target_item_type=target_item_type,
                    )
                    if res:
                        return True
                except Exception:
                    pass
            elif hasattr(self.client, "direct_message_react"):
                return bool(self.client.direct_message_react(thread_id, message_id, emoji))
        except Exception as exc:
            console.warning(f"Reaction error: {exc}")
        return False


    def direct_send_sticker(self, sticker_id: str, thread_ids: list[str]):
        """Send a sticker by sticker ID into direct threads."""
        try:
            if hasattr(self.client, "direct_send_sticker"):
                return self.client.direct_send_sticker(sticker_id, thread_ids=thread_ids)
        except Exception as exc:
            print(f"Sticker send error: {exc}")
        return None
