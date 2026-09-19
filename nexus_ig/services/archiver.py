"""archiver.py — Complete message archival for every instagrapi DirectMessage type.

Supported item_type values and what we capture:
  text          -> text content, reply context
  media         -> photo or video URL + dimensions + download
  animated_media-> sticker animated URL + static URL + download
  voice_media   -> audio URL + duration_ms + waveform + download
  clip          -> reel video URL + thumbnail
  reel_share    -> forwarded reel URL + caption
  media_share   -> shared post URL + caption
  story_share   -> shared story URL
  xma/xma_share -> link preview (URL, title, description, preview image)
  like          -> heart reaction sent as message
  action_log    -> system events (member joined/left, admin actions)
  placeholder   -> deleted message marker
  video_call_event -> call log event
  * anything else -> stored as 'unknown' with extra_json raw dump
"""

import json
import time
from pathlib import Path

from ..core import console


# Map instagrapi item_type strings to our canonical labels stored in DB
_ITEM_TYPE_MAP = {
    "text": "text",
    "media": "media",
    "animated_media": "sticker",
    "voice_media": "voice",
    "clip": "reel",
    "reel_share": "reel_share",
    "media_share": "media_share",
    "story_share": "story_share",
    "xma_share": "xma",
    "xma": "xma",
    "link": "link",
    "like": "like",
    "action_log": "action_log",
    "video_call_event": "video_call",
    "placeholder": "deleted",
}

# Extensions to infer from the CDN URL path before the query string
_URL_EXT_MAP = {
    ".mp4": ".mp4",
    ".jpg": ".jpg",
    ".jpeg": ".jpg",
    ".png": ".png",
    ".gif": ".gif",
    ".webp": ".webp",
    ".m4a": ".m4a",
    ".aac": ".aac",
}

# Fallback extension per canonical item type when URL gives no hint
_DEFAULT_EXT = {
    "media": ".jpg",
    "sticker": ".gif",
    "voice": ".m4a",
    "reel": ".mp4",
    "reel_share": ".mp4",
}


def _safe(obj, *attrs, default=None):
    """Safely walk a chain of attribute names, returning default on any failure."""
    for attr in attrs:
        try:
            obj = getattr(obj, attr, None)
            if obj is None:
                return default
        except Exception:
            return default
    return obj if obj is not None else default


def _best_url(versions_or_candidates) -> str | None:
    """Pick highest-quality URL from a list of image/video version objects."""
    if not versions_or_candidates:
        return None
    try:
        best = versions_or_candidates[0]
        return getattr(best, "url", None) or (best.get("url") if isinstance(best, dict) else None)
    except Exception:
        return None


def _ext_from_url(url: str) -> str | None:
    """Guess file extension from a CDN URL by inspecting the path part."""
    path = url.lower().split("?")[0]
    for suffix, ext in _URL_EXT_MAP.items():
        if path.endswith(suffix):
            return ext
    return None


class MessageArchiver:
    """Archives every message seen in a thread to the `messages` SQLite table.

    Call `sync_thread(thread)` on every poll.  The first time a thread is
    encountered, the archiver paginates all the way through its full history.
    On subsequent polls it only pages backward when new messages are found —
    this fills any gap caused by the bot being offline.
    """

    def __init__(self, cl, storage, config, bot_pk: str):
        self.cl = cl
        self.storage = storage
        self.config = config
        self._bot_pk = str(bot_pk)
        self._seen_ids = set()
        self._last_backfill = 0
        self._media_root = Path(config.media_dir)
        self._media_root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def sync_thread(self, thread):
        """Archive new messages instantly from current thread batch."""
        thread_id = str(thread.pk)
        thread_title = getattr(thread, "thread_title", "") or ""
        user_map = self._build_user_map(thread)

        new_in_batch = 0
        for msg in getattr(thread, "messages", []):
            msg_id = str(msg.id)
            if not self.storage.message_exists(msg_id):
                self._archive_one(msg, thread_id, thread_title, user_map)
                new_in_batch += 1

        # Periodic background backfill (runs once at startup or every 5 mins)
        now = time.time()
        first_time = not self.storage.get_state(thread_id, "archive_init_done")
        if first_time or (now - self._last_backfill > 300):
            self._last_backfill = now
            cursor = getattr(thread, "oldest_cursor", None)
            if cursor:
                filled = self._fill_history_gap(thread, thread_id, thread_title, user_map)
                if filled:
                    console.status("BACKFILL", f"+{filled} older msgs | {thread_title or thread_id}")
            self.storage.set_state(thread_id, "archive_init_done", "1")

        if new_in_batch:
            console.status("ARCHIVE", f"+{new_in_batch} new msgs | {thread_title or thread_id}")

    # ------------------------------------------------------------------
    # History pagination (gap-fill)
    # ------------------------------------------------------------------

    def _fill_history_gap(self, thread, thread_id, thread_title, user_map) -> int:
        """Walk backward through history until we hit an already-known message.

        Returns the count of newly archived messages.
        """
        filled = 0
        cursor = getattr(thread, "oldest_cursor", None)

        while cursor:
            try:
                older = self.cl.direct_thread(thread_id, amount=20, cursor=cursor)
            except Exception as exc:
                console.warning(f"History fetch stopped ({thread_id}): {exc}")
                break

            if not older.messages:
                break

            # Expand user_map with any members returned in this page
            user_map.update(self._build_user_map(older))

            all_known = True
            for msg in older.messages:
                if self.storage.message_exists(msg.id):
                    continue
                all_known = False
                self._archive_one(msg, thread_id, thread_title, user_map)
                filled += 1

            cursor = getattr(older, "oldest_cursor", None)
            if all_known:
                break  # Reached messages we already have — gap is fully closed

        return filled

    # ------------------------------------------------------------------
    # Single-message archival
    # ------------------------------------------------------------------

    def _archive_one(self, msg, thread_id: str, thread_title: str, user_map: dict):
        """Extract every available field from a DirectMessage and persist it."""
        try:
            msg_id = str(msg.id)
            user_id = str(msg.user_id)
            username, full_name = user_map.get(user_id, (None, None))

            sent_at = self._parse_timestamp(msg)
            raw_type = getattr(msg, "item_type", None) or "unknown"
            item_type = _ITEM_TYPE_MAP.get(raw_type, "unknown")

            data: dict = {
                "message_id": msg_id,
                "thread_id": thread_id,
                "thread_title": thread_title,
                "user_id": user_id,
                "username": username,
                "full_name": full_name,
                "is_bot_message": 1 if user_id == self._bot_pk else 0,
                "item_type": item_type,
                "text": self._extract_text(msg),
                "sent_at": sent_at,
            }

            data.update(self._extract_reply_context(msg))

            if item_type == "media":
                data.update(self._extract_media(msg))
            elif item_type == "sticker":
                data.update(self._extract_sticker(msg))
            elif item_type == "voice":
                data.update(self._extract_voice(msg))
            elif item_type in ("reel", "reel_share", "media_share", "story_share"):
                data.update(self._extract_share(msg, item_type))
            elif item_type in ("xma", "link"):
                data.update(self._extract_link(msg))

            # Download media to disk and write local_path back into data
            self._download_if_needed(msg_id, thread_id, item_type, sent_at, data)

            # Reactions
            reactions = self._extract_reactions(msg)
            data["reactions_json"] = json.dumps(reactions) if reactions else None

            # Forward-compat raw dump of misc instagrapi fields
            data["extra_json"] = self._build_extra_json(msg, raw_type)
            self.storage.archive_message(**data)
            self.storage.touch_member(thread_id, user_id, username, data.get("text"))

            # Persist reactions to the normalized message_reactions table
            for r in reactions:
                uid = r.get("user_id", "")
                if uid:
                    self.storage.upsert_reaction(
                        message_id=msg_id,
                        thread_id=thread_id,
                        user_id=uid,
                        emoji=r.get("emoji", "❤️"),
                        username=user_map.get(uid, (None, None))[0],
                        reacted_at=r.get("reacted_at"),
                    )

        except Exception as exc:
            console.warning(f"Archive failed for msg {getattr(msg, 'id', '?')}: {exc}")

    # ------------------------------------------------------------------
    # Field extractors — one method per content type
    # ------------------------------------------------------------------

    def _extract_text(self, msg) -> str | None:
        text = getattr(msg, "text", None)
        if not text:
            return None
        cleaned = str(text).strip()
        return cleaned or None

    def _extract_reply_context(self, msg) -> dict:
        """Extract comprehensive information about which message/user this message is replying to."""
        reply = (
            getattr(msg, "replied_to_message", None)
            or getattr(msg, "reply_to_message", None)
            or getattr(msg, "reply_to", None)
            or getattr(msg, "replied_message", None)
            or getattr(msg, "replied_to", None)
        )

        if not reply and isinstance(msg, dict):
            reply = (
                msg.get("replied_to_message")
                or msg.get("reply_to_message")
                or msg.get("reply_to")
                or msg.get("replied_message")
            )

        if not reply:
            return {}

        if isinstance(reply, dict):
            return {
                "replied_to_message_id": str(
                    reply.get("item_id") or reply.get("message_id") or reply.get("id") or ""
                ),
                "replied_to_user_id": str(reply.get("user_id") or (reply.get("user") or {}).get("pk") or ""),
                "replied_to_text": reply.get("text") or reply.get("caption") or None,
            }

        reply_user_id = str(
            getattr(reply, "user_id", None)
            or _safe(reply, "user", "pk")
            or ""
        )

        reply_text = (
            getattr(reply, "text", None)
            or getattr(reply, "caption", None)
        )

        reply_id = str(
            getattr(reply, "id", None)
            or getattr(reply, "item_id", None)
            or getattr(reply, "message_id", None)
            or ""
        )

        return {
            "replied_to_message_id": reply_id,
            "replied_to_user_id": reply_user_id,
            "replied_to_text": reply_text,
        }

    def _extract_media(self, msg) -> dict:
        """Photo or video (item_type='media')."""
        media = getattr(msg, "media", None)
        if not media:
            return {}

        media_type = getattr(media, "media_type", None)
        media_id = str(getattr(media, "id", "") or "")
        width = getattr(media, "original_width", None)
        height = getattr(media, "original_height", None)
        img_candidates = _safe(media, "image_versions2", "candidates") or []
        vid_versions = getattr(media, "video_versions", None) or []

        if media_type == 1:  # photo
            return {
                "media_id": media_id,
                "media_subtype": "photo",
                "media_url": _best_url(img_candidates),
                "media_width": width,
                "media_height": height,
            }
        if media_type == 2:  # video
            duration = getattr(media, "video_duration", None)
            return {
                "media_id": media_id,
                "media_subtype": "video",
                "media_url": _best_url(vid_versions),
                "media_thumbnail_url": _best_url(img_candidates),
                "media_width": width,
                "media_height": height,
                "media_duration_ms": int(duration * 1000) if duration else None,
            }
        # Unknown subtype — return whatever URLs we can find
        return {
            "media_id": media_id,
            "media_subtype": "unknown",
            "media_url": _best_url(img_candidates) or _best_url(vid_versions),
            "media_width": width,
            "media_height": height,
        }

    def _extract_sticker(self, msg) -> dict:
        """Animated sticker / GIF (item_type='animated_media')."""
        anim = getattr(msg, "animated_media", None)
        if not anim:
            return {}

        images = getattr(anim, "images", None)
        animated_url = None
        static_url = None

        if images:
            # Animated version — prefer largest
            for attr in ("original", "fixed_height", "downsized_large", "downsized", "fixed_width"):
                img = getattr(images, attr, None)
                if img and getattr(img, "url", None):
                    animated_url = img.url
                    break
            # Still/static version
            for attr in ("fixed_height_still", "downsized_still", "fixed_width_still", "original_still"):
                img = getattr(images, attr, None)
                if img and getattr(img, "url", None):
                    static_url = img.url
                    break

        return {
            "sticker_id": str(getattr(anim, "id", "") or ""),
            "sticker_url": animated_url,
            "sticker_static_url": static_url,
        }

    def _extract_voice(self, msg) -> dict:
        """Voice message (item_type='voice_media')."""
        voice = getattr(msg, "voice_media", None)
        if not voice:
            return {}

        media = getattr(voice, "media", None)
        audio = getattr(media, "audio", None) if media else None

        audio_url = getattr(audio, "audio_src", None) if audio else None
        duration_raw = getattr(audio, "duration", None) if audio else None

        waveform = getattr(voice, "waveform_data", None)
        waveform_json = json.dumps(list(waveform)) if waveform else None

        return {
            "voice_url": audio_url,
            "voice_duration_ms": int(duration_raw) if duration_raw is not None else None,
            "voice_waveform_json": waveform_json,
        }

    def _extract_share(self, msg, item_type: str) -> dict:
        """Shared reel, post, or story."""
        result: dict = {"share_type": item_type.replace("_share", "")}

        if item_type == "reel_share":
            share = getattr(msg, "reel_share", None)
            if share:
                result["share_caption"] = getattr(share, "text", None)
                media = getattr(share, "media", None)
                if media:
                    result["share_url"] = _best_url(getattr(media, "video_versions", None) or [])
                    result["share_thumbnail_url"] = _best_url(
                        _safe(media, "image_versions2", "candidates") or []
                    )

        elif item_type == "reel":  # clip
            clip_obj = getattr(msg, "clip", None)
            media = getattr(clip_obj, "clip", None) if clip_obj else None
            if media:
                result["share_url"] = _best_url(getattr(media, "video_versions", None) or [])
                result["share_thumbnail_url"] = _best_url(
                    _safe(media, "image_versions2", "candidates") or []
                )

        elif item_type == "media_share":
            media = getattr(msg, "media_share", None)
            if media:
                imgs = _safe(media, "image_versions2", "candidates") or []
                vids = getattr(media, "video_versions", None) or []
                result["share_url"] = _best_url(imgs) or _best_url(vids)
                caption = getattr(media, "caption_text", None) or _safe(media, "caption", "text")
                result["share_caption"] = caption

        elif item_type == "story_share":
            story_obj = getattr(msg, "story_share", None)
            media = getattr(story_obj, "media", None) if story_obj else None
            if media:
                result["share_url"] = _best_url(
                    _safe(media, "image_versions2", "candidates") or []
                )

        return result

    def _extract_link(self, msg) -> dict:
        """Link preview / XMA share."""
        xma = getattr(msg, "xma_share", None) or getattr(msg, "link", None)
        if not xma:
            return {}
        if isinstance(xma, dict):
            return {
                "link_url": xma.get("url") or xma.get("link_url"),
                "link_title": xma.get("title"),
                "link_description": xma.get("description") or xma.get("summary"),
                "link_image_url": xma.get("image_url"),
            }
        img = getattr(xma, "preview_image", None) or getattr(xma, "image", None)
        return {
            "link_url": getattr(xma, "url", None) or getattr(xma, "link_url", None),
            "link_title": getattr(xma, "title", None),
            "link_description": getattr(xma, "description", None)
            or getattr(xma, "summary", None),
            "link_image_url": getattr(img, "url", None) if img else None,
        }

    def _extract_reactions(self, msg) -> list[dict]:
        """Return list of {user_id, emoji, reacted_at} dicts."""
        raw = getattr(msg, "reactions", None)
        if not raw:
            return []

        results: list[dict] = []

        def _add(r):
            if isinstance(r, dict):
                results.append({
                    "user_id": str(r.get("user_id", "")),
                    "emoji": "❤️",
                    "reacted_at": r.get("timestamp"),
                })
            else:
                results.append({
                    "user_id": str(getattr(r, "user_id", "")),
                    "emoji": "❤️",
                    "reacted_at": getattr(r, "timestamp", None),
                })

        if isinstance(raw, dict):
            for r in raw.get("likes", []) or []:
                _add(r)
        else:
            for r in getattr(raw, "likes", []) or []:
                _add(r)

        return results

    # ------------------------------------------------------------------
    # Media download
    # ------------------------------------------------------------------

    def _download_if_needed(
        self,
        msg_id: str,
        thread_id: str,
        item_type: str,
        sent_at: int,
        data: dict,
    ):
        """Download media file for types that have a downloadable URL."""
        url_key_map = {
            "media": "media_url",
            "voice": "voice_url",
            "sticker": "sticker_url",
        }
        path_key_map = {
            "media": "media_local_path",
            "voice": "voice_local_path",
            "sticker": "sticker_local_path",
        }
        url_key = url_key_map.get(item_type)
        if not url_key:
            return

        url = data.get(url_key)
        if not url:
            return

        ext = _ext_from_url(url) or _DEFAULT_EXT.get(item_type, ".bin")
        date_str = time.strftime("%Y%m%d", time.localtime(sent_at))
        folder = self._media_root / thread_id / date_str
        folder.mkdir(parents=True, exist_ok=True)
        dest = folder / f"{msg_id}{ext}"

        if dest.exists():
            data[path_key_map[item_type]] = str(dest)
            return

        ok = self.cl.download_file(url, str(dest))
        if ok:
            console.success(f"Saved {item_type} → {dest.name}")
            data[path_key_map[item_type]] = str(dest)
        else:
            console.warning(f"Download failed: {msg_id} ({item_type})")

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _build_user_map(self, thread) -> dict[str, tuple[str | None, str | None]]:
        """Map user_id -> (username, full_name) from thread.users."""
        return {
            str(u.pk): (
                getattr(u, "username", None),
                getattr(u, "full_name", None),
            )
            for u in getattr(thread, "users", [])
        }

    def _parse_timestamp(self, msg) -> int:
        ts = getattr(msg, "timestamp", None)
        if ts is None:
            return int(time.time())
        if hasattr(ts, "timestamp"):
            return int(ts.timestamp())
        try:
            return int(ts)
        except (TypeError, ValueError):
            return int(time.time())

    def _build_extra_json(self, msg, raw_type: str) -> str | None:
        """Dump misc raw fields for forward-compatibility."""
        try:
            return json.dumps({
                "raw_item_type": raw_type,
                "hide_in_thread": getattr(msg, "hide_in_thread", None),
                "is_shh_mode": getattr(msg, "is_shh_mode", None),
                "action_log_desc": _safe(msg, "action_log", "description"),
            })
        except Exception:
            return None
