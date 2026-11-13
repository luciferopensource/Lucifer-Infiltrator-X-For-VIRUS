# -*- coding: utf-8 -*-
import os
import html
import math
import random
import psutil
import time
import asyncio
import logging
logger = logging.getLogger('RestrictBot')
import traceback
# === Python 3.10-3.14+ Event Loop Compatibility ===
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

import re
import shutil
import subprocess
import gc
import datetime
import uuid
import base64
import hashlib
import urllib.parse
import unicodedata
from pathlib import Path
from collections import defaultdict
import motor.motor_asyncio
from pyrogram import Client, filters, enums, idle, raw
from pyrogram.errors import (
    FloodWait, UserIsBlocked, InputUserDeactivated, UserAlreadyParticipant,
    InviteHashExpired, UsernameNotOccupied, FileReferenceExpired, UserNotParticipant,
    ApiIdInvalid, PhoneNumberInvalid, PhoneNumberBanned, PhoneNumberUnoccupied, PhoneCodeInvalid, PhoneCodeExpired,
    SessionPasswordNeeded, PasswordHashInvalid, PeerIdInvalid, AuthKeyUnregistered, UserDeactivated
)

from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, Message, 
    BotCommand, BotCommandScopeDefault, BotCommandScopeChat, CallbackQuery,
    InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio
)
from concurrent.futures import ThreadPoolExecutor
import sys

# --- LOGGER SETUP ---
class LoggerWriter:
    MAX_LOG_BYTES = 10 * 1024 * 1024

    def __init__(self, is_stderr=False):
        self.terminal = sys.stderr if is_stderr else sys.stdout
        self.log = open("bot.log", "a", encoding="utf-8")
        self.is_stderr = is_stderr
        self._writes = 0

    def _rotate_if_needed(self):
        """Keep bot.log bounded (Windows-safe: copy then truncate in place)."""
        try:
            if self.is_stderr or os.path.getsize("bot.log") <= self.MAX_LOG_BYTES:
                return
            shutil.copyfile("bot.log", "bot.log.1")
            self.log.seek(0)
            self.log.truncate(0)
        except Exception:
            pass

    def write(self, message):
        self._writes += 1
        if self._writes % 500 == 0:
            self._rotate_if_needed()
        try:
            self.terminal.write(message)
        except Exception:
            try:
                enc = getattr(self.terminal, 'encoding', 'utf-8') or 'utf-8'
                self.terminal.write(message.encode(enc, errors='replace').decode(enc))
            except Exception:
                pass
        try:
            self.log.write(message)
            self.log.flush()
        except Exception:
            pass
    def flush(self):
        try:
            self.terminal.flush()
        except Exception:
            pass
        try:
            self.log.flush()
        except Exception:
            pass

# Redirect all prints and tracebacks to bot.log as well as the console
sys.stdout = LoggerWriter(is_stderr=False)
sys.stderr = LoggerWriter(is_stderr=True)


# ==============================================================================
# --- CONFIGURATION ---
# ==============================================================================

API_ID = int(os.environ.get("API_ID", "") or 0)
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
DB_URI = os.environ.get("DB_URI", "")
DB_NAME = os.environ.get("DB_NAME", "")
STRING_SESSION = os.environ.get("STRING_SESSION", None)
SESSION_ENC_KEY = os.environ.get("SESSION_ENC_KEY", "").strip()
SESSION_ENC_KEY_FALLBACK = False
if not SESSION_ENC_KEY and BOT_TOKEN:
    # Encrypt at rest even when no dedicated key is supplied; rotating BOT_TOKEN invalidates old sessions.
    SESSION_ENC_KEY = BOT_TOKEN
    SESSION_ENC_KEY_FALLBACK = True

# Error Log Channel (Optional)
LOG_CHANNEL = os.environ.get("LOG_CHANNEL", "") 

# ⏱ STATUS UPDATE TIME (Seconds) -> 10 Seconds par set hai
STATUS_UPDATE_INTERVAL = int(os.environ.get("STATUS_UPDATE_INTERVAL", 15))

# Queue System
TASK_QUEUE = defaultdict(list) 

# Create a thread pool for blocking tasks
io_executor = ThreadPoolExecutor(max_workers=4)

LOGIN_SYSTEM = os.environ.get("LOGIN_SYSTEM", "True").lower() == "true"
ALLOW_OPEN_ACCESS = os.environ.get("ALLOW_OPEN_ACCESS", "false").lower() == "true"
ERROR_MESSAGE = os.environ.get("ERROR_MESSAGE", "True").lower() == "true"
WAITING_TIME = int(os.environ.get("WAITING_TIME", 3))

# --- AUTHORIZATION & ADMIN CONFIGURATION ---
def _parse_env_ids(*keys):
    found = []
    for k in keys:
        for lookup in (k, k.lower(), k.upper()):
            raw = os.environ.get(lookup, "").strip()
            if raw:
                found.extend([int(x) for x in re.split(r'[,;\s]+', raw) if x.strip().isdigit()])
    return list(dict.fromkeys(found))

owner_str = os.environ.get("OWNER_ID", "").strip() or os.environ.get("OWNER", "").strip() or os.environ.get("owner_id", "").strip() or os.environ.get("owner", "").strip()
OWNER_ID = int(owner_str) if owner_str.isdigit() else 0

ADMINS = _parse_env_ids("ADMINS", "ADMIN", "ADMIN_ID", "ADMIN_IDS")
SUDOS = _parse_env_ids("SUDOS", "SUDO", "SUDO_USERS", "SUDO_USER")
AUTH_USERS_EXTRA = _parse_env_ids("AUTH_USERS", "AUTH_USER", "AUTH_USERS_IDS", "AUTHORIZED_USERS")

if OWNER_ID and OWNER_ID not in ADMINS:
    ADMINS.append(OWNER_ID)

# Super-administrators with unrestricted privileges (Owner, Admins, Sudos)
SUPER_ADMINS = set(ADMINS + SUDOS)
if OWNER_ID:
    SUPER_ADMINS.add(OWNER_ID)

# Master set of all authorized users allowed to interact with the bot (Admins + Sudos + Authorized Clients)
AUTH_USERS = set(ADMINS + SUDOS + AUTH_USERS_EXTRA)
if OWNER_ID:
    AUTH_USERS.add(OWNER_ID)

UNAUTH_NOTIFY_CACHE = {}  # user_id -> timestamp (throttle access denial notices)

def is_admin(user_id: int) -> bool:
    if not user_id:
        return False
    if not SUPER_ADMINS and not AUTH_USERS:
        return ALLOW_OPEN_ACCESS
    return user_id in SUPER_ADMINS

def is_authorized(user_id: int) -> bool:
    if not user_id:
        return False
    if not AUTH_USERS:
        # Open access is opt-in only; set OWNER_ID/ADMINS or ALLOW_OPEN_ACCESS=true
        return ALLOW_OPEN_ACCESS
    return user_id in AUTH_USERS

HELP_TXT = """<b>📚 𝕃𝕌ℂ𝕀𝔽𝔼ℝ 𝕄𝕆ℝℕ𝕀ℕ𝔾𝕊𝕋𝔸ℝ — MASTER OPERATOR MANUAL</b>

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
<blockquote expandable>
<b>⚡ 1. SINGLE & BATCH DOWNLOADS (/dl)</b>
• <b>Single Post:</b> Send any public or restricted message link.
• <b>Batch Range:</b> Send <code>From - To</code> links to transfer multiple posts.
• <b>Channel Scraping:</b> Send <code>From - all</code> to scrape all posts to the end.
• <b>Examples:</b>
  ├ <code>https://t.me/c/1234567890/101</code>
  ├ <code>https://t.me/c/1234567890/101 - 250</code>
  └ <code>https://t.me/c/1234567890/1 - all</code>
• <b>Restricted Bot Links:</b> <code>https://t.me/b/botusername/1234</code>
• <b>Reply Mode:</b> Reply to any forwarded message or link with <code>/dl</code>.

<b>💾 2. SAVED CHANNEL MEMORY (SOURCES & DESTINATIONS)</b>
• Store your channels permanently — no more manual channel ID lookups:
  ├ <code>/addsourcechannel [Link/ID]</code> (or <code>/addsource</code>) - Auto-resolves title & saves source.
  ├ <code>/adddestinationchannel [Link/ID]</code> (or <code>/adddest</code>) - Tests write access & saves destination.
  ├ <code>/viewsourcechannels</code> (or <code>/viewsources</code>) - 10-per-page browser with 1-click Watch & delete.
  ├ <code>/viewdestinationchannels</code> (or <code>/viewdest</code>) - 10-per-page browser with channel management.
  └ <b>WATCHERS Migration:</b> Use <code>/watchers</code> to auto-import all active watcher channels into saved memory!

<b>👀 3. 24/7 LIVE WATCHERS & SURVEILLANCE (/watch)</b>
• Real-time channel watcher that auto-routes new messages instantaneously.
• <b>1-Click Quick Setup:</b> Send <code>/watch</code> alone to pick from saved source channels!
• <b>Direct Setup:</b> <code>/watch https://t.me/channel/123</code>
• <b>Forum Topics:</b> Full support for source and destination topic IDs.
• <b>Multi-Routing:</b> Route 1 source to multiple destinations simultaneously.
• <b>Content Filtering:</b> Select Video, Document, Photo, Audio, Voice, Text, Animation, or Sticker.
• <b>Typography Engine:</b> Format captions with <b>Mono</b>, <b>Bold</b>, <b>Italic</b>, or combinations (e.g. Bold+Italic, Mono+Bold), plus Original or Cleaned captions!
• <b>Active Codex:</b> <code>/watchers</code> (or <code>/list</code>) - View, manage, or import active surveillance routes.
• <b>Watcher Removal:</b> <code>/removetarget &lt;src&gt; &lt;dst&gt;</code> or <code>/removesource &lt;src&gt;</code> (or <code>/unwatch</code>).

<b>🏷️ 4. CUSTOM RE-BRANDING & THUMBNAILS</b>
• <code>/replace [old] -> [new]</code> - Auto-replace watermarks, links & names in captions.
• <code>/replace</code> - View and manage your active text replacement rules.
• <code>/clearreplace</code> - Delete all caption replacement rules.
• <code>/setthumb</code> - Reply to any photo to set a custom channel thumbnail.
• <code>/viewthumb</code> - Preview your currently active custom thumbnail.
• <code>/delthumb</code> - Remove custom thumbnail and revert to default.

<b>📊 5. ANALYTICS & HEALTH DASHBOARD</b>
• <code>/channelstats</code> (or <code>/stats</code>) - View live deliveries, bandwidth saved, CPU & RAM load.
• <code>/mywatchers</code> - Quick shortcut to active surveillance routes.

<b>🎛 4. TASK & ENGINE DASHBOARD</b>
• <code>/tasks</code> (or <code>/progress</code>) - Refresh real-time interactive progress message cards.
• <code>/cancel</code> - Interactive termination menu for specific or all tasks.
• <code>/toggledl</code> - Toggle Direct-Only vs Fallback Download/Upload mode.
• <code>/pixel &lt;URL&gt;</code> - Generate direct high-speed CDN URLs for Pixeldrain links.
• <code>/login</code> - Generate userbot session for private restricted channels.
• <code>/logout</code> - Terminate userbot session and purge stored credentials.
• <code>/setcommands</code> - Synchronize and update Telegram menu command suggestions.

<b>👑 5. ADMINISTRATIVE CODEX (Admins & Sudos)</b>
• <code>/status</code> - System hardware telemetry (CPU, RAM, Disk, Uptime, Queue).
• <code>/botstats</code> - Detailed analytics of registered users, sessions, and database.
• <code>/log</code> - Transmit the active application log file (<code>bot.log</code>).
• <code>/broadcast</code> - Broadcast message to all registered bot users.
</blockquote>
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""

# ==============================================================================
# --- DATABASE ---
# ==============================================================================

# --- SESSION SECRET ENCRYPTION -------------------------------------------------
def _session_fernet():
    """Derive a Fernet key from SESSION_ENC_KEY; returns None when unset/unavailable."""
    if not SESSION_ENC_KEY:
        return None
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        print("⚠️ [SECURITY] cryptography is not installed; session encryption is disabled.")
        return None
    try:
        key = base64.urlsafe_b64encode(hashlib.sha256(SESSION_ENC_KEY.encode("utf-8")).digest())
        return Fernet(key)
    except Exception as e:
        print(f"⚠️ [SECURITY] Invalid SESSION_ENC_KEY: {e}")
        return None


def encrypt_secret(value):
    if not value or not isinstance(value, str) or value.startswith("enc:"):
        return value
    f = _session_fernet()
    if not f:
        return value
    return "enc:" + f.encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_secret(value):
    if not value or not isinstance(value, str) or not value.startswith("enc:"):
        return value
    f = _session_fernet()
    if not f:
        print("⚠️ [SECURITY] SESSION_ENC_KEY missing/invalid; cannot decrypt a stored session.")
        return None
    try:
        return f.decrypt(value[4:].encode("ascii")).decode("utf-8")
    except Exception:
        print("⚠️ [SECURITY] Stored session could not be decrypted (wrong SESSION_ENC_KEY?).")
        return None


def encrypt_account(acc):
    if not isinstance(acc, dict):
        return acc
    stored = dict(acc)
    if "session" in stored:
        stored["session"] = encrypt_secret(stored["session"])
    if "api_hash" in stored:
        stored["api_hash"] = encrypt_secret(stored["api_hash"])
    return stored


def decrypt_account(acc):
    if not isinstance(acc, dict):
        return acc
    plain = dict(acc)
    if "session" in plain:
        plain["session"] = decrypt_secret(plain["session"])
    if "api_hash" in plain:
        plain["api_hash"] = decrypt_secret(plain["api_hash"])
    return plain


class Database:
    def __init__(self, uri, database_name):
        if uri:
            self._client = motor.motor_asyncio.AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
            self.db = self._client[database_name or "restrict_bot"]
            self.col = self.db.users
        else:
            self._client = None
            self.db = None
            self.col = None

    async def init_indexes(self):
        try:
            if self.db is None or self.col is None:
                return
            await self.col.create_index("id", unique=True)
            await self.db.watchers.create_index([("user_id", 1), ("source_id", 1), ("source_thread", 1)])
            await self.db.sync_progress.create_index([("user_id", 1), ("source_id", 1), ("dest_id", 1)])
            await self.db.saved_channels.create_index([("user_id", 1), ("channel_type", 1), ("last_used", -1)])
            try:
                indexes = await self.db.saved_channels.index_information()
                if "user_id_1_channel_id_1_thread_id_1" in indexes:
                    await self.db.saved_channels.drop_index("user_id_1_channel_id_1_thread_id_1")
            except Exception:
                pass
            await self.db.saved_channels.create_index([("user_id", 1), ("channel_id", 1), ("channel_type", 1), ("thread_id", 1)], unique=True)
            print("✅ Database indexes verified and initialized.")
        except Exception as e:
            print(f"⚠️ Index initialization notice: {e}")

    async def save_channel(self, user_id: int, channel_id, channel_title: str, channel_type: str = "dest", thread_id=None):
        if self.db is None:
            return
        try:
            ch_type = str(channel_type or "dest").lower()
            query = {
                "user_id": int(user_id),
                "channel_id": int(channel_id) if str(channel_id).lstrip('-').isdigit() else str(channel_id),
                "channel_type": ch_type,
                "thread_id": int(thread_id) if thread_id else None
            }
            update_data = {
                "$set": {
                    "channel_title": str(channel_title),
                    "channel_type": ch_type,
                    "last_used": datetime.datetime.now()
                },
                "$inc": {"use_count": 1}
            }
            await self.db.saved_channels.update_one(query, update_data, upsert=True)
        except Exception as e:
            print(f"Error saving channel to memory: {e}")

    async def get_saved_channels(self, user_id: int, channel_type: str = "dest"):
        if self.db is None:
            return []
        try:
            q = {"user_id": int(user_id)}
            if channel_type and channel_type != "all":
                ch_type = str(channel_type).lower()
                if ch_type == "dest":
                    q["channel_type"] = {"$in": ["dest", None]}
                else:
                    q["channel_type"] = ch_type
            cursor = self.db.saved_channels.find(q).sort("last_used", -1)
            channels = []
            async for ch in cursor:
                channels.append(ch)
            return channels
        except Exception as e:
            print(f"Error fetching saved channels: {e}")
            return []

    async def get_saved_channel(self, user_id: int, channel_id, thread_id=None, channel_type: str = "dest"):
        if self.db is None:
            return None
        try:
            query = {
                "user_id": int(user_id),
                "channel_id": int(channel_id) if str(channel_id).lstrip('-').isdigit() else str(channel_id),
                "thread_id": int(thread_id) if thread_id else None
            }
            if channel_type and channel_type != "all":
                ch_type = str(channel_type).lower()
                if ch_type == "dest":
                    query["channel_type"] = {"$in": ["dest", None]}
                else:
                    query["channel_type"] = ch_type
            return await self.db.saved_channels.find_one(query)
        except Exception as e:
            print(f"Error fetching single saved channel: {e}")
            return None

    async def delete_saved_channel(self, user_id: int, channel_id, thread_id=None, channel_type: str = "dest"):
        if self.db is None:
            return False
        try:
            query = {
                "user_id": int(user_id),
                "channel_id": int(channel_id) if str(channel_id).lstrip('-').isdigit() else str(channel_id),
                "thread_id": int(thread_id) if thread_id else None
            }
            if channel_type and channel_type != "all":
                ch_type = str(channel_type).lower()
                if ch_type == "dest":
                    query["channel_type"] = {"$in": ["dest", None]}
                else:
                    query["channel_type"] = ch_type
            res = await self.db.saved_channels.delete_one(query)
            return res.deleted_count > 0
        except Exception as e:
            print(f"Error deleting saved channel: {e}")
            return False

    async def update_channel_title(self, user_id: int, channel_id, new_title: str, channel_type: str = None, thread_id=None):
        if self.db is None:
            return False
        try:
            norm_id = int(channel_id) if str(channel_id).lstrip('-').isdigit() else str(channel_id)
            query = {
                "user_id": int(user_id),
                "channel_id": norm_id
            }
            if channel_type and channel_type != "all":
                ch_type = str(channel_type).lower()
                if ch_type == "dest":
                    query["channel_type"] = {"$in": ["dest", None]}
                else:
                    query["channel_type"] = ch_type
            if thread_id is not None:
                query["thread_id"] = int(thread_id) if thread_id else None

            res = await self.db.saved_channels.update_many(
                query,
                {"$set": {"channel_title": str(new_title)}}
            )
            return res.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating saved channel title: {e}")
            return False

    async def import_watchers_channels(self, client, user_id: int, channel_type: str = "source") -> dict:
        """
        Idempotently imports channels from existing WATCHERS records into saved_channels.
        channel_type: 'source' or 'dest'
        Canonical deduplication: user_id + channel_type + normalised channel_id
        Guarantees that each channel is saved at most once in saved_channels per user.
        """
        if hasattr(self, "db") and self.db is None:
            return {
                "channel_type": channel_type,
                "discovered": 0,
                "newly_saved": 0,
                "already_saved": 0,
                "unresolved": 0,
                "errors": ["Database not connected"]
            }

        ch_type = str(channel_type or "source").lower()
        is_source = (ch_type == "source")

        # 1. Fetch user's watchers
        user_watchers = await self.get_user_watchers(user_id)
        if not user_watchers:
            return {
                "channel_type": ch_type,
                "discovered": 0,
                "newly_saved": 0,
                "already_saved": 0,
                "unresolved": 0,
                "errors": []
            }

        # 2. Extract and deduplicate candidate channels in memory
        candidates = {}  # norm_id -> {"title": ..., "thread_id": ...}

        for w in user_watchers:
            if is_source:
                src_raw = w.get("source_id")
                if src_raw is None or str(src_raw).strip() == "":
                    continue
                try:
                    norm_id = int(src_raw) if str(src_raw).lstrip('-').isdigit() else str(src_raw)
                except Exception:
                    continue

                src_title = w.get("source_title") or w.get("title") or w.get("src_title")
                src_thread = w.get("source_thread")

                if norm_id not in candidates:
                    candidates[norm_id] = {
                        "title": str(src_title).strip() if src_title else None,
                        "thread_id": int(src_thread) if src_thread else None
                    }
                else:
                    cand_t = candidates[norm_id]["title"]
                    if (not cand_t or cand_t.startswith("Chat ") or cand_t.startswith("[Unresolved]")) and src_title:
                        candidates[norm_id]["title"] = str(src_title).strip()
            else:
                targets = w.get("targets", [])
                if not targets and "dest_id" in w:
                    targets = [{
                        "dest_id": w.get("dest_id"),
                        "dest_thread": w.get("dest_thread"),
                        "dest_title": w.get("dest_title")
                    }]

                for t in targets:
                    if not isinstance(t, dict):
                        continue
                    dst_raw = t.get("dest_id")
                    if dst_raw is None or str(dst_raw).strip() == "":
                        continue
                    try:
                        norm_id = int(dst_raw) if str(dst_raw).lstrip('-').isdigit() else str(dst_raw)
                    except Exception:
                        continue

                    dst_title = t.get("dest_title") or t.get("title") or t.get("name")
                    dst_thread = t.get("dest_thread")

                    if norm_id not in candidates:
                        candidates[norm_id] = {
                            "title": str(dst_title).strip() if dst_title else None,
                            "thread_id": int(dst_thread) if dst_thread else None
                        }
                    else:
                        cand_t = candidates[norm_id]["title"]
                        if (not cand_t or cand_t.startswith("Chat ") or cand_t.startswith("[Unresolved]")) and dst_title:
                            candidates[norm_id]["title"] = str(dst_title).strip()

        discovered_count = len(candidates)
        if discovered_count == 0:
            return {
                "channel_type": ch_type,
                "discovered": 0,
                "newly_saved": 0,
                "already_saved": 0,
                "unresolved": 0,
                "errors": []
            }

        # 3. Fetch existing saved channels for this user and channel_type to check presence
        existing_saved = await self.get_saved_channels(user_id, channel_type=ch_type)
        existing_map = {}
        for doc in existing_saved:
            cid = doc.get("channel_id")
            norm_cid = int(cid) if str(cid).lstrip('-').isdigit() else str(cid)
            if norm_cid not in existing_map:
                existing_map[norm_cid] = doc

        newly_saved_count = 0
        already_saved_count = 0
        unresolved_count = 0
        errors = []

        # 4. Migrate channels idempotently
        for cid, info in candidates.items():
            existing_doc = existing_map.get(cid)
            if existing_doc:
                already_saved_count += 1
                curr_title = existing_doc.get("channel_title")
                is_curr_generic = (
                    not curr_title
                    or curr_title.startswith("Chat ")
                    or curr_title.startswith("[Unresolved]")
                    or curr_title in ["Target Chat", "Destination", "Source", "Unknown Destination"]
                )
                if is_curr_generic:
                    cand_title = info.get("title")
                    is_cand_generic = (
                        not cand_title
                        or cand_title.startswith("Chat ")
                        or cand_title.startswith("[Unresolved]")
                        or cand_title in ["Target Chat", "Destination", "Source", "Unknown Destination"]
                    )
                    best_title = cand_title if not is_cand_generic else None
                    if not best_title:
                        try:
                            _, resolved, _, _ = await resolve_telegram_chat_title(client, user_id, cid)
                            if resolved:
                                best_title = resolved
                        except Exception as e_res:
                            logger.error(f"Error resolving title for {cid} during migration: {e_res}")

                    if best_title:
                        await self.update_channel_title(user_id, cid, best_title, channel_type=ch_type)
                        existing_doc["channel_title"] = best_title
                    else:
                        unresolved_count += 1
            else:
                cand_title = info.get("title")
                is_cand_generic = (
                    not cand_title
                    or cand_title.startswith("Chat ")
                    or cand_title.startswith("[Unresolved]")
                    or cand_title in ["Target Chat", "Destination", "Source", "Unknown Destination"]
                )
                final_title = cand_title if not is_cand_generic else None
                if not final_title:
                    try:
                        _, resolved, _, _ = await resolve_telegram_chat_title(client, user_id, cid)
                        if resolved:
                            final_title = resolved
                    except Exception as e_res:
                        logger.error(f"Error resolving title for {cid} during migration: {e_res}")

                if not final_title:
                    unresolved_count += 1
                    final_title = f"[Unresolved] Chat {cid}"

                try:
                    await self.save_channel(
                        user_id=user_id,
                        channel_id=cid,
                        channel_title=final_title,
                        channel_type=ch_type,
                        thread_id=info.get("thread_id")
                    )
                    newly_saved_count += 1
                    existing_map[cid] = {"channel_id": cid, "channel_title": final_title}
                except Exception as e_save:
                    err_msg = f"Failed to save channel {cid}: {e_save}"
                    logger.error(err_msg)
                    errors.append(err_msg)

        return {
            "channel_type": ch_type,
            "discovered": discovered_count,
            "newly_saved": newly_saved_count,
            "already_saved": already_saved_count,
            "unresolved": unresolved_count,
            "errors": errors
        }

    async def get_replacements(self, user_id: int):
        if self.db is None: return []
        try:
            doc = await self.db.replacements.find_one({"user_id": int(user_id)})
            return doc.get("rules", []) if doc else []
        except Exception:
            return []

    async def add_replacement(self, user_id: int, find_text: str, replace_text: str):
        if self.db is None: return False
        try:
            rules = await self.get_replacements(user_id)
            updated = False
            for r in rules:
                if r["find"].lower() == find_text.lower():
                    r["replace"] = replace_text
                    updated = True
                    break
            if not updated:
                rules.append({"find": find_text, "replace": replace_text})
            await self.db.replacements.update_one(
                {"user_id": int(user_id)},
                {"$set": {"rules": rules, "updated_at": datetime.datetime.now()}},
                upsert=True
            )
            return True
        except Exception:
            return False

    async def delete_replacement(self, user_id: int, find_text: str):
        if self.db is None: return False
        try:
            rules = await self.get_replacements(user_id)
            rules = [r for r in rules if r["find"].lower() != find_text.lower()]
            await self.db.replacements.update_one(
                {"user_id": int(user_id)},
                {"$set": {"rules": rules}},
                upsert=True
            )
            return True
        except Exception:
            return False

    async def clear_replacements(self, user_id: int):
        if self.db is None: return False
        try:
            await self.db.replacements.delete_one({"user_id": int(user_id)})
            return True
        except Exception:
            return False

    async def inc_forward_stats(self, user_id: int, is_fast_copy: bool = True, size_bytes: int = 0, source_id=None):
        if self.db is None or not user_id: return
        try:
            now = datetime.datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            year, week_num, _ = now.isocalendar()
            week_str = f"{year}-W{week_num:02d}"
            month_str = now.strftime("%Y-%m")
            update = {
                "$inc": {
                    "total_forwards": 1,
                    f"daily.{today_str}": 1,
                    f"weekly.{week_str}": 1,
                    f"monthly.{month_str}": 1,
                    "fast_copy_count" if is_fast_copy else "download_count": 1,
                    "bytes_saved" if is_fast_copy else "bytes_downloaded": int(size_bytes)
                }
            }
            if source_id is not None:
                s_key = str(source_id).replace(".", "_")
                update["$inc"][f"channels.{s_key}.total"] = 1
                update["$inc"][f"channels.{s_key}.daily.{today_str}"] = 1
                update["$inc"][f"channels.{s_key}.weekly.{week_str}"] = 1
                update["$inc"][f"channels.{s_key}.monthly.{month_str}"] = 1
                if is_fast_copy:
                    update["$inc"][f"channels.{s_key}.fast_copy_count"] = 1
                    update["$inc"][f"channels.{s_key}.bytes_saved"] = int(size_bytes)
                else:
                    update["$inc"][f"channels.{s_key}.download_count"] = 1
                    update["$inc"][f"channels.{s_key}.bytes_downloaded"] = int(size_bytes)
            await self.db.stats.update_one({"user_id": int(user_id)}, update, upsert=True)
        except Exception as e:
            print(f"[inc_forward_stats notice]: {e}")

    async def get_forward_stats(self, user_id: int):
        if self.db is None or not user_id: return {}
        try:
            doc = await self.db.stats.find_one({"user_id": int(user_id)})
            return doc or {}
        except Exception:
            return {}

    async def set_user_thumb(self, user_id: int, file_id: str):
        if self.db is None: return
        try:
            await self.db.users.update_one({"id": int(user_id)}, {"$set": {"custom_thumb": file_id}}, upsert=True)
        except Exception:
            pass

    async def get_user_thumb(self, user_id: int):
        if self.db is None: return None
        try:
            doc = await self.db.users.find_one({"id": int(user_id)}, {"custom_thumb": 1})
            return doc.get("custom_thumb") if doc else None
        except Exception:
            return None

    async def del_user_thumb(self, user_id: int):
        if self.db is None: return
        try:
            await self.db.users.update_one({"id": int(user_id)}, {"$unset": {"custom_thumb": ""}})
        except Exception:
            pass

    async def get_dl_status(self):
        if self.db is None:
            return True
        try:
            setting = await self.db.settings.find_one({'id': 'system'})
            if setting: return setting.get('auto_download', True)
        except Exception:
            pass
        return True

    async def toggle_dl_status(self):
        if self.db is None:
            return False
        try:
            current = await self.get_dl_status()
            await self.db.settings.update_one({'id': 'system'}, {'$set': {'auto_download': not current}}, upsert=True)
            return not current
        except Exception:
            return False

    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
            session = None,
            api_id = None,
            api_hash = None,
        )

    async def add_user(self, id, name):
        if self.col is None:
            return
        try:
            user = self.new_user(id, name)
            if not await self.is_user_exist(id):
                await self.col.insert_one(user)
        except Exception:
            pass

    async def is_user_exist(self, id):
        if self.col is None:
            return False
        try:
            user = await self.col.find_one({'id':int(id)})
            return bool(user)
        except Exception:
            return False

    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def get_all_users(self):
        cursor = self.col.find({})
        return cursor

    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})

    async def set_session(self, id, session):
        await self.col.update_one({'id': int(id)}, {'$set': {'session': encrypt_secret(session)}})

    async def get_session(self, id):
        user = await self.col.find_one({'id': int(id)})
        if user:
            return decrypt_secret(user.get('session'))
        return None

    async def set_api_id(self, id, api_id):
        await self.col.update_one({'id': int(id)}, {'$set': {'api_id': api_id}})

    async def get_api_id(self, id):
        user = await self.col.find_one({'id': int(id)})
        if user:
            return user.get('api_id')
        return None

    async def set_api_hash(self, id, api_hash):
        await self.col.update_one({'id': int(id)}, {'$set': {'api_hash': encrypt_secret(api_hash)}})

    async def get_api_hash(self, id):
        user = await self.col.find_one({'id': int(id)})
        if user:
            return decrypt_secret(user.get('api_hash'))
        return None


    async def get_user_accounts(self, id):
        user = await self.col.find_one({'id': int(id)})
        if not user:
            return []
        accounts = user.get('accounts') or []
        if not accounts and user.get('session'):
            legacy_acc = {
                'account_id': f"acc_{id}_main",
                'phone': "Legacy Primary",
                'first_name': user.get('name') or "Primary Account",
                'username': "",
                'user_id': int(id),
                'session': decrypt_secret(user.get('session')),
                'api_id': user.get('api_id'),
                'api_hash': decrypt_secret(user.get('api_hash')),
                'added_at': datetime.datetime.now().isoformat(),
                'is_active': True
            }
            accounts = [legacy_acc]
            await self.col.update_one(
                {'id': int(id)},
                {'$set': {'accounts': [encrypt_account(legacy_acc)], 'active_account_id': legacy_acc['account_id']}}
            )
        return [decrypt_account(a) for a in accounts if isinstance(a, dict)]

    async def add_user_account(self, id, account_data, set_as_active=True):
        user = await self.col.find_one({'id': int(id)})
        if not user:
            await self.add_user(id, account_data.get('first_name', 'User'))
            user = await self.col.find_one({'id': int(id)}) or {}
            
        accounts = [encrypt_account(a) for a in (user.get('accounts') or []) if isinstance(a, dict)]
        if not accounts and user.get('session'):
            accounts.append({
                'account_id': f"acc_{id}_main",
                'phone': "Legacy Primary",
                'first_name': user.get('name') or "Primary Account",
                'username': "",
                'user_id': int(id),
                'session': encrypt_secret(user.get('session')),
                'api_id': user.get('api_id'),
                'api_hash': encrypt_secret(user.get('api_hash')),
                'added_at': datetime.datetime.now().isoformat(),
                'is_active': False
            })

        acc_id = str(account_data.get('account_id') or account_data.get('user_id') or uuid.uuid4().hex[:8])
        account_data = encrypt_account(account_data)
        account_data['account_id'] = acc_id
        account_data['added_at'] = datetime.datetime.now().isoformat()
        
        accounts = [
            a for a in accounts 
            if str(a.get('account_id')) != str(acc_id) and (not account_data.get('phone') or a.get('phone') != account_data.get('phone'))
        ]
        
        if set_as_active or len(accounts) == 0:
            for a in accounts:
                a['is_active'] = False
            account_data['is_active'] = True
            active_acc = account_data
        else:
            account_data['is_active'] = False
            active_acc = next((a for a in accounts if a.get('is_active')), account_data)

        accounts.append(account_data)
        
        update_fields = {
            'accounts': accounts,
            'active_account_id': active_acc['account_id'],
            'session': active_acc['session'],
            'api_id': active_acc.get('api_id'),
            'api_hash': active_acc.get('api_hash')
        }
        await self.col.update_one({'id': int(id)}, {'$set': update_fields})
        return acc_id

    async def switch_active_account(self, id, account_id):
        accounts = await self.get_user_accounts(id)
        target_acc = None
        for a in accounts:
            if str(a.get('account_id')) == str(account_id):
                a['is_active'] = True
                target_acc = a
            else:
                a['is_active'] = False
                
        if not target_acc:
            return None
            
        update_fields = {
            'accounts': [encrypt_account(a) for a in accounts],
            'active_account_id': target_acc['account_id'],
            'session': encrypt_secret(target_acc['session']),
            'api_id': target_acc.get('api_id'),
            'api_hash': encrypt_secret(target_acc.get('api_hash'))
        }
        await self.col.update_one({'id': int(id)}, {'$set': update_fields})
        return target_acc

    async def delete_user_account(self, id, account_id):
        accounts = await self.get_user_accounts(id)
        remaining = [a for a in accounts if str(a.get('account_id')) != str(account_id)]
        new_active = None
        if remaining:
            new_active = next((a for a in remaining if a.get('is_active')), remaining[0])
            for a in remaining:
                a['is_active'] = (str(a.get('account_id')) == str(new_active.get('account_id')))
            update_fields = {
                'accounts': [encrypt_account(a) for a in remaining],
                'active_account_id': new_active['account_id'],
                'session': encrypt_secret(new_active['session']),
                'api_id': new_active.get('api_id'),
                'api_hash': encrypt_secret(new_active.get('api_hash'))
            }
        else:
            update_fields = {
                'accounts': [],
                'active_account_id': None,
                'session': None,
                'api_id': None,
                'api_hash': None
            }
        await self.col.update_one({'id': int(id)}, {'$set': update_fields})
        return remaining, new_active

    async def total_session_users_count(self):
        count = await self.col.count_documents({"session": {"$ne": None}})
        return count

    async def save_sync_progress(self, user_id, source_id, dest_id, msg_id):
        query = {"user_id": int(user_id), "source_id": str(source_id), "dest_id": str(dest_id)}
        await self.db.sync_progress.update_one(
            query,
            {"$set": {"last_msg_id": int(msg_id), "updated_at": datetime.datetime.now()}},
            upsert=True
        )

    async def get_sync_progress(self, user_id, source_id, dest_id):
        data = await self.db.sync_progress.find_one({"user_id": int(user_id), "source_id": str(source_id), "dest_id": str(dest_id)})
        return data.get("last_msg_id", 0) if data else 0

    async def add_watcher(self, user_id, source_id, dest_id, source_thread=None, dest_thread=None, delay=0, is_restricted=False, source_title=None, dest_title=None, allowed_types=None, text_format=None):
        if allowed_types is None:
            allowed_types = ["Video", "Document"] 
        if text_format is None:
            text_format = []

        query = {
            'user_id': int(user_id),
            'source_id': int(source_id),
            'source_thread': int(source_thread) if source_thread else None
        }
        
        new_target = {
            "dest_id": int(dest_id),
            "dest_thread": int(dest_thread) if dest_thread else None,
            "dest_title": dest_title
        }

        existing = await self.db.watchers.find_one(query)
        if existing:
            targets = existing.get("targets", [])
            if not targets and 'dest_id' in existing:
                targets = [{"dest_id": existing['dest_id'], "dest_thread": existing.get('dest_thread'), "dest_title": existing.get('dest_title')}]
                
            target_exists = any(t["dest_id"] == new_target["dest_id"] and t.get("dest_thread") == new_target["dest_thread"] for t in targets)
            
            if not target_exists:
                targets.append(new_target)
                await self.db.watchers.update_one(query, {
                    "$set": {"targets": targets, "allowed_types": allowed_types, "delay": int(delay), "text_format": text_format}
                })
            else:
                await self.db.watchers.update_one(query, {"$set": {"allowed_types": allowed_types, "delay": int(delay), "text_format": text_format}})
        else:
            watcher = {
                "user_id": user_id,
                "source_id": int(source_id),
                "source_thread": int(source_thread) if source_thread else None,
                "delay": int(delay),
                "is_restricted": is_restricted,
                "source_title": source_title,
                "allowed_types": allowed_types,
                "text_format": text_format,
                "targets": [new_target],
                "created_at": datetime.datetime.now()
            }
            await self.db.watchers.insert_one(watcher)

    async def get_watcher(self, source_id, source_thread=None, user_id=None):
        query = {'source_id': int(source_id)}
        if source_thread:
            query['source_thread'] = int(source_thread)
        if user_id is not None:
            query['user_id'] = int(user_id)
        return await self.db.watchers.find_one(query)

    async def get_all_watchers(self):
        if self.db is None:
            async def _empty():
                if False: yield
            return _empty()
        return self.db.watchers.find({})

    async def get_user_watchers(self, user_id, show_all=False):
        if self.db is None: return []
        try:
            if show_all:
                cursor = self.db.watchers.find({})
            else:
                q_filter = {"$or": [{"user_id": user_id}, {"user_id": int(user_id)}, {"user_id": str(user_id)}]}
                cursor = self.db.watchers.find(q_filter)
            watchers = []
            async for w in cursor:
                watchers.append(w)
            return watchers
        except Exception:
            return []

    async def remove_watcher(self, source_id, user_id=None):
        query = {'source_id': int(source_id)}
        if user_id is not None:
            query['$or'] = [{'user_id': user_id}, {'user_id': int(user_id)}, {'user_id': str(user_id)}]
        result = await self.db.watchers.delete_many(query)
        return result.deleted_count > 0

    async def remove_watcher_target(self, source_id, dest_id, source_thread=None, user_id=None):
        query = {'source_id': int(source_id)}
        if source_thread is not None:
            query['source_thread'] = int(source_thread)
        if user_id is not None:
            query['$or'] = [{'user_id': user_id}, {'user_id': int(user_id)}, {'user_id': str(user_id)}]

        result = await self.db.watchers.update_one(
            query,
            {"$pull": {"targets": {"dest_id": int(dest_id)}}}
        )
        doc = await self.db.watchers.find_one(query)
        if doc and not doc.get("targets"):
            await self.db.watchers.delete_one(query)
        return result.modified_count > 0

db = Database(DB_URI, DB_NAME)

# ==============================================================================
# --- CLIENT & GLOBAL STATE ---
# ==============================================================================

app = Client(
    "RestrictedBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=50,                 
    sleep_threshold=20,
    ipv6=False                  
)

# ==============================================================================
# --- NATIVE ASK IMPLEMENTATION ---
# ==============================================================================
ASK_FUTURES = {}
ASK_FLOW_SEQ = 0


def _make_cancel_message(client, chat_id):
    class MockMessage:
        text = "/cancel"
        async def reply(self, reply_text, *args, **kw):
            return await client.send_message(chat_id, reply_text, *args, **kw)
    mock_msg = MockMessage()
    mock_msg._client = client
    return mock_msg


async def custom_ask(self, chat_id: int, text: str, filters=None, timeout: int = 300, flow_id: str = None, **kwargs):
    global ASK_FLOW_SEQ
    await self.send_message(chat_id, text, **kwargs)
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    if flow_id is None:
        ASK_FLOW_SEQ += 1
        flow_id = f"auto{ASK_FLOW_SEQ}"
    key = (int(chat_id), str(flow_id))

    # A new prompt supersedes older pending prompts in the same chat; never leave them hanging
    for old_key in [k for k in list(ASK_FUTURES.keys()) if k[0] == key[0] and k != key]:
        old_future, _old_filters, _created = ASK_FUTURES.pop(old_key, (None, None, None))
        if old_future and not old_future.done():
            old_future.set_result(_make_cancel_message(self, chat_id))

    ASK_FUTURES[key] = (future, filters, time.time())

    try:
        return await asyncio.wait_for(future, timeout)
    except asyncio.TimeoutError:
        ASK_FUTURES.pop(key, None)
        try:
            await self.send_message(chat_id, "⏱ <b>Timeout:</b> no response received — the prompt was cancelled.")
        except Exception:
            pass
        return _make_cancel_message(self, chat_id)

Client.ask = custom_ask

# ==============================================================================
# --- GLOBAL ACCESS CONTROL GATEKEEPERS (GROUP -2) ---
# ==============================================================================


# ==============================================================================
# --- 10 ROAST & COMEDY ACCESS DENIED TEMPLATES (CODE BLOCK MONOSPACE) ---
# ==============================================================================
UNAUTH_TEMPLATES = [
    """╔══════════════════════════════════════════════════════╗
║        ⛔ ACCESS DENIED : BINA LIFAAFE ENTRY ⛔      ║
╠══════════════════════════════════════════════════════╣
Arey bhai bhai! Shaadi me bina lifaafe ke ghus gaye?
Direct rasmalai pe toot pade? Gatekeeper ne pakad liya!
Ye bot filhaal private VIP list pe chal raha hai.

🚀 BOT KE ASLI JALWE DEKHO (FULL PAISA VASOOL):
⚡ Normal Channels: Rocket speed instant direct forward!
🔓 Restricted Content: Auto Download & Re-Upload bypass!
🧹 Auto-Rename & Cleaner: Faltu sponsor/promo delete!
🔄 24/7 Live Watcher: Source to destination auto clone.
💾 100 GB Download: Restricted files ka monthly quota
   (Bas setup ke liye apna ek email ID dena padega).
╠══════════════════════════════════════════════════════╣
💸 Pocket Pinch: Sirf ₹50 / Month (Chai-sutta se sasta!)
╠══════════════════════════════════════════════════════╣
👑 Whitelist hona hai? Message Owner:
👉 @lucifermorningstarofficialsss
╚══════════════════════════════════════════════════════╝""",

    """╔══════════════════════════════════════════════════════╗
║        🛑 RUKO ZARA, SABAR KARO : ACCESS DENIED 🛑   ║
╠══════════════════════════════════════════════════════╣
Arey mitra, pehle thoda paani piyo, lambi saans lo!
Socha tha bot free hai toh aaj hi poora Telegram ghar le
jaoge? Dhakka-mukki nahi karne ka, line me lago!

🛠️ YE BEAST BOT KYA KYA KARTA HAI?
• Normal Channels: Bina delay ke superfast instant forward.
• Restricted Channels: Background Download & Fresh Upload.
• Smart Clean-Up: Title se sponsor ads & promo auto-clean!
• 100 GB/Month Quota: Restricted content download enabled
  (Setup ke liye personal email ID required hai).
• 24/7 Channel Watcher: Ek baar lagao, din-raat sync paao.
╠══════════════════════════════════════════════════════╣
☕ Price: Sirf ₹50 / Month (Tapri ki 2 chai se bhi sasta!)
╠══════════════════════════════════════════════════════╣
🤝 Izzat ke sath access lene ke liye Owner ko ping karo:
👑 @lucifermorningstarofficialsss
╚══════════════════════════════════════════════════════╝""",

    """╔══════════════════════════════════════════════════════╗
║        ⛔ ACCESS DENIED : YE SAB DOGLAPAN HAI ⛔     ║
╠══════════════════════════════════════════════════════╣
Arey bhai, bina permission bot chalane ka try kar rahe ho?
Ye sab doglapan hai! Par chinta mat karo, hum deal laye
hain jisme aapka poora fayda hai.

💼 THE KILLER TECH STACK:
⚡ Normal Channels: Public channels ka instant fast clone.
🛡️ Restricted Bypass: Heavy Download & Clean Upload engine
✂️ Ad-Stripper: Starting ke sponsor & promo auto-remove.
📦 Turbo Batch: 1 se lekar 10,000 files bulk transfer.
💾 100 GB Data Download: Restricted files ka monthly quota
   (Bas setup ke liye apna ek Email ID provide karo).
╠══════════════════════════════════════════════════════╣
💰 The Valuation: Sirf ₹50 / Month (Popcorn se bhi sasta!)
╠══════════════════════════════════════════════════════╣
👑 Deal done karni hai? Owner ko abhi text bhejo:
👉 @lucifermorningstarofficialsss
╚══════════════════════════════════════════════════════╝""",

    """╔══════════════════════════════════════════════════════╗
║        🔒 VIP PRIVATE ACCESS : PERMISSION REQUIRED 🔒 ║
╠══════════════════════════════════════════════════════╣
Dost sach batao, ₹50 me aaj kal milta kya hai? Lays me bhi
nitrogen bhari hoti hai! Par yahan ₹50 me beast bot milega:

🚀 TOP TIER SPECIFICATIONS:
⏩ Normal Forwarding: Palken jhapkate hi instant transfer!
📥 Restricted Engine: Safe Download & Upload with no block.
🧼 Auto Scrubbing: Suru ka promo name aur link delete.
🔄 Live Watcher: Source se naya post aate hi auto clone.
💾 100 GB/Mo Download: Restricted content download enabled
   (Email ID dena zaroori hai configuration ke liye).
╠══════════════════════════════════════════════════════╣
🏷️ Subscription: Sirf ₹50 / Month (Chai-sutta kharcha!)
╠══════════════════════════════════════════════════════╣
👑 Whitelist karwane ke liye abhi Owner se contact karo:
🔗 @lucifermorningstarofficialsss
╚══════════════════════════════════════════════════════╝""",

    """╔══════════════════════════════════════════════════════╗
║        ⛔ ACCESS DENIED : DAYA DARWAZA MAT TODO! ⛔  ║
╠══════════════════════════════════════════════════════╣
Kuch toh gadbad hai Daya! Ye user bina VIP pass ke andar
ghusne ki koshish kar raha hai! System ne lock laga diya!

🔍 FORENSIC REPORT : BOT ME KYA KYA ASSETS HAIN?
⚡ Normal Channels: Speed engine bina rukaavat fast forward
🔐 Restricted Locker: Download & Upload se restricted clone
🎯 Auto Renaming: Sponsor text aur ads ka automatic safaya
💾 100 GB / Month: Restricted files ka direct download
   (Apna personal Email ID provide karna padega).
🤖 24x7 Automation: Auto Channel Watcher on standby.
╠══════════════════════════════════════════════════════╣
💵 Faisla: Sirf ₹50 / Month (Chai-sutta se sasta deal)
╠══════════════════════════════════════════════════════╣
👑 Case solve karne ke liye Owner ko hazir karo:
👉 @lucifermorningstarofficialsss
╚══════════════════════════════════════════════════════╝""",

    """╔══════════════════════════════════════════════════════╗
║        ⚠️ HOLD ON GUEST : ACCESS NOT WHITELISTED ⚠️   ║
╠══════════════════════════════════════════════════════╣
Swiggy pe surge charge ₹60 lag jaata hai, aur yahan ₹50 me
Telegram ka sabse powerful infiltrator bot mil raha hai!
Par afsos, aapka Telegram ID abhi approved nahi hai.

🍔 MENU OF FEATURES:
🚀 Normal Channels: Instant 0-second direct bulk forwarding.
📦 Restricted Channels: Safe Download & Upload processing.
🧽 Clean Captions: Initial sponsor names automatically gone
💾 100 GB Download: Restricted files ka monthly quota
   (Configuration ke liye apna email ID dena hoga).
📡 Channel Watcher: 24/7 background real-time sync.
╠══════════════════════════════════════════════════════╣
💳 Bill Amount: ₹50 / Month Only (Full Pocket Friendly)
╠══════════════════════════════════════════════════════╣
📩 VIP Table book karne ke liye Owner ko contact karein:
👑 @lucifermorningstarofficialsss
╚══════════════════════════════════════════════════════╝""",

    """╔══════════════════════════════════════════════════════╗
║        ⛔ ACCESS DENIED : ADMIT CARD KAHAN HAI? ⛔   ║
╠══════════════════════════════════════════════════════╣
Arey padhaku bhai, exam hall me bina roll number ke entry
nahi milti! Waise hi ye bot strictly private whitelist pe
lock hai. Par syllabus dekh lo, full marks aayenge:

📚 PAPER 1 : BOT CAPABILITIES:
⚡ Normal Channels: Zero delay high-speed instant clone.
📥 Restricted Streams: Download karke naya post upload.
✂️ Ad Cut: Shuru ka sponsor name aur promo link clean.
💾 100 GB Monthly Download: Restricted content allowed
   (Setup ke liye bas apna ek Email ID submit karna hoga).
🔄 Auto Watcher: 24/7 non-stop monitoring & clone.
╠══════════════════════════════════════════════════════╣
🏷️ Admission Fee: Sirf ₹50 / Month (Chai-sutta se sasta)
╠══════════════════════════════════════════════════════╣
👑 Principal (Owner) se signature karwane ke liye click:
👉 @lucifermorningstarofficialsss
╚══════════════════════════════════════════════════════╝""",

    """╔══════════════════════════════════════════════════════╗
║        🛑 TC KA CHHAAPA : TICKET DIKHAO BHAI! 🛑     ║
╠══════════════════════════════════════════════════════╣
Rajdhani Express me chadhe aur socha bina ticket nikal
lenge? Hamare automated bot guard ne pakad liya hai!
Ye train sirf verified VIP passengers ke liye chalti hai.

🚂 ENGINE SPECIFICATIONS:
⚡ Normal Line: Superfast channels ka instant forwarding.
🛡️ Heavy Cargo: Restricted channels ka Download & Upload.
🧹 Clean Track: Title se sponsor ads & rubbish auto-clean!
💾 100 GB Pass: Restricted files ka monthly download quota
   (Seat reservation ke liye apna email ID dena hoga).
🔄 Auto-Pilot: 24/7 live channel watcher integration.
╠══════════════════════════════════════════════════════╣
🎟️ Monthly Ticket: Sirf ₹50 / Month (Platform ticket rate!)
╠══════════════════════════════════════════════════════╣
👑 TTE (Owner) se ticket lene ke liye abhi sampark karein:
🔗 @lucifermorningstarofficialsss
╚══════════════════════════════════════════════════════╝""",

    """╔══════════════════════════════════════════════════════╗
║        ⛔ ACCESS DENIED : SCREEN LIMIT REACHED ⛔    ║
╠══════════════════════════════════════════════════════╣
Aise bina puche bot me ghus rahe ho jaise doston se
Netflix ka password maang ke 4K me stream chala li ho!
Par ye bot exclusive private members ke liye reserved hai.

🍿 PREMIER SHOW HIGHLIGHTS:
⏩ Normal Channels: Bullet speed instant direct forward.
🔐 Restricted Channels: Automated Download & Upload pipeline.
🧼 Auto Ad-Block: Sponsor names & spam lines auto deleted.
💾 100 GB Monthly Download: Restricted videos/files quota
   (Bas setup ke liye apna ek Email ID provide karo).
🤖 Auto Sync: Live channel watcher on duty 24/7.
╠══════════════════════════════════════════════════════╣
🎟️ Monthly Pass: Sirf ₹50 / Month (Chai-sutta kharcha!)
╠══════════════════════════════════════════════════════╣
👑 VIP Subscription lene ke liye Owner ko ping karein:
👉 @lucifermorningstarofficialsss
╚══════════════════════════════════════════════════════╝""",

    """╔══════════════════════════════════════════════════════╗
║        ⛔ ACCESS DENIED : BAAP SE BAKCHODI NAHI ⛔   ║
╠══════════════════════════════════════════════════════╣
"Hume laga sabka badla lene aaye ho, par tum toh bina
permission ke command maarne nikal pade!"
Maaf karna lala, bina whitelist huye bot nahi hilega!

💣 ASLI ASLA DEKHO BOT KA:
⚡ Normal Forward: Goli ki speed me instant direct clone.
📥 Restricted Forward: Download & Upload se har lock khule!
🧹 Auto-Rename: Shuru ka sponsor name jad se gayab.
💾 100 GB Download: Restricted files ka monthly quota
   (Iske liye apna personal email ID dena padega).
🔄 24/7 Watcher: Bina hath lagaye automatic clone chalu.
╠══════════════════════════════════════════════════════╣
💰 Hissa: Sirf ₹50 / Month (Chai-sutta se bhi sasta plan!)
╠══════════════════════════════════════════════════════╣
👑 Sarkar (Owner) ke aage arzi lagane ke liye click karo:
👉 @lucifermorningstarofficialsss
╚══════════════════════════════════════════════════════╝"""
]

@app.on_message(filters.private & ~filters.bot, group=-2)
async def auth_gatekeeper(client: Client, message: Message):
    if not AUTH_USERS:
        return
    # STRICT CHAT-TYPE GUARD: Never intercept or reply in channels, groups, or supergroups!
    if not message.chat or message.chat.type != enums.ChatType.PRIVATE:
        return
    if getattr(message, "service", False) or getattr(message, "empty", False):
        return
    user_id = message.from_user.id if message.from_user else 0
    if not user_id or getattr(message.from_user, "is_bot", False):
        return
    if not is_authorized(user_id):
        now = time.time()
        last_sent = UNAUTH_NOTIFY_CACHE.get(user_id, 0)
        raw_msg = (message.text or message.caption or "").strip()
        is_start = raw_msg.startswith('/start')
        
        # Immediate response on EVERY /start command without delay; throttle generic spam to 5s
        if is_start or (now - last_sent > 5):
            UNAUTH_NOTIFY_CACHE[user_id] = now
            try:
                owner_username = os.environ.get("OWNER_USERNAME", "").strip().lstrip("@") or "lucifermorningstarofficialsss"
                owner_url = f"https://t.me/{owner_username}"
                custom_override = os.environ.get("ACCESS_DENIED_MESSAGE", "").strip()
                if custom_override:
                    body = custom_override
                else:
                    body = random.choice(UNAUTH_TEMPLATES)
                    if owner_username != "lucifermorningstarofficialsss":
                        body = body.replace("@lucifermorningstarofficialsss", f"@{owner_username}")

                escaped_body = html.escape(body)
                reply_parts = [
                    f"<pre>{escaped_body}</pre>",
                    "",
                    f"🆔 <b>Your Telegram User ID:</b> <code>{user_id}</code>",
                    f'👑 <b>Owner:</b> @{owner_username}',
                    "<i>(Click button below or copy your ID and message the owner to get whitelisted)</i>"
                ]
                reply_text = chr(10).join(reply_parts)
                markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("👑 Contact Owner (Get Access)", url=owner_url)]
                ])
                try:
                    await message.reply(
                        reply_text,
                        quote=True,
                        disable_web_page_preview=True,
                        reply_markup=markup
                    )
                except Exception:
                    try:
                        await client.send_message(
                            chat_id=message.chat.id,
                            text=reply_text,
                            disable_web_page_preview=True,
                            reply_markup=markup
                        )
                    except Exception:
                        # Plaintext fallback that never fails entity parsing
                        plain_body = f"{body}\n\n🆔 Your Telegram User ID: {user_id}\n👑 Owner: @{owner_username}\n(Contact your bot administrator to get whitelisted)"
                        await client.send_message(
                            chat_id=message.chat.id,
                            text=plain_body,
                            disable_web_page_preview=True,
                            reply_markup=markup,
                            parse_mode=None
                        )
            except Exception as e:
                print(f"[Gatekeeper Error] Failed to send paywall notice: {e}")
                try:
                    await client.send_message(
                        chat_id=message.chat.id,
                        text=f"⛔ Access Denied!\n\nThis bot is private.\n🆔 Your User ID: {user_id}\nPlease contact the administrator.",
                        parse_mode=None
                    )
                except Exception:
                    pass
        
        # Stop propagation only AFTER sending notice so message actually arrives
        message.stop_propagation()

@app.on_callback_query(group=-2)
async def callback_auth_gatekeeper(client: Client, query: CallbackQuery):
    if not AUTH_USERS:
        return
    # Only enforce gatekeeper on private chat callbacks
    if query.message and query.message.chat and query.message.chat.type != enums.ChatType.PRIVATE:
        return
    user_id = query.from_user.id if query.from_user else 0
    if not user_id or getattr(query.from_user, "is_bot", False):
        return
    if not is_authorized(user_id):
        try:
            await query.answer("⛔ Access Denied: You are not authorized to use this bot.", show_alert=True)
        except Exception:
            pass
        query.stop_propagation()

@app.on_message(filters.private, group=-1)
async def ask_listener(client, message):
    chat_id = message.chat.id
    pending = [(k, v) for k, v in ASK_FUTURES.items() if k[0] == chat_id]
    if not pending:
        return
    key, (future, filter_cond, _created) = max(pending, key=lambda kv: kv[1][2])

    if filter_cond:
        is_match = filter_cond(client, message)
        if asyncio.iscoroutine(is_match):
            is_match = await is_match
        if not is_match:
            return

    ASK_FUTURES.pop(key, None)
    if not future.done():
        future.set_result(message)
    message.stop_propagation()

# ==============================================================================

BOT_START_TIME = time.time()

ACTIVE_PROCESSES = defaultdict(dict)
ALBUM_BUFFERS = {}


# --- RE-BRANDING ENGINE CACHE & LOGIC ---
USER_REPLACEMENTS = {}

async def get_user_replacements(user_id: int):
    if not user_id:
        return []
    uid = int(user_id)
    if uid in USER_REPLACEMENTS:
        return USER_REPLACEMENTS[uid]
    rules = await db.get_replacements(uid)
    USER_REPLACEMENTS[uid] = rules
    return rules

async def apply_user_replacements(text: str, user_id: int) -> str:
    if not text or not user_id:
        return text
    uid = int(user_id)
    rules = USER_REPLACEMENTS.get(uid)
    if rules is None:
        rules = await db.get_replacements(uid)
        USER_REPLACEMENTS[uid] = rules
    if not rules:
        return text
    for rule in rules:
        f_str = rule.get("find", "").strip()
        r_str = rule.get("replace", "")
        if f_str:
            try:
                pattern = re.compile(re.escape(f_str), re.IGNORECASE)
                text = pattern.sub(r_str, text)
            except Exception:
                text = text.replace(f_str, r_str)
    return text

async def get_or_download_user_thumb(user_id: int, client: Client):
    if not user_id:
        return None
    thumb_path = Path(f"./thumbnails/{user_id}.jpg")
    if thumb_path.exists():
        return str(thumb_path)
    file_id = await db.get_user_thumb(user_id)
    if file_id:
        try:
            Path("./thumbnails").mkdir(parents=True, exist_ok=True)
            downloaded = await client.download_media(file_id, file_name=str(thumb_path))
            if downloaded and os.path.exists(downloaded):
                return str(thumb_path)
        except Exception:
            pass
    return None
  
CANCEL_FLAGS = {}  

batch_temp = type("BT", (), {})()
batch_temp.ACTIVE_TASKS = defaultdict(int)

# --- ROBUST CONCURRENCY SETTINGS ---
SERVER_UPLOAD_LIMIT = asyncio.Semaphore(30) 
USER_SEMAPHORE_LIMIT = 3 
USER_SEMAPHORES = defaultdict(lambda: asyncio.Semaphore(USER_SEMAPHORE_LIMIT))

PENDING_TASKS = {}
PENDING_ADD_CHANNEL = {}  # user_id -> prompt_message_id
PROGRESS = {}
SESSION_STRING_SIZE = 351

MAX_CONCURRENT_TASKS_PER_USER = int(os.environ.get("MAX_TASKS_PER_USER", "3"))

USER_CLIENTS = {} 
PENDING_LOGINS = {}
IMPORT_LOCKS = set()

ALL_MSG_TYPES = ["Video", "Document", "Text", "Audio", "Photo", "Voice", "Animation", "Sticker"]

# ==============================================================================
# --- NEW PREMIUM PROGRESS UI AESTHETICS ---
# ==============================================================================

def _pretty_bytes(n: float) -> str:
    try:
        n = float(n)
    except Exception:
        return "0 B"
    if n == 0: return "0 B"
    units = ("B", "KB", "MB", "GB", "TB", "PB")
    i = 0
    while n >= 1024 and i < len(units) - 1:
        n /= 1024
        i += 1
    unit = units[i]
    if unit == "B": return f"{int(n)} {unit}"
    else: return f"{n:.1f} {unit}"

def get_readable_time(seconds: int) -> str:
    try:
        seconds = int(seconds)
    except Exception:
        seconds = 0
    if seconds <= 0: return "0s"
    time_parts = []
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0: time_parts.append(f"{h}h")
    if m > 0: time_parts.append(f"{m}m")
    if not time_parts or s > 0: time_parts.append(f"{s}s")
    return " ".join(time_parts)

def generate_bar(percent: float, length: int = 11) -> str:
    filled_length = int(length * percent / 100)
    fraction = (percent / 100 * length) - filled_length
    has_half = fraction >= 0.5
    
    bar = '⬤' * filled_length
    if has_half and filled_length < length:
        bar += '◔'
        bar += '○' * (length - filled_length - 1)
    else:
        bar += '○' * (length - filled_length)
        
    return bar

def generate_aesthetic_progress_ui(task_info: dict, current_status: str = "Forwarding", percent: float = 0.0, footer_status: str = "FORWARDING") -> str:
    total = task_info.get("total", 0)
    success = task_info.get("success", 0)
    duplicate = task_info.get("duplicate", 0)
    deleted = task_info.get("deleted", 0)
    skipped = task_info.get("skipped", 0)
    filtered = task_info.get("filtered", 0)
    
    source_title = task_info.get("source_title", "Unknown Source")
    dest_title = task_info.get("dest_title_name", "Unknown Destination")
    
    if percent > 100.0: percent = 100.0

    bar_str = generate_bar(percent, length=11)

    text = (
        f"╔════❰ ғᴏʀᴡᴀʀᴅ sᴛᴀᴛᴜs ❱═❍⊱❁۪۪\n"
        f"║╭━━━━━━━━━━━━━━━➣\n"
        f"║┣⪼🕵 Tᴏᴛᴀʟ Msɢ : {total}\n"
        f"║┃\n"
        f"║┣⪼✅ sᴜᴄᴄᴇғᴜʟʟʏ Fᴡᴅ : {success}\n"
        f"║┃\n"
        f"║┣⪼👥 ᴅᴜᴘʟɪᴄᴀᴛᴇ Msɢ : {duplicate}\n"
        f"║┃\n"
        f"║┣⪼🗑 ᴅᴇʟᴇᴛᴇᴅ Msɢ : {deleted}\n"
        f"║┃\n"
        f"║┣⪼🪆 Sᴋɪᴘᴘᴇᴅ Msɢ : {skipped}\n"
        f"║┃\n"
        f"║┣⪼🔁 Fɪʟᴛᴇʀᴇᴅ Msɢ : {filtered}\n"
        f"║┃\n"
        f"║┣⪼📊 Cᴜʀʀᴇɴᴛ Sᴛᴀᴛᴜs: {current_status}\n"
        f"║┃\n"
        f"║┣⪼🔁 Source: {source_title}\n"
        f"║┃\n"
        f"║┣⪼📊 Destination : {dest_title}\n"
        f"║┃\n"
        f"║┣⪼𖨠 Pᴇʀᴄᴇɴᴛᴀɢᴇ: {percent:.1f} %\n"
        f"║╰━━━━━━━━━━━━━━━➣\n"
        f"╚════❰ {footer_status} ❱══❍⊱❁۪۪\n"
        f"〘{bar_str}〙 {percent:.1f}%"
    )
    return f"<pre><code>{text}</code></pre>"

PROMO_NAMES_RAW = [
    "Cloud Station", "TamilMob", "LinkZz", "ONAAMovies", "Hdhub4u", "HDHub4u", "Hub4u", "HDHub", "HDHu", "Cinevood", "Vegamovies", "Bollyflix", "1XBET", "Melbet", "Olamovies", "MoviesMod", "Khatrimaza", "9xmovies", "Desiremovies", "HubFlix", "Bolly4u", "Bolly2tolly", "Filmyzilla", "Tamilrockers", "JioRockers", "Kuttymovies", "Moviesda", "4kHdHub",
    "KatMovieHD", "KatMovies", "MoviesFlix", "MoviesVerse", "MoviesVerseHD", "MoviesRulz", "MovieRulz", "TamilYogi", "TamilMV", "TamilGun", "TamilBlasters", "TamilPrint", "Tamilian", "Isaimini", "KuttyWeb", "SSRMovies", "SSRMovie", "TeluguWap", "Ibomma", "Movierulz", "Filmypur", "Filmy4wap", "Filmywap", "FilmyMeet", "MoviesPapa", "MoviesBaba", "MoviesJoy", "MoviesNation", "MoviesCrown", "MoviesCounter", "MoviesDrive", "Moviezwap", "MoviezWap", "Mp4Moviez", "World4uFree", "9xflix", "DownloadHub", "DownloadHub4u", "HDMoviesHub", "HDMovieArea", "HDMovie14", "HDMovie2", "HubMovies", "BollyShare", "BollyRulez", "Bolly4Wap", "BollyZone", "BollyWoodMovies", "Cinevez", "CineHub", "Cineplex", "CineBinge", "FilmHub", "FilmBolly", "MovieBox", "MovieBoxPro", "MovieVerse", "MovieRaja", "MoviePanda", "MovieKing", "MoviePapa", "MovieMaza", "MovieDokan", "MoviezAdda", "Bollyflix4u", "Filmyzilla4u", "MoviesModHD", "LinkZ", "4KHDHub"
]

# Deduplicate promotional names case-insensitively
_seen_promo = set()
PROMO_NAMES = []
for _pname in PROMO_NAMES_RAW:
    _plower = _pname.lower()
    if _plower not in _seen_promo:
        _seen_promo.add(_plower)
        PROMO_NAMES.append(_pname)

PROMO_DOMAINS_SUFFIX = r"(?:\.(?:com|in|to|org|net|me|live|cc|vip|tv|nl|eu|is|pro|tech|info|xyz|app|site|club|link|top|world|online|hub|store|ws|biz|click|fun|trade|icu|cfd|lol))?"
PROMO_SPLIT_WORDS = [
    "cloud", "station", "tamil", "mob", "link", "zz", "onaa", "movies", "hd", "hub", "4u", "hu",
    "cine", "vood", "vega", "bolly", "flix", "1xbet", "melbet", "ola", "mod", "khatri", "maza",
    "9x", "desire", "2tolly", "filmy", "zilla", "rockers", "jio", "kutty", "da", "4k", "kat",
    "verse", "rulz", "yogi", "mv", "gun", "blasters", "print", "ian", "isaimini", "web",
    "ssr", "telugu", "wap", "ibomma", "pur", "meet", "papa", "baba", "joy", "nation", "crown",
    "counter", "drive", "zwap", "mp4", "world", "free", "area", "14", "2", "share", "zone",
    "wood", "vez", "plex", "binge", "box", "pro", "raja", "panda", "king", "dokan", "adda"
]

def _build_promo_regex():
    patterns = []
    for name in PROMO_NAMES:
        lower_name = name.lower().replace(" ", "")
        segments = []
        pos = 0
        while pos < len(lower_name):
            matched = False
            for w in sorted(PROMO_SPLIT_WORDS, key=len, reverse=True):
                if lower_name[pos:].startswith(w):
                    segments.append(re.escape(w))
                    pos += len(w)
                    matched = True
                    break
            if not matched:
                segments.append(re.escape(lower_name[pos]))
                pos += 1
        inner_pat = r'[-_.\s]*'.join(segments)
        pat = r'(?:\[|\(|\{)?@?' + inner_pat + PROMO_DOMAINS_SUFFIX + r'(?:\]|\)|\})?'
        patterns.append(pat)
    patterns.sort(key=len, reverse=True)
    return re.compile(r'(?<![a-zA-Z0-9])(?:' + '|'.join(patterns) + r')(?![a-zA-Z0-9])', re.IGNORECASE)

PROMO_NAME_REGEX = _build_promo_regex()

# ==============================================================================
# --- MEDIA FILTERING & SANITISATION ENGINE ---
# ==============================================================================

# Strict Blocklist Rule A: All 'Part' Keyword Split Files (001 to 999) - with or without extension
# e.g., *.part001.ext, *part001.ext, * part001.ext, *.part001, part001 to part999
BLOCK_PART_REGEX = re.compile(
    r"part[._\s-]?(?:00[1-9]|0[1-9]\d|[1-9]\d{2})(?!\d)",
    re.IGNORECASE
)

# Watermark Removal Regex (HDHub4u, Hub4u, HDHub, HDHu)
WATERMARK_CLEAN_REGEX = re.compile(
    r"(?i)(?:[@#]?\b(?:hdhub4u|hub4u|hdhub|hdhu)\b(?:[._-]?(?:com|org|net|in|top)\b)?|[\[\({][^\]\)}]*?(?:hdhub4u|hub4u|hdhub|hdhu)[^\]\)}]*?[\]\)}])"
)

def clean_promotional_watermarks(text: str) -> str:
    """
    Cleans target promotional watermarks (HDHub4u, Hub4u, HDHub, HDHu) and
    surrounding brackets/tags, collapsing multiple spaces and trimming whitespace.
    """
    if not text:
        return ""
    cleaned = WATERMARK_CLEAN_REGEX.sub('', text)
    cleaned = re.sub(r'(?:\s*-\s*){2,}', ' - ', cleaned)
    cleaned = re.sub(r'[\s\-_–—|]+(?=\.[a-zA-Z0-9]+)', '', cleaned)
    cleaned = re.sub(r'^\s*[-_–—|:.,\s]+', '', cleaned)
    cleaned = re.sub(r'\s*[-_–—|:.,\s]+$', '', cleaned)
    cleaned = re.sub(r'\s+(\.[a-zA-Z0-9]+(?:\.\d{2,4})?)', r'\1', cleaned)
    cleaned = re.sub(r'\.{2,}', '.', cleaned)
    cleaned = re.sub(r'[ \t]{2,}', ' ', cleaned).strip()
    return cleaned

def is_standalone_subtitle_file(filename: str) -> bool:
    """
    Identifies standalone subtitle files ending with .srt (case-insensitive).
    """
    if not filename:
        return False
    return filename.strip().lower().endswith(".srt") or bool(re.search(r"\.srt$", filename.strip(), re.IGNORECASE))

def should_drop_file(filename: str) -> tuple[bool, str]:
    """
    Checks if a candidate filename matches the strict blocklist.
    Returns (should_drop: bool, reason: str).
    """
    if not filename:
        return False, ""
    fn = filename.strip()
    if is_standalone_subtitle_file(fn):
        return True, "standalone_subtitle_srt"
    if BLOCK_PART_REGEX.search(fn):
        return True, "part_keyword_split"
    return False, ""

def extract_telegram_file_names(message) -> list[str]:
    """
    Inspects actual Telegram document metadata (DocumentAttributeFilename) across
    document, video, audio, animation, and raw MTProto attributes, as well as text/caption.
    """
    names = []
    if not message:
        return names

    # 1. Inspect Pyrogram media attributes & DocumentAttributeFilename
    for media_type in ("document", "video", "audio", "animation"):
        media = getattr(message, media_type, None)
        if media:
            fn = getattr(media, "file_name", None)
            if fn and isinstance(fn, str) and fn.strip():
                names.append(fn.strip())
            attrs = getattr(media, "attributes", None) or []
            for attr in attrs:
                if isinstance(attr, raw.types.DocumentAttributeFilename) and getattr(attr, "file_name", None):
                    names.append(attr.file_name.strip())
                elif getattr(attr, "file_name", None) and isinstance(attr.file_name, str):
                    names.append(attr.file_name.strip())

    # 2. Inspect raw MTProto message attributes if present
    raw_obj = getattr(message, "_raw", None) or getattr(message, "media", None)
    if raw_obj:
        doc = getattr(raw_obj, "document", None)
        if doc and hasattr(doc, "attributes"):
            for attr in getattr(doc, "attributes", []):
                if isinstance(attr, raw.types.DocumentAttributeFilename) and getattr(attr, "file_name", None):
                    names.append(attr.file_name.strip())
                elif getattr(attr, "file_name", None) and isinstance(attr.file_name, str):
                    names.append(attr.file_name.strip())

    # 3. Caption / text lines inspection fallback (ONLY when the message carries a file).
    #    A text post that merely mentions "English.srt" must never be treated as a subtitle file.
    has_media = any(getattr(message, t, None) for t in ("document", "video", "audio", "animation"))
    if not names and has_media:
        if getattr(message, "caption", None):
            cap_str = message.caption.html if hasattr(message.caption, "html") else str(message.caption)
            for line in cap_str.splitlines():
                line_clean = re.sub(r'<[^>]+>', '', line).strip()
                if line_clean:
                    names.append(line_clean)
        elif getattr(message, "text", None):
            txt_str = message.text.html if hasattr(message.text, "html") else str(message.text)
            for line in txt_str.splitlines():
                line_clean = re.sub(r'<[^>]+>', '', line).strip()
                if line_clean:
                    names.append(line_clean)

    return list(dict.fromkeys(names))

def is_message_blocked(message) -> tuple[bool, str, str]:
    """
    Inspects Telegram document metadata (DocumentAttributeFilename) and evaluates against
    the strict blocklist. Returns (is_blocked: bool, reason: str, matched_name: str).
    """
    if not message:
        return False, "", ""
    candidates = extract_telegram_file_names(message)
    for fn in candidates:
        dropped, reason = should_drop_file(fn)
        if dropped:
            return True, reason, fn
    return False, "", ""

UNAMBIGUOUS_EXTS = r'mkv|mp4|webm|m4v|flv|wmv|m4a|flac|7z'
DELIMITED_ONLY_EXTS = r'avi|ts|avc|mp3|aac|wav|opus|ogg|zip|rar|tar|iso|apk|pdf'
ALL_MEDIA_EXTS = UNAMBIGUOUS_EXTS + r'|' + DELIMITED_ONLY_EXTS

# 1. Match split files (.001, .002, etc.) for ANY known extension, even if glued to letters/domains (e.g. Commkv.001)
SPLIT_EXT_REGEX = re.compile(
    r'^(?P<stem>.*?)(?:[\.\s_\-]+|(?<=[\)\]\}_>\'\"a-zA-Z0-9]))(?P<ext>' + ALL_MEDIA_EXTS + r')(?P<split>\.\d{2,4})(?P<closing>\s*(?:</[^>]+>)*\s*)$',
    re.IGNORECASE
)

# 2. Match ANY extension preceded by dot, space, underscore, hyphen, or bracket/quote
# E.g. .mkv,  mkv, _mkv, -mkv, ]mkv, .avi,  avi, .ts,  ts, .mp4,  mp4
DELIM_EXT_REGEX = re.compile(
    r'^(?P<stem>.*?)(?:[\.\s_\-]+|(?<=[\)\]\}_>\'\"]))(?P<ext>' + ALL_MEDIA_EXTS + r')(?P<closing>\s*(?:</[^>]+>)*\s*)$',
    re.IGNORECASE
)

# 3. Match unambiguous extensions even if glued directly to promo domain or letters (e.g. Commkv, Bollyflixmp4)
UNAMBIGUOUS_TAIL_REGEX = re.compile(
    r'^(?P<stem>.*?)(?P<ext>' + UNAMBIGUOUS_EXTS + r')(?P<closing>\s*(?:</[^>]+>)*\s*)$',
    re.IGNORECASE
)

# 4. Generic fallback with dot
GENERIC_EXT_REGEX = re.compile(
    r'^(?P<stem>.*?)(?P<ext>\.[a-zA-Z][a-zA-Z0-9]{1,4})(?P<split>\.\d{2,4})?(?P<closing>\s*(?:</[^>]+>)*\s*)$',
    re.IGNORECASE
)

def balance_html_tags(html: str) -> str:
    """
    Ensures HTML tags are balanced in proper LIFO nesting order and strips orphan closing tags.
    Handles 'b', 'i', 'code', 'u', 's', 'pre', 'a'.
    """
    if not html:
        return ""
    tag_pattern = re.compile(r'<(/?)([a-zA-Z0-9]+)(?:\s+[^>]*)?>', re.IGNORECASE)
    valid_tags = {'b', 'i', 'code', 'u', 's', 'pre', 'a'}
    stack = []
    output = []
    last_idx = 0
    for m in tag_pattern.finditer(html):
        is_close = bool(m.group(1))
        tag = m.group(2).lower()
        if tag not in valid_tags:
            continue
        output.append(html[last_idx:m.start()])
        last_idx = m.end()
        if not is_close:
            stack.append(tag)
            output.append(m.group(0))
        else:
            for i in range(len(stack) - 1, -1, -1):
                if stack[i] == tag:
                    while len(stack) > i + 1:
                        pop_t = stack.pop()
                        output.append(f"</{pop_t}>")
                    stack.pop()
                    output.append(f"</{tag}>")
                    break
    output.append(html[last_idx:])
    while stack:
        pop_t = stack.pop()
        output.append(f"</{pop_t}>")
    return "".join(output)

def parse_media_extension_and_split(text: str):
    m = SPLIT_EXT_REGEX.search(text)
    if not m:
        m = DELIM_EXT_REGEX.search(text)
    if not m:
        m = UNAMBIGUOUS_TAIL_REGEX.search(text)
    if not m:
        m = GENERIC_EXT_REGEX.search(text)
    if m:
        stem = m.group("stem")
        ext = m.group("ext")
        if ext and not ext.startswith("."):
            ext = "." + ext.lower()
        split = m.groupdict().get("split") or ""
        closing = m.groupdict().get("closing") or ""
        if stem:
            # Strip trailing promotional domain residue from stem (e.g. .Com, .in, .org)
            stem = re.sub(r'(?i)\.(?:com|in|to|org|net|me|xyz|site|club|app|top|biz|info|cc)$', '', stem)
        return stem or "", ext or "", split or "", closing or ""
    return text, "", "", ""

# Quality regex: 2160p, 1080p, 720p, 480p, 360p, 1440p, 4k, 8k
QUALITY_REGEX = re.compile(r'\b(2160p|1080p|720p|480p|360p|1440p|4k|8k)\b', re.IGNORECASE)


# Hyperlink & domain regex for caption cleaning
LINK_PATTERN = re.compile(r'<a\s+[^>]*href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
PROMO_DOMAINS = [
    r't\.me', r'telegram\.me', r'telegram\.dog', r'1xbet', r'melbet', r'vegamovies', r'bollyflix',
    r'hdhub4u', r'moviesmod', r'filmyzilla', r'khatrimaza', r'desiremovies', r'9xmovies',
    r'katmovie', r'moviesflix', r'moviesverse', r'movierulz', r'tamilmv', r'tamilrockers',
    r'isaimini', r'kuttyweb', r'ssrmovies', r'ibomma', r'filmypur', r'moviesdrive', r'mp4moviez',
    r'world4ufree', r'downloadhub', r'cinevez', r'cinehub', r'cinevood', r'linkzz', r'bit\.ly',
    r'tinyurl\.com', r'cutt\.ly', r'shorturl\.at'
]
PROMO_DOMAIN_REGEX = re.compile(r'https?://(?:[a-zA-Z0-9_-]+\.)*(?:' + '|'.join(PROMO_DOMAINS) + r')(?::\d+)?(?:/[^\s"\'>]*)?', re.IGNORECASE)
PROMO_PHRASES_REGEX = re.compile(r'\b(?:join|subscribe|telegram|channel|group|backup|click here|download now|direct link|update channel|official|powered by|credit|credits|uploaded by|shared by)\b', re.IGNORECASE)

PROMO_LINE_REGEX = re.compile(
    r'(?i)^\s*(?:[⚜️✨🌟👉🔹🔸🔻🔺➡️✔️📢🔗]\s*)*'
    r'(?:powered\s*by|uploaded\s*by|shared\s*by|posted\s*by|credits?|join|subscribe|telegram\s*channel|backup\s*channel|official\s*channel|main\s*channel|contact)'
    r'(?:\s*[:\-–—]\s*|\s+).*$',
    re.IGNORECASE
)

MD_LINK_PATTERN = re.compile(r'\[([^\]]+)\]\((https?://[^\)]+)\)')

SMALL_CAPS_MAP = str.maketrans({
    'ᴀ': 'a', 'ʙ': 'b', 'ᴄ': 'c', 'ᴅ': 'd', 'ᴇ': 'e', 'ғ': 'f', 'ɢ': 'g', 'ʜ': 'h',
    'ɪ': 'i', 'ᴊ': 'j', 'ᴋ': 'k', 'ʟ': 'l', 'ᴍ': 'm', 'ɴ': 'n', 'ᴏ': 'o', 'ᴘ': 'p',
    'ǫ': 'q', 'ʀ': 'r', 's': 's', 'ᴛ': 't', 'ᴜ': 'u', 'ᴠ': 'v', 'ᴡ': 'w', 'x': 'x',
    'ʏ': 'y', 'ᴢ': 'z'
})

def normalize_fancy_unicode(text: str) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize('NFKD', text)
    return normalized.translate(SMALL_CAPS_MAP)

PROMO_PHRASE_EXPANDED = re.compile(
    r'\b(?:must\s*)?join\b|'
    r'\b(?:subscribe|sub)\b|'
    r'\b(?:telegram|tg)\s*(?:channel|group|link|bot)\b|'
    r'\b(?:backup|official|main|update|daily)\s*(?:channel|group)\b|'
    r'\b(?:powered\s*by|uploaded\s*by|shared\s*by|posted\s*by|credits?)\b|'
    r'\b(?:click\s*here|download\s*now|direct\s*link)\b',
    re.IGNORECASE
)

LUCIFER_TITLE_TAG_REGEX = re.compile(r"""^<a\s+[^>]*href=['"]https?://t\.me/luciferdatabase['"][^>]*>(.*?)</a>$""", re.IGNORECASE)

def clean_promotional_hyperlinks(text_html: str) -> str:
    if not text_html:
        return ""

    # 0. Unwrap full-line markdown links where title contains nested brackets: [title](url)
    lines = text_html.split('\n')
    unwrapped_lines = []
    for line in lines:
        stripped = line.strip()
        m_full = re.match(r'^\s*\[(?P<anchor>(?:[^\[\]]|\[[^\]]*\])*)\]\((?P<url>https?://[^\s\)]+)\)\s*$', stripped)
        if m_full:
            anc = m_full.group('anchor').strip()
            href = m_full.group('url').strip()
            if anc.startswith(r'\[') and anc.endswith(r'\]'):
                anc = anc[2:-2].strip()
            plain_anc = re.sub(r'<[^>]+>', '', anc).strip()
            norm_anc = normalize_fancy_unicode(plain_anc)
            _, ext, _, _ = parse_media_extension_and_split(plain_anc)
            is_promo_anc = (
                bool(PROMO_PHRASE_EXPANDED.search(norm_anc)) or 
                bool(re.search(r'^@[a-zA-Z0-9_]+$', plain_anc)) or
                bool(re.search(r'(?i)\b(?:powered\s*by|botz|update|channel|join|link)\b', norm_anc))
            )
            if is_promo_anc:
                continue
            if ext:
                leading = line[:len(line) - len(line.lstrip())]
                unwrapped_lines.append(leading + anc)
            elif (PROMO_DOMAIN_REGEX.search(href) or re.search(r'(?i)\b(?:t\.me|telegram\.me|telegram\.dog)\b', href)):
                continue
            else:
                unwrapped_lines.append(line)
        else:
            unwrapped_lines.append(line)
    text_html = '\n'.join(unwrapped_lines)

    # 1. Unwrap raw markdown links [anchor](url)
    def replace_md_link(match):
        anchor = match.group(1).strip()
        href = match.group(2).strip()
        plain_anchor = re.sub(r'<[^>]+>', '', anchor).strip()
        norm_anchor = normalize_fancy_unicode(plain_anchor)
        cleaned_anchor = clean_promotional_names(plain_anchor).strip()
        _, ext, _, _ = parse_media_extension_and_split(plain_anchor)
        is_promo_anchor = (
            bool(PROMO_PHRASE_EXPANDED.search(norm_anchor)) or 
            bool(re.search(r'^@[a-zA-Z0-9_]+$', plain_anchor)) or
            cleaned_anchor == "" or
            bool(re.match(r'^[⚜️✨🌟👉🔹🔸🔻🔺➡️✔️📢🔗➥➔➜➤➢►▶⏩🔔🏷📌🎬🍿🔥⚡:\-\[\]\(\)\s\\/]*$', cleaned_anchor))
        )
        if is_promo_anchor:
            return ""
        if not ext and (PROMO_DOMAIN_REGEX.search(href) or re.search(r'(?i)\b(?:t\.me|telegram\.me|telegram\.dog)\b', href)):
            return ""
        return anchor

    text_html = re.compile(r'\[+((?:[^\[\]]|\[[^\]]*\])+)\]+\((https?://[^\)]+)\)').sub(replace_md_link, text_html)

    # 2. Unwrap HTML links <a href="url">anchor</a>
    def replace_html_link(match):
        href = match.group(1).strip()
        anchor = match.group(2).strip()
        plain_anchor = re.sub(r'<[^>]+>', '', anchor).strip()
        norm_anchor = normalize_fancy_unicode(plain_anchor)
        cleaned_anchor = clean_promotional_names(plain_anchor).strip()
        _, ext, _, _ = parse_media_extension_and_split(plain_anchor)
        is_promo_anchor = (
            bool(PROMO_PHRASE_EXPANDED.search(norm_anchor)) or 
            bool(re.search(r'^@[a-zA-Z0-9_]+$', plain_anchor)) or
            cleaned_anchor == "" or
            bool(re.match(r'^[⚜️✨🌟👉🔹🔸🔻🔺➡️✔️📢🔗➥➔➜➤➢►▶⏩🔔🏷📌🎬🍿🔥⚡:\-\[\]\(\)\s\\/]*$', cleaned_anchor))
        )
        if is_promo_anchor:
            return ""
        if not ext and (PROMO_DOMAIN_REGEX.search(href) or re.search(r'(?i)\b(?:t\.me|telegram\.me|telegram\.dog)\b', href)):
            return ""
        return anchor

    cleaned = LINK_PATTERN.sub(replace_html_link, text_html)
    cleaned = PROMO_DOMAIN_REGEX.sub("", cleaned)
    cleaned = re.sub(r'(?i)(?:https?://)?\b(?:t\.me|telegram\.me|telegram\.dog)/(?!luciferdatabase\b|RequestLuciferDatabase\b)[a-zA-Z0-9_+\-/?=]+', '', cleaned)
    cleaned = re.sub(r'https?://(?=[\s\.,;:\-\(\)\[\]]|$)', '', cleaned)
    cleaned = re.sub(r'(?i)\b(?:join|link|channel|backup channel|official channel)\s*:\s*', '', cleaned)
    return cleaned



def clean_promotional_names(text: str) -> str:
    if not text:
        return ""
    res = clean_promotional_watermarks(text)
    res = PROMO_NAME_REGEX.sub(" ", res)
    res = re.sub(r'(\.)\s*[\.\-_]\s*', r'\1', res)
    res = re.sub(r'([-_])\s*[-_]\s*', r'\1', res)
    res = re.sub(r'\s*-\s*(?=\.(?:' + ALL_MEDIA_EXTS + r'))', '', res, flags=re.IGNORECASE)
    res = re.sub(r'\s*\.\s*(?=\.(?:' + ALL_MEDIA_EXTS + r'))', '', res, flags=re.IGNORECASE)
    res = re.sub(r' {2,}', ' ', res)
    return res.strip()

def strip_existing_media_footers(caption: str) -> str:
    """
    Strips pre-existing footers (File Size, Join links, and ANY Powered By / Uploaded By / Credits
    promotions regardless of source bot, Unicode fonts, emojis, HTML, or markdown formatting).
    """
    if not caption:
        return ""
    # Strip any file size line (e.g. 💾 Size: 3.12 GB)
    caption = re.sub(r'(?im)^\s*💾?\s*(?:size|file\s*size)\s*[:\-–—]?\s*[^\n]*$', '', caption)
    # Strip any join/link promotional line
    caption = re.sub(r'(?im)^\s*[🔗👉📢\s]*(?:join|link|channel|backup)\b[^\n]*$', '', caption)
    # Strip any Powered By / Uploaded By / Shared By / Credits line
    caption = re.sub(r'(?im)^\s*[⚜️✨🌟👉🔹🔸🔻🔺➡️✔️📢🔗\s]*(?:powered\s*by|uploaded\s*by|shared\s*by|posted\s*by|credits?)\s*[:\-–—]?\s*[^\n]*$', '', caption)
    # Strip any residual Powered By with markdown or HTML links
    caption = re.sub(r'\n*\s*⚜️?\s*(?:powered\s*by|uploaded\s*by|shared\s*by|posted\s*by|credits?)\s*[:\-–—]?\s*(?:<a\s+[^>]*>)?\[?[^\]\n]*\]?(?:</a>)?(?:\([^\)\n]*\))?[^\n]*', '', caption, flags=re.IGNORECASE)
    # Strip any lingering @luciferdatabase footers
    caption = re.sub(r'\n*\s*🔗\s*Join\s*@luciferdatabase[^\n]*', '', caption, flags=re.IGNORECASE)
    caption = re.sub(r'\n*\s*⚜️\s*Powered\s*By\s*:\s*(?:<a\s+[^>]*>)?\[?\s*@luciferdatabase\s*\]?(?:</a>)?[^\n]*', '', caption, flags=re.IGNORECASE)
    caption = re.sub(r'\n{3,}', '\n\n', caption).strip()
    return caption

def format_file_size(size_bytes: int | float) -> str:
    try:
        n = float(size_bytes)
    except Exception:
        return "0 B"
    if n <= 0:
        return "0 B"
    if n < 1024:
        return f"{int(n)} B"
    elif n < 1024 * 1024:
        return f"{n / 1024:.2f} KB"
    elif n < 1024 * 1024 * 1024:
        return f"{n / (1024 * 1024):.2f} MB"
    else:
        return f"{n / (1024 * 1024 * 1024):.2f} GB"

def append_media_footer(caption: str, file_size_bytes: int = 0) -> str:
    if not caption:
        caption = ""
    # Lucifer Cloud Engine templates already carry Size + the official footer.
    # Never strip/re-append them: doing so deleted the Join line and duplicated Size.
    if is_lucifer_cloud_engine_caption(caption):
        return caption
    # Strip any pre-existing footer to prevent duplication across retries/fallbacks/targets
    caption = strip_existing_media_footers(caption)

    powered_by_link = '<a href="https://t.me/luciferdatabase">[@luciferdatabase]</a>'

    if file_size_bytes > 0:
        size_str = format_file_size(file_size_bytes)
        footer = f"\n\n💾 Size: {size_str}\n\n⚜️ Powered By : {powered_by_link}"
    else:
        footer = f"\n\n⚜️ Powered By : {powered_by_link}"

    # Enforce Telegram 1024-character caption limit
    if len(caption) + len(footer) > 1024:
        avail = 1024 - len(footer)
        caption = balance_html_tags(caption[:avail].rstrip())
        while len(caption) + len(footer) > 1024 and avail > 0:
            avail -= (len(caption) + len(footer) - 1024)
            caption = balance_html_tags(caption[:avail].rstrip())

    return f"{caption}{footer}"

def prepare_caption_fallback(caption: str, file_size_bytes: int = 0) -> str:
    if is_lucifer_cloud_engine_caption(caption):
        cap = process_lucifer_cloud_engine_caption(caption)
        plain = re.sub(r'<[^>]+>', '', cap).strip()
        return plain
    caption = strip_existing_media_footers(caption)
    plain = re.sub(r'<[^>]+>', '', caption).strip()
    
    if file_size_bytes > 0:
        footer = f"\n\n💾 Size: {format_file_size(file_size_bytes)}\n\n⚜️ Powered By : [@luciferdatabase]"
    else:
        footer = f"\n\n⚜️ Powered By : [@luciferdatabase]"
    if len(plain) + len(footer) > 1024:
        avail = 1024 - len(footer)
        plain = plain[:avail].rstrip()
    return f"{plain}{footer}"


def sanitize_filename(filename: str) -> str:
    if not filename: return "unnamed_file.dat"
    filename = re.sub(r'[:]', "-", filename)
    filename = re.sub(r'[\\/*?"<>|]', "", filename)
    
    stem, ext, split_suffix, _ = parse_media_extension_and_split(filename)

    # Replace underscores with spaces
    stem = stem.replace('_', ' ')

    # Remove promotional website/channel names and target watermarks
    stem = clean_promotional_watermarks(stem)
    stem = clean_promotional_names(stem)

    # Strip leading @usernames and leading promo brackets
    while True:
        old_stem = stem
        stem = re.sub(r'^\s*@[a-zA-Z0-9_]+\s*', '', stem)
        m_lead = re.match(r'^\s*(?:\[(.*?)\]|\((.*?)\))\s*', stem)
        if m_lead:
            bracket_content = m_lead.group(1) or m_lead.group(2) or ""
            if re.match(r'^(?:S\d+|E\d+|S\d+E\d+|Season\s*\d+|Episode\s*\d+|\d{4}|Hindi|English|Tamil|Telugu|Dual\s*Audio|Multi\s*Audio|HEVC|H\.?265|H\.?264|AAC|DDP|x264|x265|2160p|1080p|720p|480p|4K|8K)$', bracket_content.strip(), re.IGNORECASE):
                pass
            else:
                stem = stem[m_lead.end():]
        if old_stem == stem:
            break

    stem = re.sub(r'(@[a-zA-Z0-9_]+)\s*$', '', stem)
    stem = stem.rstrip(' .-')

    if ext:
        final_name = f"{stem}{ext}{split_suffix}"
    else:
        final_name = stem
    final_name = re.sub(r' {2,}', ' ', final_name).strip()
    return final_name or "unnamed_file.dat"

def _process_media_line(line_html: str) -> tuple[str, bool]:
    stem, ext, split_suffix, closing_tags = parse_media_extension_and_split(line_html)
    if not ext:
        return line_html, False

    line_stem = stem.replace('_', ' ')
    line_stem = clean_promotional_watermarks(line_stem)
    line_stem = clean_promotional_names(line_stem)

    while True:
        old_stem = line_stem
        line_stem = re.sub(r'^((?:<[^>]+>)*\s*)@[a-zA-Z0-9_]+(\s*)', r'\1', line_stem)
        m_lead = re.match(r'^((?:<[^>]+>)*\s*)(?:\[(.*?)\]|\((.*?)\))(\s*)', line_stem)
        if m_lead:
            bracket_content = m_lead.group(2) or m_lead.group(3) or ""
            if re.match(r'^(?:S\d+|E\d+|S\d+E\d+|Season\s*\d+|Episode\s*\d+|\d{4}|Hindi|English|Tamil|Telugu|Dual\s*Audio|Multi\s*Audio|HEVC|H\.?265|H\.?264|AAC|DDP|x264|x265|2160p|1080p|720p|480p|4K|8K)$', bracket_content.strip(), re.IGNORECASE):
                pass
            else:
                line_stem = line_stem[:m_lead.start()] + m_lead.group(1) + line_stem[m_lead.end():]
        if old_stem == line_stem:
            break

    line_stem = re.sub(r'(@[a-zA-Z0-9_]+)(\s*(?:</[^>]+>)*\s*)$', r'\2', line_stem)
    line_stem = line_stem.rstrip(' .-')
    final_line = f"{line_stem}{ext}{split_suffix}{closing_tags}"
    final_line = re.sub(r' {2,}', ' ', final_line).strip()
    return final_line, True

def sanitize_cloud_filename(raw_fname: str) -> str:
    """
    Sanitises a filename inside Lucifer Cloud Engine format:
    Unwraps markdown/HTML links, strips promotional watermarks & foreign tags,
    and preserves legitimate technical media brackets.
    """
    m_html = re.search(r'<a\s+[^>]*>(.*?)</a>', raw_fname, flags=re.IGNORECASE | re.DOTALL)
    if m_html:
        raw_fname = m_html.group(1).strip()
    m_md = re.search(r'\[(.*?)\]\((https?://[^\)]+)\)', raw_fname)
    if m_md:
        raw_fname = m_md.group(1).strip()

    stem, ext, split_suffix, closing_tags = parse_media_extension_and_split(raw_fname)
    if not ext:
        stem = raw_fname
        ext = ""

    stem = WATERMARK_CLEAN_REGEX.sub('', stem)
    stem = re.sub(r'^\s*@[a-zA-Z0-9_]+\s*', '', stem)

    while True:
        old = stem
        m_lead = re.match(r'^\s*(?:\[(.*?)\]|\((.*?)\))\s*', stem)
        if m_lead:
            content = (m_lead.group(1) or m_lead.group(2) or "").strip()
            if re.match(r'^(?:S\d+|E\d+|S\d+E\d+|Season\s*\d+|Episode\s*\d+|\d{4}|Hindi|English|Tamil|Telugu|Dual\s*Audio|Multi\s*Audio|HEVC|H\.?265|H\.?264|AAC|DDP|x264|x265|2160p|1080p|720p|480p|4K|8K)$', content, re.IGNORECASE):
                pass
            else:
                stem = stem[m_lead.end():]
        if old == stem:
            break

    stem = re.sub(r'(@[a-zA-Z0-9_]+)\s*$', '', stem)
    stem = stem.rstrip(' .-')
    stem = re.sub(r' {2,}', ' ', stem).strip()
    return f"{stem}{ext}{split_suffix}{closing_tags}"

def is_lucifer_cloud_engine_caption(text: str) -> bool:
    """
    Detects whether an incoming caption is in the Lucifer Cloud Engine format.
    Signatures:
      - '🎬 File Name:' or 'File Name:'
      - Box/divider '━━━━━━━━━━━━━━━━━━━' or '💾 DB ID:' or '[@LuciferDatabase]' or '@RequestLuciferDatabase' or '⚖️ Size:'
    """
    if not text:
        return False
    has_fn = bool(re.search(r'(?i)(?:🎬\s*)?file\s*name\s*:', text))
    has_cloud_sig = bool(
        '━━━━━━━━━━━━━━━━━━━' in text or
        re.search(r'(?i)\bDB\s*ID\s*:\s*\[?@LuciferDatabase\]?', text) or
        '@RequestLuciferDatabase' in text or
        '@LuciferDatabase' in text or
        re.search(r'(?i)⚖️\s*Size\s*:', text)
    )
    return has_fn and has_cloud_sig

def process_lucifer_cloud_engine_caption(text_html: str) -> str:
    """
    Processes captions generated by Lucifer Cloud Engine:
      1. Preserves the full cinematic template structure:
         - Separator lines ('━━━━━━━━━━━━━━━━━━━')
         - DB ID, Size, Format, Codec, Resolution, Video, HDR, Audio, Season, Episode
         - Official contact/request lines: @LuciferDatabase, @RequestLuciferDatabase
      2. Cleans the File Name line:
         - Removes external promotional watermarks/tags/brackets (HDHub4u, Hub4u, etc.)
         - Wraps the cleaned media filename with the official Lucifer hyperlink:
           <a href="https://t.me/luciferdatabase">{cleaned_filename}</a>
      3. Strips foreign promo footers or links (e.g. Movies Botz, third-party channels).
      4. Appends the royal verified footer at the bottom:
         ⚜️ Powered By : <a href="https://t.me/luciferdatabase">[@luciferdatabase]</a>
      5. Does NOT append an extra redundant '💾 Size:' footer since size is already present in the template.
    """
    if not text_html:
        return ""

    lines = text_html.split('\n')
    output_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if output_lines and output_lines[-1] != "":
                output_lines.append("")
            continue

        # 1. File Name line
        m_fn = re.match(r'^(?P<prefix>.*?🎬?\s*File\s*Name\s*:\s*)(?P<fname>.+)$', stripped, flags=re.IGNORECASE)
        if m_fn:
            raw_fname = m_fn.group('fname').strip()
            cleaned_fname = sanitize_cloud_filename(raw_fname)
            cleaned_fname = re.sub(r'<[^>]+>', '', cleaned_fname).strip()
            linked_fname = f'<a href="https://t.me/luciferdatabase">{cleaned_fname}</a>'
            output_lines.append(f"🎬 File Name: {linked_fname}")
            continue

        # 2. Check if line is a foreign or existing Powered By / Uploaded By / Credits line
        if re.search(r'(?i)^\s*[⚜️✨🌟👉🔹🔸🔻🔺➡️✔️📢🔗\s]*(?:powered\s*by|uploaded\s*by|shared\s*by|posted\s*by|credits?)\s*[:\-–—]', stripped):
            continue

        # 3. Check for foreign promotional telegram links (preserve official LuciferDatabase & RequestLuciferDatabase)
        if re.search(r'(?i)\b(?:t\.me|telegram\.me|telegram\.dog)\b', stripped):
            if not ('@LuciferDatabase' in stripped or 'LuciferDatabase' in stripped or 'RequestLuciferDatabase' in stripped):
                continue

        # 4. Check for foreign promo line regex (unless it's an official Lucifer channel line)
        if not ('@LuciferDatabase' in stripped or 'RequestLuciferDatabase' in stripped or 'DB ID:' in stripped):
            norm_stripped = normalize_fancy_unicode(stripped)
            clean_pfx = re.sub(r'^[\s\[\(⚜️✨🌟👉🔹🔸🔻🔺➡️✔️📢🔗➥➔➜➤➢►▶⏩🔔🏷📌🎬🍿🔥⚡:\-–—]+', '', norm_stripped)
            if PROMO_LINE_REGEX.match(norm_stripped) or PROMO_LINE_REGEX.match(clean_pfx):
                continue

        # 5. Clean watermarks from line preserving formatting
        cleaned_line = WATERMARK_CLEAN_REGEX.sub('', line)
        cleaned_line = re.sub(r' {2,}', ' ', cleaned_line).strip()
        output_lines.append(cleaned_line)

    powered_by_footer = '⚜️ Powered By : <a href="https://t.me/luciferdatabase">[@luciferdatabase]</a>'
    result = '\n'.join(output_lines).strip()
    result = f"{result}\n{powered_by_footer}"
    result = balance_html_tags(result)
    return result

# 🚀 SMART CAPTION LOGIC
def _link_first_meaningful_line(lines):
    """Fallback: hyperlink the first meaningful line when no media extension is present."""
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        plain = re.sub(r'<[^>]+>', '', stripped).strip()
        if len(plain) < 4:
            continue
        if re.search(r'(?i)https?://|(?:^|\s)t\.me/|^@[A-Za-z0-9_]+$', plain):
            continue
        if PROMO_LINE_REGEX.match(normalize_fancy_unicode(plain)):
            continue
        lines[idx] = f'<a href="https://t.me/luciferdatabase">{stripped}</a>'
        break
    return lines


def smart_caption(text_html, file_size_bytes=0, link_fallback=False):
    if not text_html: return ""
    
    # 0. Specialized Lucifer Cloud Engine format handling
    if is_lucifer_cloud_engine_caption(text_html):
        return process_lucifer_cloud_engine_caption(text_html)

    # 0. Clean promotional watermarks and hidden promotional links & URLs
    text_html = clean_promotional_watermarks(text_html)
    text_html = clean_promotional_hyperlinks(text_html)

    # 1. Strip pre-existing footers (any Powered By, Size, or Join links)
    text_html = strip_existing_media_footers(text_html)

    # 2. Process multiline captions preserving formatting
    lines = text_html.split('\n')
    transformed = False
    media_idx = -1

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        stripped_clean = LUCIFER_TITLE_TAG_REGEX.sub(r'\1', stripped)
        new_line, ok = _process_media_line(stripped_clean)
        if ok:
            leading = line[:len(line) - len(line.lstrip())]
            lines[i] = f'{leading}<a href="https://t.me/luciferdatabase">{new_line}</a>'
            transformed = True
            media_idx = i
            break

    if not transformed:
        text_clean = LUCIFER_TITLE_TAG_REGEX.sub(r'\1', text_html)
        new_text, ok = _process_media_line(text_clean)
        if ok:
            lines = [f'<a href="https://t.me/luciferdatabase">{new_text}</a>']
            media_idx = 0
            transformed = True
        else:
            lines = [clean_promotional_names(l.replace('_', ' ')) for l in lines]
            if link_fallback:
                lines = _link_first_meaningful_line(lines)
    else:
        for j in range(len(lines)):
            if j != media_idx:
                lines[j] = clean_promotional_names(lines[j].replace('_', ' '))

    # Filter out promotional lines, raw @usernames, or empty punctuation lines
    filtered_lines = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            if filtered_lines and filtered_lines[-1] != "":
                filtered_lines.append("")
            continue

        if idx == media_idx and transformed:
            filtered_lines.append(line)
            continue

        plain = re.sub(r'<[^>]+>', '', stripped).strip()
        if not plain:
            continue

        norm_plain = normalize_fancy_unicode(plain)
        clean_prefix = re.sub(r'^[\s\[\(⚜️✨🌟👉🔹🔸🔻🔺➡️✔️📢🔗➥➔➜➤➢►▶⏩🔔🏷📌🎬🍿🔥⚡:\-–—]+', '', norm_plain)

        if (
            PROMO_LINE_REGEX.match(norm_plain) or 
            PROMO_LINE_REGEX.match(clean_prefix) or
            PROMO_PHRASE_EXPANDED.search(norm_plain) or
            PROMO_PHRASE_EXPANDED.search(clean_prefix)
        ):
            continue

        if PROMO_DOMAIN_REGEX.search(plain) or re.search(r'(?i)\b(?:t\.me|telegram\.me|telegram\.dog)\b', plain):
            continue

        if re.match(r'^\s*@[a-zA-Z0-9_]+\s*$', plain):
            continue

        cleaned_plain = clean_promotional_names(plain)
        cleaned_norm = clean_promotional_names(norm_plain)
        if (
            re.match(r'^[⚜️✨🌟👉🔹🔸🔻🔺➡️✔️📢🔗➥➔➜➤➢►▶⏩🔔🏷📌🎬🍿🔥⚡:\-\[\]\(\)\s\\/]*$', cleaned_plain) or
            re.match(r'^[⚜️✨🌟👉🔹🔸🔻🔺➡️✔️📢🔗➥➔➜➤➢►▶⏩🔔🏷📌🎬🍿🔥⚡:\-\[\]\(\)\s\\/]*$', cleaned_norm)
        ):
            continue

        filtered_lines.append(line)

    result = '\n'.join(filtered_lines)
    result = re.sub(r' {2,}', ' ', result).strip()
    result = balance_html_tags(result)
    
    # 3. Append footer if file size provided
    if file_size_bytes > 0:
        result = append_media_footer(result, file_size_bytes)
        
    return result



def apply_text_format(caption: str, formats) -> str:
    """Bold/Italic may wrap hyperlinks; <code> cannot contain a link, so Mono strips tags.
    Cloud Engine templates are never reformatted."""
    if not caption or not formats:
        return caption
    if is_lucifer_cloud_engine_caption(caption):
        return caption
    if "Italic" in formats:
        caption = f"<i>{caption}</i>"
    if "Bold" in formats:
        caption = f"<b>{caption}</b>"
    if "Mono" in formats:
        if "<a " in caption:
            caption = re.sub(r'<[^>]+>', '', caption)
        caption = f"<code>{caption}</code>"
    return caption


async def check_link_restriction(user_id, link_text):
    clean_text = link_text.replace("https://", "").replace("http://", "").replace("t.me/", "").replace("c/", "")
    
    if "-" in clean_text:
        clean_text = clean_text.split("-")[0].strip()
        
    parts = clean_text.split("/")
    
    is_private = False
    chat_id = None
    msg_id = None

    try:
        if "t.me/b/" in link_text:
            return False, "🤖 **Bot Link:** Content availability depends on the bot."
            
        if "t.me/c/" in link_text:
            is_private = True
            chat_id = int("-100" + parts[0])
            if len(parts) > 1 and parts[-1].isdigit():
                msg_id = int(parts[-1])
        else:
            chat_id = parts[0]
            if len(parts) > 1 and parts[-1].isdigit():
                msg_id = int(parts[-1])
            
    except Exception as e:
        return None, f"⚠️ **Could not analyze link.** Error: {e}"

    is_temp_client = False
    check_client = app 
    
    if is_private:
        if user_id in USER_CLIENTS and USER_CLIENTS[user_id].is_connected:
            check_client = USER_CLIENTS[user_id]
            is_temp_client = False
        else:
            user_session = await db.get_session(user_id)
            if not user_session:
                return None, "🔒 **Private Link:** Please /login to verify restrictions."
            
            api_id = await db.get_api_id(user_id)
            api_hash = await db.get_api_hash(user_id)
            check_client = Client(f"check_{user_id}_{int(time.time())}", session_string=user_session, api_id=api_id, api_hash=api_hash, no_updates=True, ipv6=False, in_memory=True)
            is_temp_client = True

    is_restricted = False
    status_msg = ""
    
    try:
        if is_temp_client:
            await check_client.connect()
            
        if msg_id:
            msg = await check_client.get_messages(chat_id, msg_id)
            if getattr(msg.chat, "has_protected_content", False) or getattr(msg, "has_protected_content", False):
                is_restricted = True
                status_msg = "🔒 **Source is RESTRICTED** (Will use Download Mode)"
            else:
                is_restricted = False
                status_msg = "🔓 **Source is PUBLIC/UNRESTRICTED** (Will use Fast Forward)"
        else:
            chat = await check_client.get_chat(chat_id)
            if getattr(chat, "has_protected_content", False):
                is_restricted = True
                status_msg = "🔒 **Channel is RESTRICTED** (Will use Download Mode)"
            else:
                is_restricted = False
                status_msg = "🔓 **Channel is PUBLIC/UNRESTRICTED**"
            
    except Exception as e:
        if "CHANNEL_PRIVATE" in str(e) or "USER_NOT_PARTICIPANT" in str(e):
            status_msg = "⚠️ **Private Chat:** I can't check yet (You need to join first)."
        else:
            status_msg = f"⚠️ **Check Failed:** `{str(e)[:30]}...`"
    finally:
        if is_temp_client and check_client:
            try: await check_client.disconnect()
            except Exception: pass
        
    return is_restricted, status_msg
    
async def split_file_python(file_path, chunk_size=2000*1024*1024):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(io_executor, _split_file_smart, file_path, chunk_size)

def _split_file_smart(file_path, chunk_size):
    file_path = Path(file_path)
    if not file_path.exists():
        return []

    file_size = os.path.getsize(file_path)
    if file_size <= chunk_size:
        return [file_path]

    part_num = 0
    parts = []
    buffer_size = 32 * 1024 * 1024 
    
    # Generate splits as raw numeric chunks after extension (e.g. Movie.mkv.001)
    # Fully whitelisted and compliant with Telegram forwarder split rules
    try:
        with open(file_path, 'rb') as source:
            while True:
                part_name = file_path.parent / f"{file_path.name}.{part_num + 1:03d}"
                current_chunk_size = 0
                with open(part_name, 'wb') as dest:
                    while current_chunk_size < chunk_size:
                        read_size = min(buffer_size, chunk_size - current_chunk_size)
                        data = source.read(read_size)
                        if not data: break
                        dest.write(data)
                        current_chunk_size += len(data)
                if current_chunk_size == 0:
                    if part_name.exists(): part_name.unlink()
                    break
                parts.append(part_name)
                part_num += 1
        return parts
    except Exception:
        for p in parts:
            try:
                if p.exists(): p.unlink()
            except Exception:
                pass
        raise

def progress(current, total, task_uuid, typ):
    if task_uuid and CANCEL_FLAGS.get(task_uuid):
        raise Exception("CANCELLED_BY_USER")
    
    key = f"{task_uuid}:{typ}"
    now = time.time()
    if key not in PROGRESS:
        PROGRESS[key] = {
            "current": 0, "total": int(total), "percent": 0.0,
            "last_time": now, "last_current": 0, "speed": 0.0, "eta": None
        }
    rec = PROGRESS[key]
    rec["current"] = int(current)
    rec["total"] = int(total)
    if total > 0:
        rec["percent"] = (current / total) * 100.0
    dt = now - rec["last_time"]
    if dt >= 1 or current == total:
        delta_bytes = current - rec["last_current"]
        if dt <= 0: dt = 0.1
        speed = delta_bytes / dt
        rec["speed"] = speed
        rec["last_time"] = now
        rec["last_current"] = current
        if speed > 0 and total > current:
            rec["eta"] = (total - current) / speed
            
async def downstatus(client: Client, status_message: Message, chat, index: int, total_count: int, header_text: str = "", task_uuid: str = None, user_id: int = None):
    original_msg_id = status_message.id if status_message else 0
    original_chat_id = chat
    key = f"{task_uuid}:down" 
    last_text = ""
    while True:
        current_msg_id = original_msg_id
        current_chat_id = original_chat_id
        task_info = {}
        if task_uuid and user_id:
            task_info = ACTIVE_PROCESSES.get(user_id, {}).get(task_uuid, {})
            current_msg_id = task_info.get("status_msg_id", original_msg_id)
            current_chat_id = task_info.get("status_chat_id", original_chat_id)
            
        if task_uuid and CANCEL_FLAGS.get(task_uuid): break

        rec = PROGRESS.get(key)
        if not rec:
            await asyncio.sleep(1)
            continue
        if rec["current"] == rec["total"] and rec["total"] > 0:
            break
            
        percent = rec.get("percent", 0)
        speed_str = f"{_pretty_bytes(rec.get('speed', 0))}/s"
        size_str = f"{_pretty_bytes(rec.get('current', 0))} / {_pretty_bytes(rec.get('total', 0))}"
        eta_str = get_readable_time(int(rec.get('eta', 0)) if rec.get('eta') else 0)

        current_action = f"📥 Downloading ({percent:.1f}%)\n║┣⪼🚀 Sᴘᴇᴇᴅ: {speed_str}\n║┣⪼💾 Sɪᴢᴇ: {size_str}\n║┣⪼⏳ ETA: {eta_str}"
        status_text = generate_aesthetic_progress_ui(task_info, current_action, percent, "DOWNLOADING")

        if not task_info.get("confirming_cancel"):
            if status_text != last_text or task_info.get("force_update_ui"):
                task_info["force_update_ui"] = False
                try:
                    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Cancel Task", callback_data=f"ask_cancel:{task_uuid}")]])
                    await client.edit_message_text(current_chat_id, current_msg_id, status_text, reply_markup=kb)
                    last_text = status_text
                except Exception:
                    pass
        
        total_size = rec.get("total", 0)
        if total_size > 0 and total_size < 50 * 1024 * 1024:
            await asyncio.sleep(8) 
        else:
            await asyncio.sleep(15)
            
async def upstatus(client: Client, status_message: Message, chat, index: int, total_count: int, header_text: str = "", task_uuid: str = None, user_id: int = None):
    original_msg_id = status_message.id if status_message else 0
    original_chat_id = chat
    key = f"{task_uuid}:up"
    last_text = ""
    while True:
        current_msg_id = original_msg_id
        current_chat_id = original_chat_id
        task_info = {}
        if task_uuid and user_id:
            task_info = ACTIVE_PROCESSES.get(user_id, {}).get(task_uuid, {})
            current_msg_id = task_info.get("status_msg_id", original_msg_id)
            current_chat_id = task_info.get("status_chat_id", original_chat_id)
            
        if task_uuid and CANCEL_FLAGS.get(task_uuid): break
        
        rec = PROGRESS.get(key)
        if not rec:
            await asyncio.sleep(1)
            continue
        if rec["current"] == rec["total"] and rec["total"] > 0:
            break
            
        percent = rec.get("percent", 0)
        speed_str = f"{_pretty_bytes(rec.get('speed', 0))}/s"
        size_str = f"{_pretty_bytes(rec.get('current', 0))} / {_pretty_bytes(rec.get('total', 0))}"
        eta_str = get_readable_time(int(rec.get('eta', 0)) if rec.get('eta') else 0)

        current_action = f"📤 Uploading ({percent:.1f}%)\n║┣⪼🚀 Sᴘᴇᴇᴅ: {speed_str}\n║┣⪼💾 Sɪᴢᴇ: {size_str}\n║┣⪼⏳ ETA: {eta_str}"
        status_text = generate_aesthetic_progress_ui(task_info, current_action, percent, "UPLOADING")

        if not task_info.get("confirming_cancel"):
            if status_text != last_text or task_info.get("force_update_ui"):
                task_info["force_update_ui"] = False
                try:
                    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Cancel Task", callback_data=f"ask_cancel:{task_uuid}")]])
                    await client.edit_message_text(current_chat_id, current_msg_id, status_text, reply_markup=kb)
                    last_text = status_text
                except Exception:
                    pass
        
        total_size = rec.get("total", 0)
        if total_size > 0 and total_size < 50 * 1024 * 1024:
            await asyncio.sleep(8) 
        else:
            await asyncio.sleep(15)
            
def get_message_type(msg: Message):
    if msg.document: return "Document"
    if msg.video: return "Video"
    if msg.animation: return "Animation"
    if msg.sticker: return "Sticker"
    if msg.voice: return "Voice"
    if msg.audio: return "Audio"
    if msg.photo: return "Photo"
    if msg.text: return "Text"
    return None

# ==============================================================================
# --- HANDLERS ---
# ==============================================================================

async def test_destination_access(client: Client, chat_id, thread_id=None, user_id=None):
    try:
        test_msg = await client.send_message(
            chat_id=chat_id,
            text="🔄 **Testing Destination Accessibility...**\n*(This message will self-destruct)*",
            reply_to_message_id=thread_id
        )
        await test_msg.delete()
        return True, "Success"
    except Exception as e:
        if user_id:
            try:
                u_client = await get_user_client(user_id)
                if u_client:
                    test_msg = await u_client.send_message(
                        chat_id=chat_id,
                        text="🔄 **Testing Destination Accessibility...**\n*(This message will self-destruct)*",
                        reply_to_message_id=thread_id
                    )
                    await test_msg.delete()
                    return True, "Success"
            except Exception as ue:
                return False, f"Bot error: {e} | User Client error: {ue}"
        return False, str(e)
        
@app.on_message(filters.command(["start"]) & filters.private & ~filters.bot)
async def send_start(client: Client, message: Message):
    if not message.chat or message.chat.type != enums.ChatType.PRIVATE:
        return
    user_id = message.from_user.id if message.from_user else 0
    if not user_id or getattr(message.from_user, "is_bot", False):
        return
    if not is_authorized(user_id):
        return await message.reply(f'⛔ <b>Access Denied!</b>\n\nThis bot is private and restricted to authorized administrators.\n\n🆔 <b>Your User ID:</b> <code>{user_id}</code>', quote=True)
    user_name = message.from_user.first_name
    
    # Save user non-blocking in background so start command responds instantly
    async def _save_user_bg():
        try:
            if not await db.is_user_exist(user_id):
                await db.add_user(user_id, user_name)
                print(f"New user {user_id} saved to database.") 
        except Exception as e:
            print(f"Failed to save user {user_id}: {e}")

    asyncio.create_task(_save_user_bg())
    asyncio.create_task(register_bot_commands(client))

    user_mention = getattr(message.from_user, "mention", None) or html.escape(message.from_user.first_name or "User")
    welcome_video_url = "https://holy-field-055f.lucifermotivational.workers.dev/0:/Google%20Flow%20%E2%80%93%20Sept%2004%20-%2016-28.mp4"
    
    # Check if user has an active session
    user_accounts = await db.get_user_accounts(user_id) if (db and hasattr(db, "get_user_accounts")) else []
    if user_accounts:
        active_acc = next((a for a in user_accounts if a.get('is_active')), user_accounts[0])
        acc_name = html.escape(active_acc.get('first_name', 'Active Session'))
        acc_phone = active_acc.get('phone', '')
        phone_part = f" ({acc_phone})" if acc_phone and acc_phone != 'Hidden' else ""
        session_info = (
            f"🟢 <b>Login Status:</b> <code>LOGGED IN ({acc_name}{phone_part})</code>\n"
            "✨ <i>All restricted downloads & forwarders are active and ready!</i>"
        )
    else:
        session_info = (
            "🔴 <b>Login Status:</b> <code>NOT LOGGED IN</code>\n"
            "👉 <i>For downloading restricted content, please /login first.</i>"
        )

    welcome_text = (
        f"<b>👋 Hi {user_mention}, I am Save Restricted Content Bot.</b>\n\n"
        f"{session_info}\n\n"
        "<b>Know how to use bot by - /help</b>"
    )
    
    buttons = [
        [InlineKeyboardButton("❣️ Developer", url = "https://t.me/LuciferOpenSource")],
        [InlineKeyboardButton('🔍 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ', url='https://t.me/LuciferOpenSourceDiscussionGroup'), InlineKeyboardButton('🤖 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/LuciferOpenSource')]
    ]

    try:
        await client.send_video(
            chat_id=message.chat.id, 
            video=welcome_video_url, 
            caption=welcome_text, 
            reply_markup=InlineKeyboardMarkup(buttons),
            reply_to_message_id=message.id
        )
    except Exception as e:
        try:
            await client.send_message(
                chat_id=message.chat.id,
                text=welcome_text,
                reply_markup=InlineKeyboardMarkup(buttons),
                reply_to_message_id=message.id
            )
        except Exception:
            plain_welcome = (
                f"👋 Hi {message.from_user.first_name or 'User'}, I am Save Restricted Content Bot.\n\n"
                "For downloading restricted content /login first.\n\n"
                "Know how to use bot by - /help"
            )
            await client.send_message(
                chat_id=message.chat.id,
                text=plain_welcome,
                reply_markup=InlineKeyboardMarkup(buttons),
                reply_to_message_id=message.id,
                parse_mode=None
            )

@app.on_message(filters.command(["help"]) & filters.private & ~filters.bot)
async def send_help(client: Client, message: Message):
    if not message.chat or message.chat.type != enums.ChatType.PRIVATE:
        return
    user_id = message.from_user.id if message.from_user else 0
    if not user_id or getattr(message.from_user, "is_bot", False):
        return
    if not is_authorized(user_id):
        return await message.reply('⛔ <b>Access Denied:</b> You are not authorized to use this bot.', quote=True)

    help_kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📥 Saved Sources", callback_data="ch_page:1:source_view:source"),
            InlineKeyboardButton("📤 Saved Destinations", callback_data="ch_page:1:dest_view:dest")
        ],
        [
            InlineKeyboardButton("🛰️ Active Watchers", callback_data="view_watchers_menu"),
            InlineKeyboardButton("⚙️ Live Tasks", callback_data="tasks_refresh_menu")
        ],
        [
            InlineKeyboardButton("❌ Close Guide", callback_data="close_menu")
        ]
    ])

    await client.send_message(
        message.chat.id,
        text=HELP_TXT,
        reply_markup=help_kb,
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True
    )

@app.on_callback_query(filters.regex(r"^tasks_refresh_menu$"))
async def tasks_refresh_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied", show_alert=True)
    user_tasks = ACTIVE_PROCESSES.get(user_id, {})
    if not user_tasks:
        return await query.answer("💤 No active tasks currently running.", show_alert=True)
    for task_uuid, info in list(user_tasks.items()):
        if CANCEL_FLAGS.get(task_uuid): continue
        info["needs_refresh"] = True
    await query.answer("✅ Active tasks refreshed!", show_alert=True)

PAGE_SIZE_WATCHERS = 20

def build_watchers_page_ui(user_watchers, page=0, is_admin_view=False):
    total = len(user_watchers)
    total_pages = max(1, math.ceil(total / PAGE_SIZE_WATCHERS))
    page = max(0, min(page, total_pages - 1))

    start_idx = page * PAGE_SIZE_WATCHERS
    end_idx = min(start_idx + PAGE_SIZE_WATCHERS, total)
    page_items = user_watchers[start_idx:end_idx]

    title = "📊 <b>Global Surveillance Mappings (Admin View):</b>\n\n" if is_admin_view else "📊 <b>Your Active Surveillance Channels (Watchers):</b>\n\n"
    text = title
    text += f"📑 <b>Page:</b> <code>{page + 1}/{total_pages}</code> • Total Watchers: <code>{total}</code>\n"
    text += "─────────────────────────\n\n"

    for rel_idx, w in enumerate(page_items):
        idx = start_idx + rel_idx + 1
        src_id = w['source_id']
        src_thread = w.get('source_thread')
        src_display = w.get('source_title') or str(src_id)
        th_info = f" (Topic: {src_thread})" if src_thread else ""

        targets = w.get('targets', [])
        if not targets and 'dest_id' in w:
            targets = [{"dest_id": w['dest_id'], "dest_thread": w.get('dest_thread'), "dest_title": w.get('dest_title')}]

        filters_list = w.get('allowed_types', ['All Media'])
        flt_str = ", ".join(filters_list)
        fmts = w.get('text_format', [])
        fmt_str = ", ".join(fmts) if fmts else "Default"
        delay_val = w.get('delay', 0)
        owner_info = f" | 👤 <code>{w.get('user_id')}</code>" if is_admin_view else ""

        text += f"<b>{idx}. 📥 {html.escape(src_display)}{th_info}</b>{owner_info}\n"
        text += f"   <code>{src_id}</code>\n"
        text += f"   🎛 Filters: {html.escape(flt_str)}\n"
        text += f"   📝 Format: {html.escape(fmt_str)}\n"
        text += f"   ⏱ Delay: {delay_val}s\n"
        text += f"   ⤵️ Targets ({len(targets)}):\n"

        for t in targets:
            dst_id = t.get('dest_id')
            dst_display = t.get('dest_title') or str(dst_id)
            dst_th = f" (Topic: {t['dest_thread']})" if t.get('dest_thread') else ""
            text += f"   • {html.escape(dst_display)}{dst_th} (<code>{dst_id}</code>)\n"

        text += "\n"

    nav_buttons = []
    if total_pages > 1:
        prev_page = page - 1 if page > 0 else total_pages - 1
        next_page = page + 1 if page < total_pages - 1 else 0
        admin_flag = 1 if is_admin_view else 0
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"watchers_pg:{prev_page}:{admin_flag}"))
        nav_buttons.append(InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data=f"watchers_pg:{page}:{admin_flag}"))
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"watchers_pg:{next_page}:{admin_flag}"))

    full_markup = []
    if nav_buttons:
        full_markup.append(nav_buttons)

    full_markup.append([
        InlineKeyboardButton("🛰️ New Watcher", callback_data="watch_manual"),
        InlineKeyboardButton("🗑 Unwatch All", callback_data="unwatch_all")
    ])
    full_markup.append([
        InlineKeyboardButton("📥 Save All WATCHERS Source Channels", callback_data="watchers_import_src"),
        InlineKeyboardButton("📤 Save All WATCHERS Destination Channels", callback_data="watchers_import_dst")
    ])
    full_markup.append([
        InlineKeyboardButton("📥 Saved Sources", callback_data="ch_page:1:source_view:source"),
        InlineKeyboardButton("📤 Saved Destinations", callback_data="ch_page:1:dest_view:dest")
    ])
    full_markup.append([
        InlineKeyboardButton("🔙 Back to Help", callback_data="back_to_help"),
        InlineKeyboardButton("❌ Close", callback_data="close_menu")
    ])

    return text, InlineKeyboardMarkup(full_markup)


@app.on_callback_query(filters.regex(r"^view_watchers_menu$"))
async def view_watchers_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied", show_alert=True)

    q_filter = {"$or": [{"user_id": user_id}, {"user_id": int(user_id)}, {"user_id": str(user_id)}]}
    user_watchers = await db.db.watchers.find(q_filter).to_list(length=None)

    if not user_watchers:
        empty_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛰️ Setup New Watcher", callback_data="watch_manual")],
            [InlineKeyboardButton("📥 Saved Sources", callback_data="ch_page:1:source_view:source"),
             InlineKeyboardButton("📤 Saved Destinations", callback_data="ch_page:1:dest_view:dest")],
            [InlineKeyboardButton("🔙 Back to Help", callback_data="back_to_help"),
             InlineKeyboardButton("❌ Close", callback_data="close_menu")]
        ])
        empty_text = (
            "💤 <b>No Active Watchers Found.</b>\n\n"
            "You don't have any channels currently being monitored in real-time.\n\n"
            "• Use <code>/watch &lt;Link&gt;</code> to set up a 24/7 auto-forwarder.\n"
            "• Or pick directly from your saved source channels!"
        )
        return await query.message.edit_text(
            empty_text,
            reply_markup=empty_kb,
            parse_mode=enums.ParseMode.HTML
        )

    text, markup = build_watchers_page_ui(user_watchers, page=0, is_admin_view=False)
    await query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^watchers_pg:(\d+)(?::(\d+))?$"))
async def watchers_page_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied", show_alert=True)

    page = int(query.matches[0].group(1))
    is_admin_flag = bool(int(query.matches[0].group(2) or 0))

    show_all = is_admin_flag and is_admin(user_id)
    user_watchers = await db.get_user_watchers(user_id, show_all=show_all)

    if not user_watchers:
        empty_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛰️ Setup New Watcher", callback_data="watch_manual")],
            [InlineKeyboardButton("📥 Saved Sources", callback_data="ch_page:1:source_view:source"),
             InlineKeyboardButton("📤 Saved Destinations", callback_data="ch_page:1:dest_view:dest")],
            [InlineKeyboardButton("🔙 Back to Help", callback_data="back_to_help"),
             InlineKeyboardButton("❌ Close", callback_data="close_menu")]
        ])
        empty_text = (
            "💤 <b>No Active Watchers Found.</b>\n\n"
            "You don't have any channels currently being monitored in real-time.\n\n"
            "• Use <code>/watch &lt;Link&gt;</code> to set up a 24/7 auto-forwarder.\n"
            "• Or pick directly from your saved source channels!"
        )
        return await query.message.edit_text(empty_text, reply_markup=empty_kb, parse_mode=enums.ParseMode.HTML)

    text, markup = build_watchers_page_ui(user_watchers, page=page, is_admin_view=is_admin_flag)
    try:
        await query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        if "MESSAGE_NOT_MODIFIED" not in str(e):
            logger.error(f"Error in watchers_page_callback: {e}")
    await query.answer()

@app.on_callback_query(filters.regex(r"^watchers_import_(src|dst)$"))
async def watchers_import_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied.", show_alert=True)

    ch_type = "source" if query.matches[0].group(1) == "src" else "dest"
    type_label = "SOURCE" if ch_type == "source" else "DESTINATION"

    lock_key = (user_id, ch_type)
    if lock_key in IMPORT_LOCKS:
        return await query.answer("⏳ Migration is already in progress for this channel type. Please wait...", show_alert=True)

    IMPORT_LOCKS.add(lock_key)
    try:
        await query.answer(f"⏳ Importing {type_label.lower()} channels from active watchers...", show_alert=False)

        stats = await db.import_watchers_channels(client, user_id, channel_type=ch_type)

        discovered = stats["discovered"]
        newly_saved = stats["newly_saved"]
        already_saved = stats["already_saved"]
        unresolved = stats["unresolved"]
        errors = stats["errors"]

        if discovered == 0:
            result_text = (
                f"💤 <b>NO ELIGIBLE {type_label} CHANNELS FOUND</b>\n"
                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                f"You do not have any active watcher routes referencing {type_label.lower()} channels to import.\n\n"
                f"• Use <code>/watch &lt;Link&gt;</code> to set up 24/7 channel monitoring.\n"
                f"• Or manually save channels using <code>/add{ch_type}channel</code>."
            )
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🛰️ Setup New Watcher", callback_data="watch_manual")],
                [InlineKeyboardButton("🔙 Back to Watchers", callback_data="view_watchers_menu"),
                 InlineKeyboardButton("❌ Close", callback_data="ch_close")]
            ])
            return await query.message.edit_text(result_text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)

        unresolved_note = ""
        if unresolved > 0:
            unresolved_note = (
                f"\n⚠️ <b>Inaccessible Channels ({unresolved}):</b>\n"
                f"Some channel titles could not be retrieved from Telegram because neither this bot nor your connected account has access.\n"
                f"<i>They have been saved with their IDs so your data is preserved. Real names will be updated automatically as soon as access is granted!</i>\n"
            )

        err_note = ""
        if errors:
            err_note = f"\n⚠️ <b>Migration Warnings:</b>\n" + "\n".join(f"• <code>{html.escape(e)}</code>" for e in errors[:3]) + "\n"

        result_text = (
            f"╔════❰ 🜏 WATCHERS MEMORY IMPORT ❱═❍⊱❁۪۪\n"
            f"║ 📂 <b>Type:</b> <b>{type_label} Channels</b>\n"
            f"╠═► 🔍 <b>Distinct Channels Discovered:</b> <code>{discovered}</code>\n"
            f"╠═► 💾 <b>Newly Saved to Memory:</b> <code>{newly_saved}</code>\n"
            f"╠═► ⏭️ <b>Already Saved (Skipped):</b> <code>{already_saved}</code>\n"
            f"╠═► ⚠️ <b>Unresolved Titles:</b> <code>{unresolved}</code>\n"
            f"╚══════════════════════════════════❍⊱❁۪۪\n"
            + unresolved_note
            + err_note
            + f"\n💎 <i>Your {type_label.lower()} channels are now safely stored in permanent memory for quick 1-tap setups!</i>"
        )

        view_cb = f"ch_page:1:{ch_type}_view:{ch_type}"
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"📋 View Saved {type_label.capitalize()} Channels", callback_data=view_cb)],
            [InlineKeyboardButton("🔙 Back to Watchers", callback_data="view_watchers_menu"),
             InlineKeyboardButton("❌ Close", callback_data="ch_close")]
        ])

        await query.message.edit_text(result_text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        logger.error(f"Error in watchers_import_callback: {e}", exc_info=True)
        try:
            await query.message.reply(f"❌ <b>Import Failed:</b> <code>{html.escape(str(e))}</code>", quote=True)
        except Exception:
            pass
    finally:
        IMPORT_LOCKS.discard(lock_key)

@app.on_callback_query(filters.regex(r"^back_to_help$"))
async def back_to_help_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied", show_alert=True)

    help_kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📥 Saved Sources", callback_data="ch_page:1:source_view:source"),
            InlineKeyboardButton("📤 Saved Destinations", callback_data="ch_page:1:dest_view:dest")
        ],
        [
            InlineKeyboardButton("🛰️ Active Watchers", callback_data="view_watchers_menu"),
            InlineKeyboardButton("⚙️ Live Tasks", callback_data="tasks_refresh_menu")
        ],
        [
            InlineKeyboardButton("❌ Close Guide", callback_data="close_menu")
        ]
    ])
    await query.message.edit_text(HELP_TXT, reply_markup=help_kb, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)


@app.on_message(filters.command(["toggledl", "toggledownl"]) & filters.private & ~filters.bot)
async def toggle_dl_command(client: Client, message: Message):
    if not message.chat or message.chat.type != enums.ChatType.PRIVATE:
        return
    user_id = message.from_user.id if message.from_user else 0
    if not is_authorized(user_id):
        return await message.reply('⛔ <b>Access Denied:</b> You are not authorized to use this bot.', quote=True)
    new_status = await db.toggle_dl_status()
    if new_status:
        await message.reply("✅ **Auto-Download is now ON.**\nBot will download files if direct fast-copy fails.")
    else:
        await message.reply("🚫 **Auto-Download is now OFF.**\nBot will ONLY direct-forward. If forwarding fails (restricted or floodwait), it will simply SKIP the file to save bandwidth.")

@app.on_message(filters.command(["task", "tasks", "progress"]) & filters.private & ~filters.bot)
async def task_refresh_handler(client: Client, message: Message):
    if not message.chat or message.chat.type != enums.ChatType.PRIVATE:
        return
    user_id = message.from_user.id if message.from_user else 0
    if not is_authorized(user_id):
        return await message.reply('⛔ <b>Access Denied:</b> You are not authorized to use this bot.', quote=True)
    user_tasks = ACTIVE_PROCESSES.get(user_id, {})
    if not user_tasks:
        return await message.reply("💤 **No active tasks running.**")
        
    for task_uuid, info in list(user_tasks.items()):
        if CANCEL_FLAGS.get(task_uuid): continue
        info["needs_refresh"] = True
    await message.reply("✅ **Refreshing... Your live progress message will pop up again shortly!**")

@app.on_message(filters.command(["cancel"]) & filters.private & ~filters.bot)
async def send_cancel(client: Client, message: Message):
    if not message.chat or message.chat.type != enums.ChatType.PRIVATE:
        return
    user_id = message.from_user.id if message.from_user else 0
    if not user_id or getattr(message.from_user, "is_bot", False):
        return
    if not is_authorized(user_id):
        return await message.reply('⛔ <b>Access Denied:</b> You are not authorized to use this bot.', quote=True)

    if user_id in PENDING_TASKS:
        del PENDING_TASKS[user_id]
        await message.reply("✅ **Setup process cancelled.** You can send a new link now.")
        return

    user_tasks = ACTIVE_PROCESSES.get(user_id, {})
    if not user_tasks:
        await message.reply("✅ **No active tasks to cancel.**\n\n*(Note: To remove a Watcher, please use the /watchers command and click Delete, or use /unwatch)*")
        return

    buttons = []
    for tid, info in list(user_tasks.items()):
        label = info.get("item", "Task")
        label_short = (label[:26] + "...") if len(label) > 29 else label
        buttons.append([InlineKeyboardButton(f"🛑 {label_short}", callback_data=f"ask_cancel:{tid}")])
    buttons.append([InlineKeyboardButton("🛑 Cancel ALL My Tasks", callback_data="ask_cancel_all")])
    buttons.append([InlineKeyboardButton("❌ Close Menu", callback_data="close_menu")])

    await message.reply(
        "**🚫 Cancel Tasks**\n\nSelect the task you want to cancel:",
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True
    )
    
@app.on_callback_query(filters.regex(r"^cancel_") | filters.regex(r"^cancel_task:") | filters.regex(r"^ask_cancel") | filters.regex(r"^resume_task:"))
async def cancel_callback(client: Client, query):
    user_id = query.from_user.id
    data = query.data

    if data == "cancel_setup":
        if user_id in PENDING_TASKS:
            del PENDING_TASKS[user_id]
        await query.message.edit("❌ **Task Setup Cancelled.**")
        return

    if data == "ask_cancel_all":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ YES, CANCEL ALL", callback_data="cancel_all")],
            [InlineKeyboardButton("❌ NO, GO BACK", callback_data="close_menu")]
        ])
        await query.message.edit("**⚠️ Are you sure you want to cancel ALL active tasks?**", reply_markup=kb)
        return

    if data == "cancel_all":
        if user_id in TASK_QUEUE:
            TASK_QUEUE[user_id].clear()
        
        user_tasks = list(ACTIVE_PROCESSES.get(user_id, {}).keys())
        if not user_tasks:
            await query.answer("No active tasks to cancel.", show_alert=True)
            try: await query.message.delete()
            except Exception: pass
            return
        for tid in user_tasks:
            CANCEL_FLAGS[tid] = True 
        await query.message.edit("**🛑 Cancelling ALL your tasks...**\n(This may take a moment to stop current downloads)")
        return

    if data.startswith("ask_cancel:"):
        task_uuid = data.split(":",1)[1]
        user_tasks = ACTIVE_PROCESSES.get(user_id, {})
        if task_uuid not in user_tasks:
            await query.answer("Task not found or already finished.", show_alert=True)
            try: await query.message.delete()
            except Exception: pass
            return
            
        user_tasks[task_uuid]["confirming_cancel"] = True
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ YES, CANCEL", callback_data=f"cancel_task:{task_uuid}")],
            [InlineKeyboardButton("❌ NO, RESUME", callback_data=f"resume_task:{task_uuid}")]
        ])
        await query.message.edit("⚠️ **Are you sure you want to cancel this task?**\n\n*(Background progress will pause updating here until you choose)*", reply_markup=kb)
        return

    if data.startswith("resume_task:"):
        task_uuid = data.split(":",1)[1]
        user_tasks = ACTIVE_PROCESSES.get(user_id, {})
        if task_uuid in user_tasks:
            user_tasks[task_uuid]["confirming_cancel"] = False
            user_tasks[task_uuid]["force_update_ui"] = True
            await query.answer("▶️ Task Resumed!", show_alert=False)
            if query.message.id != user_tasks[task_uuid].get("status_msg_id"):
                try: await query.message.delete()
                except Exception: pass
        else:
            await query.answer("Task already finished.", show_alert=True)
            try: await query.message.delete()
            except Exception: pass
        return

    if data.startswith("cancel_task:"):
        task_uuid = data.split(":",1)[1]
        user_tasks = ACTIVE_PROCESSES.get(user_id, {})
        if task_uuid not in user_tasks:
            await query.answer("Task not found or already finished.", show_alert=True)
            try: await query.message.delete()
            except Exception: pass
            return
        CANCEL_FLAGS[task_uuid] = True
        await query.message.edit(f"🛑 **Task cancelled:** `{user_tasks[task_uuid].get('item','Task')}`\nIt will stop shortly.")
        return
        
@app.on_callback_query(filters.regex("^close_menu"))
async def close_menu(client, query):
    try:
        await query.message.delete()
    except Exception:
        await query.answer("Menu closed.")

@app.on_message(filters.command(["pixel"]) & filters.private & ~filters.bot)
async def pixel_bypass_handler(client: Client, message: Message):
    if not message.chat or message.chat.type != enums.ChatType.PRIVATE:
        return
    user_id = message.from_user.id if message.from_user else 0
    if not is_authorized(user_id):
        return await message.reply('⛔ <b>Access Denied:</b> You are not authorized to use this bot.', quote=True)
    if len(message.command) < 2:
        return await message.reply(
            "**Usage:**\n`/pixel https://pixeldrain.com/u/xxxx`\n\n"
            "Or multiple comma-separated links:\n"
            "`/pixel link1,link2,link3`"
        )

    input_text = message.text.split(None, 1)[1]
    matches = re.findall(r"pixeldrain\.com/u/([a-zA-Z0-9_-]+)", input_text)
    
    if not matches:
        return await message.reply(
            "❌ **No valid Pixeldrain links found.**\n"
            "Please ensure the links follow the format: `https://pixeldrain.com/u/XXXX`"
        )

    lines = []
    for match in matches:
        orig = f"https://pixeldrain.com/u/{match}"
        byp = f"https://cdn.pixeldrain.eu.cc/{match}"
        lines.append(f"🔗 **Original:** {orig}\n🔓 **Bypassed:** `{byp}`\n")
        
    bypassed_text = "\n".join(lines)
    
    reply_text = (
        "✨ **Pixeldrain Bypass Successful!** ✨\n\n"
        "**📥 Bypassed Links:**\n\n"
        f"{bypassed_text}\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "🌐 **Original Bypass Website:** [Click Here](https://pixeldrain-bypass.gamedrive.org/)\n"
        "📜 **Userscript:** [Install Script](https://pixeldrain-bypass.gamedrive.org/pixeldrain-bypass.user.js)"
    )
    
    await message.reply(reply_text, disable_web_page_preview=True)

@app.on_message(filters.command(["status"]) & filters.private & ~filters.bot)
async def status_style_handler(client, message):
    if not message.chat or message.chat.type != enums.ChatType.PRIVATE:
        return
    user_id = message.from_user.id if message.from_user else 0
    if not is_admin(user_id):
        return await message.reply("⛔ <b>Access Denied:</b> This command is restricted to administrators.", quote=True)
    uptime_seconds = int(time.time() - BOT_START_TIME)
    uptime_str = get_readable_time(uptime_seconds)
    mem = psutil.virtual_memory().percent
    cpu = psutil.cpu_percent()
    
    total, used, free = shutil.disk_usage(".")
    disk_free = free / (1024**3)
    
    active_count = 0
    queue_list = []
    
    for uid, tasks in ACTIVE_PROCESSES.items():
        for t_id, info in tasks.items():
            active_count += 1
            src = info.get("source_title", "Source")
            dst = info.get("dest_title_name", "Destination")
            queue_list.append(f"• {src} → {dst}")
    
    watcher_count = await db.db.watchers.count_documents({}) if (db and db.db is not None) else 0
    queue_text = "\n".join(queue_list) if queue_list else "😴 No active downloads."
    
    auto_dl = "ON ✅" if await db.get_dl_status() else "OFF ❌"

    status_body = (
        f"🔰 SYSTEM DASHBOARD\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"⏱ Uptime: {uptime_str}\n"
        f"🧠 RAM: {mem}%  │  ⚙️ CPU: {cpu}% \n"
        f"💿 Disk Free: {disk_free:.1f} GB \n"
        f"🔄 Auto-Download: {auto_dl} \n\n"
        f"👀 Live Watchers: {watcher_count} running\n"
        f"📉 Active Downloads ({active_count}):\n"
        f"{queue_text}\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
    )
    await message.reply(f"<pre>{html.escape(status_body)}</pre>", quote=True, parse_mode=enums.ParseMode.HTML)
    
def build_redacted_log():
    """Copy bot.log with tokens, session strings and DB URIs removed."""
    src = Path("bot.log")
    if not src.exists():
        return None
    dst = Path("bot.log.redacted")
    try:
        text = src.read_text(encoding="utf-8", errors="replace")
        text = re.sub(r'mongodb(?:\+srv)?://[^\s\'"<>]+', 'mongodb://[REDACTED]', text)
        text = re.sub(r'(?i)\b(bot_token|api_hash|session_string|session_enc_key|db_uri)\b\s*[=:]\s*[^\s,;"\']+', r'\1=[REDACTED]', text)
        text = re.sub(r'\b\d{8,10}:[A-Za-z0-9_-]{30,}\b', '[BOT_TOKEN_REDACTED]', text)
        text = re.sub(r'\b[A-Za-z0-9_-]{250,}\b', '[LONG_SECRET_REDACTED]', text)
        dst.write_text(text, encoding="utf-8")
        return dst
    except Exception as e:
        print(f"⚠️ [LOG] Redaction failed: {e}")
        return None


@app.on_message(filters.command(["log"]) & filters.private & ~filters.bot)
async def send_log_handler(client: Client, message: Message):
    if not message.chat or message.chat.type != enums.ChatType.PRIVATE:
        return
    user_id = message.from_user.id if message.from_user else 0
    if not is_admin(user_id):
        return await message.reply("⛔ <b>Access Denied:</b> This command is restricted to administrators.", quote=True)
    redacted_log = build_redacted_log()
    if redacted_log:
        try:
            await message.reply_document(str(redacted_log), caption="📄 **Bot Logs (redacted)**\nSecrets and long tokens removed.")
        finally:
            try:
                redacted_log.unlink()
            except Exception:
                pass
    else:
        await message.reply("⚠️ Log file not found yet.")

async def build_bot_stats_ui(page: int = 1, page_size: int = 10):
    all_users_cursor = await db.get_all_users()
    users_list = []
    async for u in all_users_cursor:
        users_list.append(u)
        
    total_users = len(users_list)
    total_pages = max(1, math.ceil(total_users / page_size)) if total_users > 0 else 1
    
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    # Categorize and sort users
    # Priority: 0 = active tasks (running), 1 = logged in (idle), 2 = no session
    def user_sort_key(u):
        u_id = u.get("id", 0)
        has_tasks = bool(ACTIVE_PROCESSES.get(u_id, {}))
        has_session = bool(u.get("session"))
        if has_tasks:
            return (0, -(u_id or 0))
        elif has_session:
            return (1, -(u_id or 0))
        else:
            return (2, -(u_id or 0))

    sorted_users = sorted(users_list, key=user_sort_key)

    logged_in_count = sum(1 for u in sorted_users if u.get("session"))
    active_users_count = sum(1 for u in sorted_users if ACTIVE_PROCESSES.get(u.get("id"), {}))
    idle_users_count = logged_in_count - active_users_count
    no_session_count = total_users - logged_in_count
    total_active_tasks = sum(len(ACTIVE_PROCESSES.get(u.get("id"), {})) for u in sorted_users)

    # Slice for page
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_users)
    page_users = sorted_users[start_idx:end_idx]

    user_blocks = []
    num_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    for i, u in enumerate(page_users, start=start_idx + 1):
        u_id = u.get("id", 0)
        raw_name = u.get("name") or f"User:{u_id}"
        safe_name = html.escape(str(raw_name))
        u_tasks = ACTIVE_PROCESSES.get(u_id, {})
        has_session = bool(u.get("session"))

        pos_in_page = i - start_idx
        display_num = num_emojis[pos_in_page - 1] if 1 <= pos_in_page <= 10 else f"#{i}"

        if u_tasks:
            task_lines = []
            for t_id, info in u_tasks.items():
                src = html.escape(str(info.get("source_title", "Source")))
                dst = html.escape(str(info.get("dest_title_name") or info.get("dest_title") or "Destination"))
                curr = info.get("current", 0)
                tot = info.get("total", 0)
                pct = (curr / tot * 100) if tot > 0 else 0
                start_t = info.get("started", time.time())
                elapsed = time.time() - start_t
                eta_str = "Calculating..."
                if curr > 0 and elapsed > 0:
                    try:
                        eta_str = get_readable_time(int(((tot - curr) / (curr / elapsed))))
                    except Exception:
                        eta_str = "N/A"
                task_lines.append(f"      └ 🏃 <code>{src}</code> ➔ <code>{dst}</code> [{curr}/{tot} ({pct:.1f}%)] (ETA: {eta_str})")
            
            tasks_str = chr(10).join(task_lines)
            user_blocks.append(
                f"{display_num} 🟢 <b>{safe_name}</b> [<code>{u_id}</code>]\n"
                f"   └ ⚡ <b>Status:</b> ACTIVE ({len(u_tasks)} Task{'s' if len(u_tasks)>1 else ''})\n"
                f"{tasks_str}"
            )
        elif has_session:
            user_blocks.append(
                f"{display_num} 🟡 <b>{safe_name}</b> [<code>{u_id}</code>]\n"
                f"   └ 🔑 <b>Status:</b> LOGGED IN (IDLE 😴)"
            )
        else:
            user_blocks.append(
                f"{display_num} ⚪ <b>{safe_name}</b> [<code>{u_id}</code>]\n"
                f"   └ 🔒 <b>Status:</b> NO ACTIVE SESSION"
            )

    users_text = chr(10).join(user_blocks) if user_blocks else "<i>No registered users found in directory.</i>"

    users_plain = chr(10).join(re.sub(r'<[^>]+>', '', b) for b in user_blocks) if user_blocks else "No registered users found in directory."
    stats_body = (
        "👑 ROYAL INFILTRATOR BOT STATISTICS 👑\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        "🏛️ EXECUTIVE OVERVIEW:\n"
        f"• 👥 Total Registered: {total_users}\n"
        f"• 🔑 Logged-in Sessions: {logged_in_count}\n"
        f"• 🟢 Active Runners: {active_users_count}\n"
        f"• 🟡 Idle Standby: {idle_users_count}\n"
        f"• ⚪ Unauthenticated: {no_session_count}\n"
        f"• ⚡ Running Workloads: {total_active_tasks}\n\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"📜 USER DIRECTORY (Page {page}/{total_pages}):\n\n"
        f"{users_plain}\n\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"💎 Showing {start_idx + 1 if total_users else 0}–{end_idx} of {total_users} users • 10 Users/Page"
    )
    stats_msg = f"<pre>{html.escape(stats_body)}</pre>" 

    buttons = []
    if total_pages > 1:
        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton("◀️ Prev", callback_data=f"botstats_p:{page-1}"))
        nav_row.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data=f"botstats_p:{page}"))
        if page < total_pages:
            nav_row.append(InlineKeyboardButton("Next ▶️", callback_data=f"botstats_p:{page+1}"))
        buttons.append(nav_row)

    # 🚪 Admin Kick / Logout User Buttons for logged-in users on this page
    kick_buttons = []
    for pos, u in enumerate(page_users, start=1):
        u_id = u.get("id", 0)
        has_sess = bool(u.get("session")) or (u_id in USER_CLIENTS)
        if has_sess:
            raw_n = u.get("name") or str(u_id)
            short_n = html.escape(str(raw_n))[:10]
            kick_buttons.append(InlineKeyboardButton(f"🚪 Kick #{pos} ({short_n})", callback_data=f"kick_u:{u_id}:{page}"))
    
    # Place kick buttons in rows of 2
    for k_idx in range(0, len(kick_buttons), 2):
        buttons.append(kick_buttons[k_idx:k_idx + 2])

    buttons.append([
        InlineKeyboardButton("🔄 Refresh Stats", callback_data=f"botstats_p:{page}"),
        InlineKeyboardButton("❌ Close", callback_data="close_menu")
    ])

    markup = InlineKeyboardMarkup(buttons)
    return stats_msg, markup

@app.on_message(filters.command(["botstats"]) & filters.private & ~filters.bot)
async def bot_stats_handler(client: Client, message: Message):
    if not message.chat or message.chat.type != enums.ChatType.PRIVATE:
        return
    user_id = message.from_user.id if message.from_user else 0
    if not is_admin(user_id):
        return await message.reply("⛔ <b>Access Denied:</b> This command is restricted to administrators.", quote=True)
    
    wait = await message.reply("📊 <b>Retrieving royal system statistics...</b>", quote=True)
    text, markup = await build_bot_stats_ui(page=1)
    await wait.edit_text(text, reply_markup=markup, disable_web_page_preview=True)

@app.on_callback_query(filters.regex(r"^botstats_p:(\d+)"))
async def bot_stats_page_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id if query.from_user else 0
    if not is_admin(user_id):
        return await query.answer("⛔ Access Denied: This feature is restricted to administrators.", show_alert=True)
    
    try:
        page = int(query.matches[0].group(1))
    except (IndexError, ValueError):
        page = 1
        
    text, markup = await build_bot_stats_ui(page=page)
    try:
        await query.message.edit_text(text, reply_markup=markup, disable_web_page_preview=True)
        await query.answer(f"Page {page} loaded ⚡")
    except Exception:
        await query.answer("Stats are up to date! 🔄")
async def force_logout_user(target_id: int):
    target_id = int(target_id)
    if target_id in USER_CLIENTS:
        try:
            await USER_CLIENTS[target_id].stop()
        except Exception:
            pass
        USER_CLIENTS.pop(target_id, None)

    await db.set_session(target_id, session=None)
    await db.set_api_id(target_id, api_id=None)
    await db.set_api_hash(target_id, api_hash=None)
    try:
        await db.col.update_one(
            {'id': target_id},
            {'$set': {'accounts': [], 'active_account_id': None, 'session': None, 'api_id': None, 'api_hash': None}}
        )
    except Exception:
        pass

    user_procs = ACTIVE_PROCESSES.get(target_id, {})
    for tid in list(user_procs.keys()):
        CANCEL_FLAGS[tid] = True
    ACTIVE_PROCESSES.pop(target_id, None)

async def get_user_client(user_id: int, session_string: str = None) -> Client | None:
    if user_id in USER_CLIENTS:
        client = USER_CLIENTS[user_id]
        if getattr(client, "is_connected", False):
            return client
        try:
            await client.start()
            return client
        except Exception:
            try: await client.stop()
            except Exception: pass
            USER_CLIENTS.pop(user_id, None)

    session_str = session_string or await db.get_session(user_id)
    if not session_str:
        return None

    u_api = await db.get_api_id(user_id) or API_ID
    u_hash = await db.get_api_hash(user_id) or API_HASH

    new_client = Client(
        f"userbot_{user_id}_{int(time.time())}",
        session_string=session_str,
        api_id=u_api,
        api_hash=u_hash,
        device_model="Telegram Desktop",
        system_version="Windows 11 x64",
        app_version="5.6.1 x64",
        lang_code="en",
        workers=4,
        ipv6=False,
        in_memory=True
    )
    if "user_watcher_handler" in globals():
        new_client.add_handler(MessageHandler(globals()["user_watcher_handler"]))
    try:
        await new_client.start()
        USER_CLIENTS[user_id] = new_client
        return new_client
    except Exception as e:
        print(f"Failed to start user client for {user_id}: {e}")
        return None

@app.on_callback_query(filters.regex(r"^kick_u:(\d+):(\d+)"))
async def kick_user_callback(client: Client, query: CallbackQuery):
    admin_id = query.from_user.id if query.from_user else 0
    if not is_admin(admin_id):
        return await query.answer("⛔ Access Denied: Administrator permission required.", show_alert=True)
    
    target_id = int(query.matches[0].group(1))
    page = int(query.matches[0].group(2))

    await query.answer(f"⏳ Terminating session for user {target_id}...", show_alert=False)
    await force_logout_user(target_id)

    text, markup = await build_bot_stats_ui(page=page)
    try:
        await query.message.edit_text(text, reply_markup=markup, disable_web_page_preview=True)
    except Exception:
        pass
    await query.answer(f"✅ User {target_id} logged out & session kicked!", show_alert=True)

@app.on_message(filters.command(["kickuser", "logoutuser", "kicksession"]) & filters.private & ~filters.bot)
async def kick_user_command(client: Client, message: Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        return await message.reply("⛔ <b>Access Denied:</b> This command is restricted to administrators.", quote=True)

    args = message.command
    if len(args) < 2:
        return await message.reply(
            "⚠️ <b>Usage:</b> <code>/kickuser &lt;user_id&gt;</code>\n\n"
            "Terminates the user's active session, stops their userbot instance, and clears session data.",
            quote=True
        )

    try:
        target_id = int(args[1].strip())
    except ValueError:
        return await message.reply("⚠️ Invalid User ID. Must be a numeric Telegram ID.", quote=True)

    status_msg = await message.reply(f"⏳ <i>Terminating session for user <code>{target_id}</code>...</i>", quote=True)
    await force_logout_user(target_id)
    await status_msg.edit(
        f"✅ <b>User Successfully Kicked & Logged Out!</b>\n\n"
        f"• <b>Target User ID:</b> <code>{target_id}</code>\n"
        f"• <b>Session Status:</b> Terminated & Cleared from Database\n"
        f"• <b>Running Tasks:</b> Cancelled",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📊 View Updated Stats", callback_data="botstats_p:1")]])
    )


        
# ==============================================================================
# --- LOGIN / LOGOUT ---
# ==============================================================================

@app.on_message(filters.private & ~filters.forwarded & filters.command(["logout"]))
async def logout(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else 0
    if not is_authorized(user_id):
        return await message.reply('⛔ <b>Access Denied:</b> You are not authorized to use this bot.', quote=True)

    accounts = await db.get_user_accounts(user_id)
    if not accounts:
        if user_id in USER_CLIENTS:
            try: await USER_CLIENTS[user_id].stop()
            except Exception: pass
            USER_CLIENTS.pop(user_id, None)
        await db.set_session(user_id, session=None)
        await db.set_api_id(user_id, api_id=None)
        await db.set_api_hash(user_id, api_hash=None)
        return await message.reply("ℹ️ <b>You are not currently logged in.</b>", quote=True)

    if len(accounts) > 1:
        active_acc = next((a for a in accounts if a.get('is_active')), accounts[0])
        logout_text = (
            "🚨 <b>Logout & Account Management</b>\n\n"
            f"You currently have <b>{len(accounts)}</b> saved account(s).\n"
            f"🟢 <b>Active Account:</b> <b>{html.escape(active_acc.get('first_name', 'User'))}</b> (<code>{active_acc.get('phone', 'N/A')}</code>)\n\n"
            "Choose an action:"
        )
        logout_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚪 Logout Active Account Only", callback_data="logout_act_confirm")],
            [InlineKeyboardButton("🔥 Logout All Saved Accounts", callback_data="logout_all_confirm")],
            [InlineKeyboardButton("❌ Cancel", callback_data="acc_close")]
        ])
        return await message.reply(logout_text, reply_markup=logout_kb, quote=True)

    status_msg = await message.reply("📡 <b>Connecting to Telegram to terminate session...</b>", quote=True)
    if user_id in USER_CLIENTS:
        try: await USER_CLIENTS[user_id].stop()
        except Exception: pass
        USER_CLIENTS.pop(user_id, None)

    await db.set_session(user_id, session=None)
    await db.set_api_id(user_id, api_id=None)
    await db.set_api_hash(user_id, api_hash=None)
    await db.col.update_one({'id': int(user_id)}, {'$set': {'accounts': [], 'active_account_id': None}})
    await status_msg.edit("✅ <b>Logout Complete!</b> ♦\nYour session has been safely disconnected and removed.")

async def build_accounts_ui(user_id: int):
    accounts = await db.get_user_accounts(user_id)
    if not accounts:
        text = (
            "👥 <b>Multi-Account Manager</b>\n\n"
            "❌ <i>No Telegram accounts currently connected.</i>\n\n"
            "Connecting an account allows the bot to forward restricted content, download protected files, and run live watchers."
        )
        buttons = [
            [InlineKeyboardButton("🔑 Add Account (String Session - Zero SMS)", callback_data="login_choice_string")],
            [InlineKeyboardButton("📱 Add Account (Phone Number + OTP)", callback_data="login_choice_phone")],
            [InlineKeyboardButton("❌ Close", callback_data="acc_close")]
        ]
        return text, InlineKeyboardMarkup(buttons)

    active_acc = next((a for a in accounts if a.get('is_active')), accounts[0])
    lines = [
        "👥 <b>Multi-Account Manager</b>\n",
        f"📊 <b>Total Accounts:</b> <code>{len(accounts)}</code>",
        f"🟢 <b>Active Account:</b> <b>{html.escape(active_acc.get('first_name', 'User'))}</b> (<code>{active_acc.get('phone', 'N/A')}</code>)\n",
        "👇 <i>Tap an account to switch to it, or remove old accounts:</i>\n"
    ]

    buttons = []
    for idx, acc in enumerate(accounts, 1):
        is_active = acc.get('is_active', False)
        acc_id = acc.get('account_id')
        name = acc.get('first_name', f"Account {idx}")
        phone = acc.get('phone', '')
        status_icon = "🟢" if is_active else "⚪"
        active_tag = " [ACTIVE]" if is_active else ""
        btn_label = f"{status_icon} {idx}. {name[:12]} ({phone[-4:] if len(phone)>=4 else phone}){active_tag}"
        
        row = [InlineKeyboardButton(btn_label, callback_data=f"acc_switch:{acc_id}")]
        row.append(InlineKeyboardButton("🗑️", callback_data=f"acc_del:{acc_id}"))
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton("➕ Add Another Account", callback_data="acc_add_choice"),
        InlineKeyboardButton("🔄 Refresh", callback_data="acc_refresh")
    ])
    buttons.append([InlineKeyboardButton("❌ Close", callback_data="acc_close")])

    return "\n".join(lines), InlineKeyboardMarkup(buttons)

@app.on_message(filters.command(["accounts", "switchaccount", "myaccounts"]) & filters.private & ~filters.bot)
async def accounts_command_handler(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else 0
    if not is_authorized(user_id):
        return await message.reply('⛔ <b>Access Denied:</b> You are not authorized to use this bot.', quote=True)
    text, markup = await build_accounts_ui(user_id)
    await message.reply(text, reply_markup=markup, quote=True, parse_mode=enums.ParseMode.HTML)

@app.on_message(filters.private & ~filters.forwarded & filters.command(["login"]))
async def login_handler(bot: Client, message: Message):
    user_id = message.from_user.id if message.from_user else 0
    if not is_authorized(user_id):
        return await message.reply('⛔ <b>Access Denied:</b> You are not authorized to use this bot.', quote=True)

    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)

    accounts = await db.get_user_accounts(user_id)
    if accounts:
        active_acc = next((a for a in accounts if a.get('is_active')), accounts[0])
        text = (
            "🔐 <b>Telegram Login & Multi-Account Manager</b>\n\n"
            f"🟢 <b>Currently Active:</b> <b>{html.escape(active_acc.get('first_name', 'User'))}</b> (<code>{active_acc.get('phone', 'N/A')}</code>)\n"
            f"📊 <b>Total Saved Accounts:</b> <code>{len(accounts)}</code>\n\n"
            "You can add another account below without logging out, or manage and switch your accounts:"
        )
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔑 Add via String Session (Zero-SMS)", callback_data="login_choice_string"),
                InlineKeyboardButton("📱 Add via Phone + OTP", callback_data="login_choice_phone")
            ],
            [
                InlineKeyboardButton("👥 Manage / Switch Accounts", callback_data="acc_manage"),
                InlineKeyboardButton("❌ Cancel", callback_data="acc_close")
            ]
        ])
        return await message.reply(text, reply_markup=markup, quote=True)

    text = (
        "🔐 <b>Telegram Account Login</b>\n\n"
        "Choose your preferred login method:\n\n"
        "1️⃣ <b>🔑 Pyrogram String Session (Recommended - Zero SMS)</b>\n"
        "⚡ <i>1-second instant login! 100% reliable, zero SMS required, bypasses all carrier SMS filters and Telegram MTProto rate limits.</i>\n\n"
        "2️⃣ <b>📱 Phone Number + OTP</b>\n"
        "<i>Direct login with official Telegram Desktop headers and live in-app/SMS delivery tracking.</i>"
    )
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 Pyrogram String Session (Zero-SMS)", callback_data="login_choice_string")],
        [InlineKeyboardButton("📱 Phone Number + OTP", callback_data="login_choice_phone")],
        [InlineKeyboardButton("❌ Cancel", callback_data="acc_close")]
    ])
    await message.reply(text, reply_markup=markup, quote=True)

async def start_string_session_login(bot: Client, user_id: int):
    prompt_msg = await bot.ask(
        user_id,
        "🔑 <b>Pyrogram String Session Login</b>\n\n"
        "Please send your <b>Pyrogram Session String</b> below.\n\n"
        "💡 <i>Tip: You can generate a Pyrogram session using any standard Telegram session generator bot or script.</i>\n\n"
        "🛡️ <i>Your session string is stored safely in your private database.</i>\n\n"
        "Enter <code>/cancel</code> to abort.",
        filters=filters.text,
        timeout=300
    )
    if not prompt_msg.text or prompt_msg.text.strip().lower() == '/cancel':
        return await bot.send_message(user_id, "❌ <i>Login process cancelled.</i>")

    raw_session = prompt_msg.text.strip().replace(" ", "").replace("\n", "").replace("\r", "")
    if len(raw_session) < SESSION_STRING_SIZE:
        return await prompt_msg.reply(
            "❌ <b>Invalid Session String:</b>\n"
            "The string provided is too short. Please ensure you copied the complete Pyrogram Session String.",
            quote=True
        )

    validating_msg = await prompt_msg.reply("🔄 <b>Connecting & verifying session with Telegram...</b>", quote=True)
    temp_client = None
    login_api_id = API_ID or 6
    login_api_hash = API_HASH or "eb06d4abfb49dc3eeb1aeb98ae0f581e"
    try:
        temp_client = Client(
            f"auth_val_{user_id}_{int(time.time())}",
            session_string=raw_session,
            api_id=login_api_id,
            api_hash=login_api_hash,
            device_model="Telegram Desktop",
            system_version="Windows 11 x64",
            app_version="5.6.1 x64",
            lang_code="en",
            in_memory=True
        )
        await temp_client.start()
        me = await temp_client.get_me()
        
        acc_data = {
            'account_id': str(me.id),
            'phone': f"+{me.phone_number}" if me.phone_number else "Hidden",
            'first_name': me.first_name or "Telegram User",
            'username': f"@{me.username}" if me.username else "",
            'user_id': me.id,
            'session': raw_session,
            'api_id': login_api_id,
            'api_hash': login_api_hash
        }
        await db.add_user_account(user_id, acc_data, set_as_active=True)
        
        try: await temp_client.stop()
        except Exception: pass
        
        if user_id in USER_CLIENTS:
            try: await USER_CLIENTS[user_id].stop()
            except Exception: pass
            USER_CLIENTS.pop(user_id, None)
            
        await get_user_client(user_id)
        
        success_text = (
            "╔════❰ ʟᴏɢɪɴ sᴜᴄᴄᴇssғᴜʟ ❱═❍⊱❁۪۪\n"
            "║╭━━━━━━━━━━━━━━━➣\n"
            f"║┣⪼ 👤 Name: {html.escape(acc_data['first_name'])}\n"
            f"║┣⪼ 🆔 User ID: <code>{me.id}</code>\n"
            f"║┣⪼ 📞 Phone: <code>{acc_data['phone']}</code>\n"
            f"║┣⪼ 🔗 Username: {acc_data['username'] or 'None'}\n"
            "║┣⪼ 🟢 Status: <code>LOGGED IN & ACTIVE</code>\n"
            "║╰━━━━━━━━━━━━━━━➣\n"
            "╚════❰ ʟᴏɢɪɴ ᴅᴏɴᴇ ❱══❍⊱❁۪۪\n\n"
            "🎉 <b>Login Done! Telegram session successfully authenticated.</b>\n\n"
            "⚡ All restricted downloads, fast copies, and watchers will now use this active session!\n"
            "💡 Use <code>/accounts</code> to view/switch sessions or <code>/logout</code> to disconnect."
        )
        try:
            await validating_msg.edit(success_text)
        except Exception:
            await bot.send_message(user_id, success_text)
    except Exception as e:
        if temp_client:
            try: await temp_client.stop()
            except Exception: pass
        await validating_msg.edit(f"❌ <b>Login Failed:</b> <code>{html.escape(str(e))}</code>\n\nPlease check your session string and try again with /login.")

async def start_phone_login(bot: Client, user_id: int):
    api_id = API_ID
    api_hash = API_HASH
    
    if API_ID == 0 or not API_HASH:
        api_id_msg = await bot.ask(user_id, "<b>Send Your API ID from my.telegram.org.</b>\n\nEnter /cancel to abort.", filters=filters.text, timeout=300)
        if not api_id_msg.text or api_id_msg.text.strip().lower() == '/cancel':
            return await bot.send_message(user_id, "❌ <i>Login process cancelled.</i>")
        try:
            api_id = int(api_id_msg.text.strip())
            if api_id < 10000 or api_id > 999999999:
                return await api_id_msg.reply("❌ <b>Invalid API ID.</b> Start again with /login.", quote=True)
        except ValueError:
            return await api_id_msg.reply("❌ <b>API ID must be an integer.</b> Start again with /login.", quote=True)

        api_hash_msg = await bot.ask(user_id, "<b>Now Send Your API HASH from my.telegram.org.</b>\n\nEnter /cancel to abort.", filters=filters.text, timeout=300)
        if not api_hash_msg.text or api_hash_msg.text.strip().lower() == '/cancel':
            return await bot.send_message(user_id, "❌ <i>Login process cancelled.</i>")
        api_hash = api_hash_msg.text.strip()
        if len(api_hash) != 32:
            return await api_hash_msg.reply("❌ <b>Invalid API HASH</b> (must be 32 characters). Start again with /login.", quote=True)

    phone_prompt = (
        "📱 <b>Phone Number Login</b>\n\n"
        "Please send your <b>Phone Number</b> in international format.\n"
        "Example: <code>+1234567890</code> or <code>+919876543210</code>\n\n"
        "Enter <code>/cancel</code> to abort."
    )
    phone_msg = await bot.ask(user_id, phone_prompt, filters=filters.text, timeout=300)
    if not phone_msg.text or phone_msg.text.strip().lower() == '/cancel':
        return await bot.send_message(user_id, "❌ <i>Login process cancelled.</i>")

    phone_number = re.sub(r"[^\d+]", "", phone_msg.text.strip())
    if not phone_number.startswith("+"):
        phone_number = "+" + phone_number
    if len(phone_number) < 8 or len(phone_number) > 16:
        return await phone_msg.reply("❌ <b>Invalid phone number format.</b> Include country code, e.g. <code>+919876543210</code>.", quote=True)

    status_msg = await phone_msg.reply("🔄 <b>Connecting to Telegram & requesting OTP...</b>", quote=True)

    client_auth = Client(
        f"login_{user_id}_{int(time.time())}",
        api_id=api_id,
        api_hash=api_hash,
        device_model="Telegram Desktop",
        system_version="Windows 11 x64",
        app_version="5.6.1 x64",
        lang_code="en",
        in_memory=True
    )
    
    try:
        await client_auth.connect()
    except Exception as e:
        return await status_msg.edit(f"❌ <b>Connection Error:</b> <code>{html.escape(str(e))}</code>")

    try:
        code = await client_auth.send_code(phone_number)
    except FloodWait as e:
        await client_auth.disconnect()
        return await status_msg.edit(f"⏳ <b>Telegram FloodWait:</b> Please wait <code>{e.value}</code> seconds before trying again.")
    except PhoneNumberInvalid:
        await client_auth.disconnect()
        return await status_msg.edit("❌ <b>Phone number is invalid</b> in Telegram's database. Please check country code.")
    except PhoneNumberBanned:
        await client_auth.disconnect()
        return await status_msg.edit("🚫 <b>This phone number is banned</b> from Telegram.")
    except ApiIdInvalid:
        await client_auth.disconnect()
        return await status_msg.edit("❌ <b>API ID / API Hash invalid.</b>")
    except Exception as e:
        await client_auth.disconnect()
        return await status_msg.edit(f"❌ <b>Failed to send OTP:</b> <code>{html.escape(str(e))}</code>\n\n💡 <i>Try logging in via <b>Pyrogram Session String</b> instead (Zero SMS)!</i>")

    PENDING_LOGINS[user_id] = {
        'client': client_auth,
        'phone': phone_number,
        'phone_code_hash': code.phone_code_hash,
        'api_id': api_id,
        'api_hash': api_hash,
        'time': time.time()
    }

    code_type = getattr(code, 'type', None)
    type_str = str(code_type).lower()
    
    if "app" in type_str:
        where_otp = (
            "📩 <b>OTP sent to Official Telegram App!</b>\n"
            "👉 Please open Telegram on your other device (phone or PC) and check the chat from <b>Telegram (777000)</b>.\n"
            "<i>(Telegram did NOT send an SMS because you have an active Telegram app session).</i>"
        )
    elif "sms" in type_str:
        where_otp = (
            "📱 <b>OTP sent via SMS!</b>\n"
            "👉 Please check the SMS messages on your phone SIM card."
        )
    elif "call" in type_str:
        where_otp = (
            "📞 <b>Telegram will call your phone!</b>\n"
            "👉 Answer the call to hear your verification code."
        )
    else:
        where_otp = "🔔 <b>Telegram sent your verification code!</b>"

    otp_prompt_text = (
        f"{where_otp}\n\n"
        f"Phone: <code>{phone_number}</code>\n\n"
        "<b>Send your OTP code here.</b>\n"
        "You can send it as <code>12345</code> or with spaces <code>1 2 3 4 5</code>.\n\n"
        "💡 <i>Didn't get the code? Tap <b>[📲 Resend OTP via SMS]</b> below or send <code>/resend</code>.</i>\n"
        "Enter <code>/cancel</code> to abort."
    )
    resend_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📲 Resend OTP via SMS", callback_data="resend_otp_btn")],
        [InlineKeyboardButton("❌ Cancel Login", callback_data="cancel_otp_btn")]
    ])
    await status_msg.edit(otp_prompt_text, reply_markup=resend_kb)

    otp_msg = await bot.ask(user_id, "⌨️ <b>Waiting for OTP code:</b>", filters=filters.text, timeout=600)
    if not otp_msg.text or otp_msg.text.strip().lower() == '/cancel':
        if user_id in PENDING_LOGINS:
            try: await PENDING_LOGINS[user_id]['client'].disconnect()
            except Exception: pass
            PENDING_LOGINS.pop(user_id, None)
        return await bot.send_message(user_id, "❌ <i>Login process cancelled.</i>")

    if otp_msg.text.strip().lower() == '/resend':
        return await handle_resend_otp(bot, user_id, status_msg)

    raw_code = re.sub(r"\D", "", otp_msg.text.strip())
    if not raw_code:
        if user_id in PENDING_LOGINS:
            try: await PENDING_LOGINS[user_id]['client'].disconnect()
            except Exception: pass
            PENDING_LOGINS.pop(user_id, None)
        return await otp_msg.reply("❌ <b>Invalid OTP format.</b> OTP must contain numbers.", quote=True)

    verifying_msg = await otp_msg.reply("🔄 <b>Signing in to Telegram...</b>", quote=True)
    
    try:
        await client_auth.sign_in(phone_number, code.phone_code_hash, raw_code)
    except PhoneCodeInvalid:
        return await verifying_msg.edit("❌ <b>OTP is invalid.</b> Please try again with /login.")
    except PhoneCodeExpired:
        return await verifying_msg.edit("❌ <b>OTP is expired.</b> Please request a new code with /login.")
    except SessionPasswordNeeded:
        two_step_msg = await bot.ask(
            user_id,
            "🔐 <b>Two-Step Verification (2FA) Password Required:</b>\n\n"
            "Your Telegram account has cloud password protection enabled.\n"
            "Please send your <b>2FA Password</b> below.\n\n"
            "Enter <code>/cancel</code> to abort.",
            filters=filters.text,
            timeout=300
        )
        if not two_step_msg.text or two_step_msg.text.strip().lower() == '/cancel':
            return await bot.send_message(user_id, "❌ <i>Login cancelled.</i>")
        try:
            await client_auth.check_password(password=two_step_msg.text.strip())
        except PasswordHashInvalid:
            return await two_step_msg.reply("❌ <b>Invalid 2FA password provided.</b> Start again with /login.", quote=True)
        except Exception as e:
            return await two_step_msg.reply(f"❌ <b>2FA Error:</b> <code>{html.escape(str(e))}</code>", quote=True)
    except Exception as e:
        return await verifying_msg.edit(f"❌ <b>Sign-in error:</b> <code>{html.escape(str(e))}</code>")

    string_session = await client_auth.export_session_string()
    me = await client_auth.get_me()
    await client_auth.disconnect()
    PENDING_LOGINS.pop(user_id, None)

    acc_data = {
        'account_id': str(me.id),
        'phone': phone_number,
        'first_name': me.first_name or "Telegram User",
        'username': f"@{me.username}" if me.username else "",
        'user_id': me.id,
        'session': string_session,
        'api_id': api_id,
        'api_hash': api_hash
    }
    await db.add_user_account(user_id, acc_data, set_as_active=True)

    if user_id in USER_CLIENTS:
        try: await USER_CLIENTS[user_id].stop()
        except Exception: pass
        USER_CLIENTS.pop(user_id, None)

    await get_user_client(user_id)

    success_text = (
        "╔════❰ ʟᴏɢɪɴ sᴜᴄᴄᴇssғᴜʟ ❱═❍⊱❁۪۪\n"
        "║╭━━━━━━━━━━━━━━━➣\n"
        f"║┣⪼ 👤 Name: {html.escape(acc_data['first_name'])}\n"
        f"║┣⪼ 🆔 User ID: <code>{me.id}</code>\n"
        f"║┣⪼ 📞 Phone: <code>{acc_data['phone']}</code>\n"
        f"║┣⪼ 🔗 Username: {acc_data['username'] or 'None'}\n"
        "║┣⪼ 🟢 Status: <code>LOGGED IN & ACTIVE</code>\n"
        "║╰━━━━━━━━━━━━━━━➣\n"
        "╚════❰ ʟᴏɢɪɴ ᴅᴏɴᴇ ❱══❍⊱❁۪۪\n\n"
        "🎉 <b>Login Done! Telegram session successfully authenticated.</b>\n\n"
        "⚡ All restricted downloads, fast copies, and watchers will now use this active session!\n"
        "💡 Use <code>/accounts</code> to view/switch sessions or <code>/logout</code> to disconnect."
    )
    try:
        await verifying_msg.edit(success_text)
    except Exception:
        await bot.send_message(user_id, success_text)

async def handle_resend_otp(bot: Client, user_id: int, status_msg: Message = None):
    login_info = PENDING_LOGINS.get(user_id)
    if not login_info:
        if status_msg:
            await status_msg.edit("❌ <b>No pending login found.</b> Please start again with /login.")
        else:
            await bot.send_message(user_id, "❌ <b>No pending login found.</b> Please start again with /login.")
        return

    client_auth = login_info['client']
    phone = login_info['phone']
    old_hash = login_info['phone_code_hash']

    try:
        new_code = await client_auth.resend_code(phone, old_hash)
        login_info['phone_code_hash'] = new_code.phone_code_hash
        code_type = getattr(new_code, 'type', None)
        msg_text = (
            f"📲 <b>OTP Resent Successfully!</b>\n\n"
            f"Telegram dispatched a new verification code.\n"
            f"Delivery Type: <b>{str(code_type).replace('SentCodeType.', '')}</b>\n\n"
            "👉 Please check your SMS messages on your phone.\n"
            "Send the new code here when received, or <code>/cancel</code> to abort."
        )
        if status_msg:
            await status_msg.edit(msg_text)
        else:
            await bot.send_message(user_id, msg_text)
    except FloodWait as e:
        err = f"⏳ <b>FloodWait:</b> Please wait <code>{e.value}</code> seconds before requesting resend."
        if status_msg: await status_msg.edit(err)
        else: await bot.send_message(user_id, err)
    except Exception as e:
        err = f"❌ <b>Resend Failed:</b> <code>{html.escape(str(e))}</code>\n\n💡 <i>Try logging in via <b>Pyrogram Session String</b> instead (Zero SMS)!</i>"
        if status_msg: await status_msg.edit(err)
        else: await bot.send_message(user_id, err)

@app.on_message(filters.command(["resend", "resendotp"]) & filters.private & ~filters.bot)
async def resend_command_handler(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else 0
    if not is_authorized(user_id):
        return await message.reply('⛔ <b>Access Denied:</b> You are not authorized to use this bot.', quote=True)
    await handle_resend_otp(client, user_id)

@app.on_callback_query(filters.regex(r"^resend_otp_btn$"))
async def resend_otp_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    await query.answer("Requesting SMS resend from Telegram...", show_alert=False)
    await handle_resend_otp(client, user_id, query.message)

@app.on_callback_query(filters.regex(r"^cancel_otp_btn$"))
async def cancel_otp_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id in PENDING_LOGINS:
        try: await PENDING_LOGINS[user_id]['client'].disconnect()
        except Exception: pass
        PENDING_LOGINS.pop(user_id, None)
    await query.message.edit_text("❌ <i>Login process cancelled.</i>")
    await query.answer("Login cancelled.")

@app.on_callback_query(filters.regex(r"^login_choice_string$"))
async def login_choice_string_cb(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    await query.answer()
    try: await query.message.delete()
    except Exception: pass
    await start_string_session_login(client, user_id)

@app.on_callback_query(filters.regex(r"^login_choice_phone$"))
async def login_choice_phone_cb(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    await query.answer()
    try: await query.message.delete()
    except Exception: pass
    await start_phone_login(client, user_id)

@app.on_callback_query(filters.regex(r"^acc_switch:(.+)"))
async def acc_switch_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    acc_id = query.matches[0].group(1)
    switched = await db.switch_active_account(user_id, acc_id)
    if not switched:
        return await query.answer("❌ Account not found.", show_alert=True)
        
    if user_id in USER_CLIENTS:
        try: await USER_CLIENTS[user_id].stop()
        except Exception: pass
        USER_CLIENTS.pop(user_id, None)
    await get_user_client(user_id)
    
    text, markup = await build_accounts_ui(user_id)
    try: await query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except Exception: pass
    await query.answer(f"Switched to {switched.get('first_name', 'Account')}!", show_alert=False)

@app.on_callback_query(filters.regex(r"^acc_del:(.+)"))
async def acc_del_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    acc_id = query.matches[0].group(1)
    rem, new_act = await db.delete_user_account(user_id, acc_id)
    
    if user_id in USER_CLIENTS:
        try: await USER_CLIENTS[user_id].stop()
        except Exception: pass
        USER_CLIENTS.pop(user_id, None)
    if new_act:
        await get_user_client(user_id)
        
    text, markup = await build_accounts_ui(user_id)
    try: await query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except Exception: pass
    await query.answer("Account removed.", show_alert=False)

@app.on_callback_query(filters.regex(r"^acc_manage$|^acc_refresh$"))
async def acc_manage_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    text, markup = await build_accounts_ui(user_id)
    try: await query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except Exception: pass
    await query.answer()

@app.on_callback_query(filters.regex(r"^acc_add_choice$"))
async def acc_add_choice_callback(client: Client, query: CallbackQuery):
    text = (
        "➕ <b>Add Another Telegram Account</b>\n\n"
        "Choose how you want to add the new account:\n\n"
        "1️⃣ <b>🔑 String Session (Zero-SMS, Recommended)</b>\n"
        "2️⃣ <b>📱 Phone Number + OTP</b>"
    )
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 String Session", callback_data="login_choice_string")],
        [InlineKeyboardButton("📱 Phone Number + OTP", callback_data="login_choice_phone")],
        [InlineKeyboardButton("🔙 Back to Accounts", callback_data="acc_manage")]
    ])
    try: await query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except Exception: pass
    await query.answer()

@app.on_callback_query(filters.regex(r"^acc_close$"))
async def acc_close_callback(client: Client, query: CallbackQuery):
    try: await query.message.delete()
    except Exception: pass
    await query.answer()

@app.on_callback_query(filters.regex(r"^logout_act_confirm$"))
async def logout_act_confirm_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    accounts = await db.get_user_accounts(user_id)
    active_acc = next((a for a in accounts if a.get('is_active')), None)
    if active_acc:
        rem, new_act = await db.delete_user_account(user_id, active_acc['account_id'])
        if user_id in USER_CLIENTS:
            try: await USER_CLIENTS[user_id].stop()
            except Exception: pass
            USER_CLIENTS.pop(user_id, None)
        if new_act:
            await get_user_client(user_id)
    await query.message.edit_text("✅ <b>Active account logged out successfully!</b>")
    await query.answer("Active account logged out.")

@app.on_callback_query(filters.regex(r"^logout_all_confirm$"))
async def logout_all_confirm_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    await force_logout_user(user_id)
    await query.message.edit_text("✅ <b>All accounts logged out and cleared!</b>")
    await query.answer("All accounts cleared.")

# ==============================================================================
# --- BROADCAST ---
# ==============================================================================

async def broadcast_messages(user_id, message):
    start_time = time.time()
    try:
        await message.copy(chat_id=user_id)
        elapsed = time.time() - start_time
        await asyncio.sleep(max(0, 1.5 - elapsed)) 
        return True, "Success"
    except FloodWait as e:
        if e.value > 60:
            return False, "Error"
        await asyncio.sleep(e.value)
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        return False, "Deleted"
    except UserIsBlocked:
        await db.delete_user(int(user_id))
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        return False, "Error"
    except Exception as e:
        return False, "Error"

@app.on_message(filters.command("broadcast") & filters.private & ~filters.bot)
async def broadcast(bot, message):
    if not message.chat or message.chat.type != enums.ChatType.PRIVATE:
        return
    user_id = message.from_user.id if message.from_user else 0
    if not is_admin(user_id):
        return await message.reply("⛔ <b>Access Denied:</b> This command is restricted to administrators.", quote=True)
    if not message.reply_to_message:
        return await message.reply_text("**Reply This Command To Your Broadcast Message**")
    users = await db.get_all_users()
    b_msg = message.reply_to_message
    sts = await message.reply_text(text='Broadcasting your messages...')
    start_time = time.time()
    total_users = await db.total_users_count()
    done = 0
    blocked = 0
    deleted = 0
    failed = 0
    success = 0
    async for user in users:
        if 'id' in user:
            pti, sh = await broadcast_messages(int(user['id']), b_msg)
            if pti:
                success += 1
            elif pti == False:
                if sh == "Blocked":
                    blocked += 1
                elif sh == "Deleted":
                    deleted += 1
                elif sh == "Error":
                    failed += 1
            done += 1
            if not done % 20:
                await sts.edit(f"Broadcast in progress:\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}")
        else:
            done += 1
            failed += 1
            if not done % 20:
                await sts.edit(f"Broadcast in progress:\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}")

    time_taken = str(datetime.timedelta(seconds=int(time.time()-start_time)))
    await sts.edit(f"Broadcast Completed:\nCompleted in {time_taken} seconds.\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}")

# ==============================================================================
# --- WATCHER SETUP WIZARD ---
# ==============================================================================

@app.on_message(filters.command(["watch"]) & filters.private)
async def watch_setup(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return await message.reply('⛔ <b>Access Denied:</b> You are not authorized to use this bot.', quote=True)
    
    if len(message.command) < 2:
        saved_sources = await db.get_saved_channels(user_id, channel_type="source")
        if saved_sources:
            PENDING_TASKS[user_id] = {
                "mode": "WATCHER",
                "status": "waiting_source_select"
            }
            text, markup = build_channel_memory_ui(saved_sources, page=1, mode="watch_select", channel_type="source")
            return await message.reply(text, reply_markup=markup, quote=True)
        else:
            empty_kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Source Channel", callback_data="prompt_add_source")],
                [InlineKeyboardButton("❌ Close", callback_data="ch_close")]
            ])
            return await message.reply(
                "👀 <b>REAL-TIME AUTO-FORWARD WATCHER SETUP</b>\n\n"
                "<b>Usage:</b> <code>/watch https://t.me/channel/123</code>\n"
                "<i>(Supports Topics too: <code>/watch https://t.me/c/123/45</code>)</i>\n\n"
                "💡 <b>Save Frequent Sources:</b> Use <code>/addsourcechannel</code> to store your favourite source channels so you can start watching them with 1 tap!",
                reply_markup=empty_kb,
                quote=True
            )
    
    link_text = message.command[1]
    
    wait_msg = await message.reply("🔎 **Analyzing Source...**", quote=True)
    is_restricted, status_text = await check_link_restriction(user_id, link_text)
    
    source_thread_id = None
    if "t.me/c/" in link_text:
        parts = link_text.split("t.me/c/")[1].split("/")
        if len(parts) >= 2 and parts[1].isdigit():
            source_thread_id = int(parts[1])
    elif "t.me/" in link_text:
        parts = link_text.split("t.me/")[1].split("/")
        if len(parts) >= 2 and parts[1].isdigit():
            source_thread_id = int(parts[1])
    
    await wait_msg.delete()
    
    PENDING_TASKS[user_id] = {
        "mode": "WATCHER", 
        "link": link_text,
        "source_thread_id": source_thread_id,
        "is_restricted": is_restricted,
        "status": "waiting_choice"
    }
    # Auto-save source channel in background
    try:
        clean_text_s = link_text.replace("https://", "").replace("http://", "").replace("t.me/", "").replace("c/", "")
        clean_text_s = clean_text_s.split("-")[0].strip()
        parts_s = clean_text_s.split("/")
        cid_s = None
        if "t.me/c/" in link_text or link_text.startswith("c/"):
            cid_s = int("-100" + parts_s[0])
        elif parts_s[0].isdigit():
            cid_s = int("-100" + parts_s[0])
        else:
            cid_s = parts_s[0].lstrip("@")
        if cid_s:
            asyncio.create_task(db.save_channel(
                user_id=user_id,
                channel_id=cid_s,
                channel_title=f"Chat {cid_s}",
                channel_type="source",
                thread_id=source_thread_id
            ))
            asyncio.create_task(auto_resolve_channel_title(client, user_id, cid_s, channel_type="source", thread_id=source_thread_id))
    except Exception:
        pass
    
    buttons = [
        [InlineKeyboardButton("📂 Send to DM (Here)", callback_data="dest_dm")],
        [InlineKeyboardButton("📢 Send to Channel/Group", callback_data="dest_custom")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_setup")]
    ]
    
    await message.reply(
        f"👀 **Watcher Setup**\n\n"
        f"{status_text}\n"
        f"{(f'🔹 **Source Topic:** `{source_thread_id}` detected!' if source_thread_id else '')}\n\n"
        "**Where should new messages go?**",
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True
    )

@app.on_message(filters.command(["removetarget", "remove_target"]) & filters.private)
async def remove_target_cmd(client, message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return await message.reply("⛔ <b>Access Denied:</b> You are not authorized to use this bot.", quote=True)
    if len(message.command) < 3:
        return await message.reply("**Usage:** `/removetarget [source_id] [dest_id]`")
    src = message.command[1]
    dst = message.command[2]

    if await db.remove_watcher_target(src, dst, user_id=user_id):
        await message.reply("✅ **Target Removed Successfully!**\nNo more messages will route here from that source.")
    else:
        await message.reply("⚠️ Target or Source not found for your account.")

@app.on_message(filters.command(["removesource", "unwatch"]) & filters.private)
async def remove_source_cmd(client, message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return await message.reply("⛔ <b>Access Denied:</b> You are not authorized to use this bot.", quote=True)
    if len(message.command) < 2:
        return await message.reply("**Usage:** `/unwatch [source_id]`")

    try:
        src = int(message.command[1])
    except ValueError:
        return await message.reply("⚠️ **Invalid format!**\nPlease pass the numerical **Source ID** (e.g. `-100123...`). You can find this ID by sending `/watchers`.")

    if await db.remove_watcher(src, user_id=user_id):
        await message.reply("✅ **Source Route Removed Successfully!**")
    else:
        await message.reply("⚠️ Source not found for your account.")

@app.on_message(filters.command(["watchers", "list"]) & filters.private)
async def list_watchers(client, message):
    try:
        user_id = message.from_user.id
        if not is_authorized(user_id):
            return await message.reply("⛔ <b>Access Denied:</b> You are not authorized to use this bot.", quote=True)

        show_all = False
        if len(message.command) > 1 and message.command[1].lower() == "all" and is_admin(user_id):
            show_all = True
        user_watchers = await db.get_user_watchers(user_id, show_all=show_all)

        if not user_watchers:
            empty_kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🛰️ Setup New Watcher", callback_data="watch_manual")],
                [InlineKeyboardButton("📥 Saved Sources", callback_data="ch_page:1:source_view:source"),
                 InlineKeyboardButton("📤 Saved Destinations", callback_data="ch_page:1:dest_view:dest")],
                [InlineKeyboardButton("❌ Close", callback_data="close_menu")]
            ])
            empty_text = (
                "💤 <b>No Active Watchers Found.</b>\n\n"
                "You don't have any channels currently being monitored in real-time.\n\n"
                "• Use <code>/watch &lt;Link&gt;</code> to set up a 24/7 auto-forwarder.\n"
                "• Or pick directly from your saved source channels using the buttons below!"
            )
            return await message.reply(
                empty_text,
                reply_markup=empty_kb,
                quote=True
            )

        text, markup = build_watchers_page_ui(user_watchers, page=0, is_admin_view=show_all)
        await message.reply(text, reply_markup=markup, quote=True)
    except Exception as e:
        logger.error(f"Error in list_watchers: {e}", exc_info=True)
        await message.reply(f"⚠️ <b>Error retrieving watchers:</b> <code>{html.escape(str(e))}</code>", quote=True)

@app.on_callback_query(filters.regex("^unwatch_"))
async def unwatch_callback(client, query):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied", show_alert=True)

    if query.data == "unwatch_all":
        u_filter = {"$or": [{"user_id": user_id}, {"user_id": int(user_id)}, {"user_id": str(user_id)}]}
        result = await db.db.watchers.delete_many(u_filter)
        success_txt = f"✅ <b>Success!</b>\n\n🗑 Removed <code>{result.deleted_count}</code> active watchers for your account."
        await query.message.edit_text(
            success_txt,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 View Watchers", callback_data="watchers_pg:0:0")],
                [InlineKeyboardButton("❌ Close", callback_data="close_menu")]
            ])
        )
        return

    data = query.data.split("_")
    try:
        source_id = int(data[1])
        topic_id = int(data[2]) if len(data) > 2 else 0
        back_page = int(data[3]) if len(data) > 3 else 0
    except (ValueError, IndexError):
        return await query.answer("⚠️ Invalid watcher request data.", show_alert=True)

    u_filter = {"$or": [{"user_id": user_id}, {"user_id": int(user_id)}, {"user_id": str(user_id)}]}
    query_db = {'source_id': source_id, **u_filter}
    if topic_id != 0:
        query_db['source_thread'] = topic_id

    watcher = await db.db.watchers.find_one(query_db)
    src_name = str(source_id)
    if watcher:
        src_name = watcher.get('source_title') or str(source_id)

    del_filter = {'source_id': source_id, **u_filter}
    if topic_id == 0:
        del_filter['$or'] = [{'source_thread': None}, {'source_thread': {'$exists': False}}]
    else:
        del_filter['source_thread'] = topic_id

    result = await db.db.watchers.delete_many(del_filter)
    removed_txt = (
        f"🗑 <b>Active Watcher Task Removed</b>\n\n"
        f"• Source: <b>{html.escape(src_name)}</b> (<code>{source_id}</code>)\n"
        f"• Deleted records: <code>{result.deleted_count}</code>\n\n"
        "No more real-time messages will be forwarded from this source."
    )
    await query.message.edit_text(
        removed_txt,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 View Watchers", callback_data=f"watchers_pg:{back_page}:0")],
            [InlineKeyboardButton("❌ Close", callback_data="close_menu")]
        ])
    )


# ==============================================================================
# --- CORE: receive links / start tasks / processing / cancel checks ---
# ==============================================================================

@app.on_message((filters.text | filters.caption | filters.forwarded) & filters.private & ~filters.regex(r"^/"))
async def save(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return await message.reply('⛔ <b>Access Denied:</b> You are not authorized to use this bot.', quote=True)
    if message.text and message.text.startswith("/"):
        try: message.continue_propagation()
        except Exception: pass
        return
    if user_id in PENDING_ADD_CHANNEL:
        pending_val = PENDING_ADD_CHANNEL.pop(user_id, None)
        if isinstance(pending_val, dict):
            prompt_msg_id = pending_val.get("prompt_msg_id")
            ch_type = pending_val.get("channel_type", "dest")
        else:
            prompt_msg_id = pending_val
            ch_type = "dest"
        raw_submission = message.text or message.caption or ""
        if not raw_submission and getattr(message, "forward_from_chat", None):
            raw_submission = str(message.forward_from_chat.id)
        await process_add_channel_submission(client, message, raw_submission, prompt_msg_id=prompt_msg_id, channel_type=ch_type)
        return
    if user_id in PENDING_TASKS:
        task_status = PENDING_TASKS[user_id].get("status")
        if task_status == "waiting_speed":
            await process_speed_input(client, message)
            return
        if task_status in ["waiting_id", "waiting_channel_select", "waiting_choice"]:
            is_dest = False
            if getattr(message, "forward_from_chat", None) or getattr(message, "forward_from", None):
                is_dest = True
            else:
                raw_txt = (message.text or message.caption or "").strip()
                if task_status == "waiting_id" and raw_txt and not raw_txt.startswith("/"):
                    is_dest = True
                elif raw_txt:
                    is_dest = is_destination_channel_input(raw_txt)
            if is_dest:
                await process_custom_destination(client, message)
                return

    link_text = message.text or message.caption
    if not link_text or "https://t.me/" not in link_text:
        return

    wait_msg = await message.reply("🔎 **Analyzing Link...**", quote=True)
    is_restricted, status_text = await check_link_restriction(user_id, link_text)
    await wait_msg.delete()

    # 🚀 Auto-save source channel into Saved Sources
    try:
        source_cid = None
        source_th = None
        if "t.me/c/" in link_text:
            parts_s = link_text.split("t.me/c/")[1].split("/")
            chat_p = parts_s[0].strip()
            source_cid = int(f"-100{chat_p}") if not chat_p.startswith("-100") else int(chat_p)
            if len(parts_s) > 2 and parts_s[2].strip().isdigit():
                source_th = int(parts_s[1].strip())
        elif "t.me/" in link_text:
            parts_s = link_text.split("t.me/")[1].split("/")
            source_cid = parts_s[0].strip()
            if len(parts_s) > 2 and parts_s[2].strip().isdigit():
                source_th = int(parts_s[1].strip())
        if source_cid:
            asyncio.create_task(db.save_channel(
                user_id=user_id,
                channel_id=source_cid,
                channel_title=f"Chat {source_cid}",
                channel_type="source",
                thread_id=source_th
            ))
            asyncio.create_task(auto_resolve_channel_title(client, user_id, source_cid, channel_type="source", thread_id=source_th))
    except Exception:
        pass

    PENDING_TASKS[user_id] = {
        "link": link_text, 
        "status": "waiting_choice",
        "is_restricted": is_restricted,
        "created_at": time.time()
    }
    cleanup_stale_pending_tasks()
    
    buttons = [
        [InlineKeyboardButton("📂 Send to DM (Here)", callback_data="dest_dm")],
        [InlineKeyboardButton("📢 Send to Channel/Group", callback_data="dest_custom")],
        [InlineKeyboardButton("❌ Cancel Setup", callback_data="cancel_setup")]
    ]
    
    await message.reply(
        f"✨ **Link Detected!**\n\n"
        f"{status_text}\n\n"
        "Where should I send the files?",
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True
    )
    
@app.on_message(filters.command(["dl"]) & (filters.private | filters.group) & ~filters.bot)
async def dl_handler(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else 0
    if not user_id or getattr(message.from_user, "is_bot", False):
        return
    if not is_authorized(user_id):
        if message.chat and message.chat.type == enums.ChatType.PRIVATE:
            return await message.reply('⛔ <b>Access Denied:</b> You are not authorized to use this bot.', quote=True)
        return
    link_text = ""
    
    reply = message.reply_to_message
    if reply and (reply.text or reply.caption):
        link_text = reply.text or reply.caption
    elif len(message.command) > 1:
        link_text = message.text.split(None, 1)[1]
        
    if not link_text or "https://t.me/" not in link_text:
        await message.reply_text(
            "**Usage:**\n"
            "• Reply to a link with `/dl`\n"
            "• Or send `/dl https://t.me/...`"
        )
        return

    wait_msg = await message.reply("🔎 **Analyzing Link...**", quote=True)
    is_restricted, status_text = await check_link_restriction(user_id, link_text)
    await wait_msg.delete()

    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        PENDING_TASKS[user_id] = {
            "link": link_text,
            "dest_chat_id": message.chat.id,
            "dest_thread_id": message.message_thread_id,
            "dest_title": message.chat.title or "This Group",
            "status": "waiting_speed",
            "is_restricted": is_restricted 
        }
        await message.reply(f"✨ **Link Analyzed!**\n{status_text}", quote=True)
        await ask_for_speed(message)
        return

    PENDING_TASKS[user_id] = {
        "link": link_text, 
        "status": "waiting_choice",
        "is_restricted": is_restricted
    }
    
    buttons = [
        [InlineKeyboardButton("📂 Send to DM (Here)", callback_data="dest_dm")],
        [InlineKeyboardButton("📢 Send to Channel/Group", callback_data="dest_custom")],
        [InlineKeyboardButton("❌ Cancel Setup", callback_data="cancel_setup")]  
    ]
    
    await message.reply(
        f"✨ **Link Detected!**\n\n"
        f"{status_text}\n\n"
        "I am ready to process this content. Please tell me where you want the files sent:",
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True
    )
    

# ==============================================================================
# --- CHANNEL MEMORY & QUICK SELECTOR SYSTEM (10 BUTTONS PER PAGE) ---
# ==============================================================================
CHANNEL_EMOJIS = [
    "🎬", "📁", "🚀", "⚡", "💎", "🔥", "👑", "🍿", "📦", "🌟",
    "🎯", "🛡️", "🛸", "🔮", "🏆", "⚜️", "💠", "🪐", "🌀", "💫"
]

def get_channel_emoji(index: int, title: str) -> str:
    title_lower = str(title).lower()
    if any(k in title_lower for k in ["movie", "cinema", "film"]): return "🎬"
    if any(k in title_lower for k in ["file", "doc", "pdf", "soft"]): return "📁"
    if any(k in title_lower for k in ["backup", "archive", "storage"]): return "📦"
    if any(k in title_lower for k in ["vip", "premium", "royal"]): return "👑"
    if any(k in title_lower for k in ["fast", "speed", "express"]): return "⚡"
    if any(k in title_lower for k in ["series", "show", "anime"]): return "🍿"
    return CHANNEL_EMOJIS[(index - 1) % len(CHANNEL_EMOJIS)]

def is_destination_channel_input(raw_text: str) -> bool:
    if not raw_text or raw_text.startswith("/"):
        return False
    text = raw_text.strip()
    
    # 1. Obvious source batch links (ranges, -all, etc.) are NEVER destinations
    if "-all" in text.lower() or re.search(r"/\d+-\d+", text):
        return False

    # 2. Telegram invite links are destinations
    if "t.me/+" in text or "t.me/joinchat/" in text:
        return True

    words = text.split()
    first_token = words[0]

    # 3. Numeric ID: -100..., -..., or pure numbers >= 5 digits, or chat_id/topic_id
    if re.match(r"^-?\d+(?:/\d+)?$", first_token):
        clean = first_token.split("/")[0].lstrip("-")
        if clean.isdigit() and (len(clean) >= 5 or first_token.startswith("-100")):
            return True

    # 4. Telegram @username
    if first_token.startswith("@") and len(first_token) > 1:
        return True

    # 5. Public channel link without message ID: https://t.me/mychannel or t.me/mychannel
    if "t.me/" in first_token:
        if "t.me/c/" in first_token:
            parts = first_token.split("t.me/c/")[1].strip("/").split("/")
            if len(parts) == 1 and parts[0].isdigit():
                return True
            return False
        else:
            parts = first_token.split("t.me/")[1].strip("/").split("/")
            if len(parts) == 1 and parts[0] and not parts[0].isdigit():
                return True
            return False

    # 6. Single-token username without @ (must be exactly 1 token, e.g. "my_dest_channel")
    if len(words) == 1 and re.match(r"^[a-zA-Z][a-zA-Z0-9_]{3,31}$", first_token):
        common_words = {
            "http", "https", "cancel", "help", "start", "speed", "login", "logout",
            "hello", "thanks", "thank", "please", "admin", "owner", "status", "about",
            "watch", "ready", "close", "tasks", "stats", "reset", "clear", "error"
        }
        if first_token.lower() not in common_words:
            return True

    return False

def parse_channel_input(raw_text: str):
    text = (raw_text or "").strip()
    if not text:
        return None, None, None
    parts = text.split()
    target_spec = parts[0].strip()

    chat_id = None
    thread_id = None
    custom_title = None

    if "t.me/c/" in target_spec:
        clean = target_spec.split("t.me/c/")[1].strip("/")
        segs = clean.split("/")
        cid_str = segs[0].strip()
        chat_id = int(f"-100{cid_str}") if not cid_str.startswith("-100") else int(cid_str)
        if len(segs) > 1 and segs[1].strip().isdigit():
            thread_id = int(segs[1].strip())
    elif "t.me/" in target_spec:
        clean = target_spec.split("t.me/")[1].strip("/")
        segs = clean.split("/")
        chat_id = segs[0].strip()
        if not chat_id.startswith("+"):
            chat_id = chat_id.lstrip("@")
    elif "/" in target_spec:
        segs = target_spec.split("/")
        cid_str = segs[0].strip()
        clean_num = cid_str.lstrip("-")
        if clean_num.isdigit():
            raw_num = int(cid_str)
            if raw_num > 0 and raw_num > 10000000:
                chat_id = int(f"-100{raw_num}")
            elif not str(raw_num).startswith("-100"):
                chat_id = int(f"-100{abs(raw_num)}")
            else:
                chat_id = raw_num
        else:
            chat_id = cid_str.lstrip("@")
        if len(segs) > 1 and segs[1].strip().isdigit():
            thread_id = int(segs[1].strip())
    else:
        clean_num = target_spec.lstrip("-")
        if clean_num.isdigit():
            raw_num = int(target_spec)
            if raw_num > 0 and raw_num > 10000000:
                chat_id = int(f"-100{raw_num}")
            elif not str(raw_num).startswith("-100"):
                chat_id = int(f"-100{abs(raw_num)}")
            else:
                chat_id = raw_num
        else:
            chat_id = target_spec.lstrip("@")

    # Parse optional thread_id and custom title from subsequent tokens
    remaining_tokens = parts[1:]
    if remaining_tokens:
        if thread_id is None and len(remaining_tokens) >= 1 and remaining_tokens[0].isdigit():
            val = int(remaining_tokens[0])
            if val < 50000000 and len(remaining_tokens) > 1:
                thread_id = val
                remaining_tokens = remaining_tokens[1:]
            elif val < 50000000 and len(remaining_tokens) == 1:
                thread_id = val
                remaining_tokens = []

        if remaining_tokens:
            cand_title = " ".join(remaining_tokens).strip()
            is_accidental = False
            if re.match(r"^https?://", cand_title, re.IGNORECASE):
                is_accidental = True
            elif re.match(r"^t\.me/", cand_title, re.IGNORECASE):
                is_accidental = True
            elif re.match(r"^@[a-zA-Z0-9_]+$", cand_title):
                is_accidental = True
            elif re.match(r"^-?\d+$", cand_title):
                is_accidental = True
            elif cand_title.startswith("+"):
                is_accidental = True

            if not is_accidental and cand_title:
                custom_title = cand_title

    return chat_id, thread_id, custom_title

async def resolve_telegram_chat_title(client: Client, user_id: int, channel_id) -> tuple[int | str, str | None, bool, str | None]:
    """
    Resolves canonical channel ID, real Telegram title, forum status, and any error.
    Tries bot client first; if that fails, falls back to the user's connected userbot session.
    Returns: (canonical_channel_id, resolved_title, is_forum, error_reason)
    """
    norm_id = int(channel_id) if str(channel_id).lstrip('-').isdigit() else str(channel_id)
    canonical_id = norm_id
    resolved_title = None
    is_forum = False
    last_error = None

    # 1. Attempt resolution via bot client
    try:
        chat = await client.get_chat(norm_id)
        if chat:
            canonical_id = chat.id
            is_forum = getattr(chat, "is_forum", False)
            resolved_title = chat.title or getattr(chat, "first_name", None) or (f"{getattr(chat, 'first_name', '') or ''} {getattr(chat, 'last_name', '') or ''}".strip()) or None
            if resolved_title:
                return canonical_id, resolved_title, is_forum, None
    except Exception as e_bot:
        last_error = f"Bot: {e_bot}"

    # 2. Attempt resolution via userbot client (auto-initialised from session)
    try:
        user_client = await get_user_client(user_id)
        if user_client:
            chat = await user_client.get_chat(norm_id)
            if chat:
                canonical_id = chat.id
                is_forum = getattr(chat, "is_forum", False)
                resolved_title = chat.title or getattr(chat, "first_name", None) or (f"{getattr(chat, 'first_name', '') or ''} {getattr(chat, 'last_name', '') or ''}".strip()) or None
                if resolved_title:
                    return canonical_id, resolved_title, is_forum, None
        else:
            has_session = await db.get_session(user_id)
            if not has_session:
                last_error = (last_error or "") + " | Userbot: No active session. Use /login for private restricted channels."
            else:
                last_error = (last_error or "") + " | Userbot: Could not connect session."
    except Exception as e_user:
        last_error = f"{last_error or ''} | Userbot: {e_user}".strip(" |")

    return canonical_id, resolved_title, is_forum, last_error

async def auto_resolve_channel_title(client: Client, user_id: int, channel_id, current_title: str = None, channel_type: str = "dest", thread_id=None, force: bool = False) -> str:
    clean_title = (current_title or "").strip()
    is_generic = (
        not clean_title 
        or clean_title.startswith("Chat ") 
        or clean_title.startswith("[Unresolved]") 
        or clean_title in ["Target Chat", "Destination", "Unknown Destination", "Source"]
    )
    if not is_generic and not force:
        return clean_title

    canonical_id, resolved, _, err = await resolve_telegram_chat_title(client, user_id, channel_id)
    if resolved:
        try:
            # Update existing saved record(s) in database in-place without duplicating or inflating use_count
            await db.update_channel_title(user_id, canonical_id, resolved, channel_type=channel_type, thread_id=thread_id)
        except Exception as e:
            logger.error(f"Error persisting resolved title for channel {channel_id}: {e}")
        return resolved

    return current_title or f"[Unresolved] Chat {channel_id}"

def build_channel_memory_ui(saved_channels: list, page: int = 1, page_size: int = 10, mode: str = "select", channel_type: str = "dest"):
    ch_type = str(channel_type or "dest").lower()
    total_channels = len(saved_channels)
    total_pages = max(1, math.ceil(total_channels / page_size)) if total_channels > 0 else 1
    
    if page < 1: page = 1
    if page > total_pages: page = total_pages
    
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_channels)
    page_channels = saved_channels[start_idx:end_idx]
    
    buttons = []
    
    is_source = (ch_type == "source")
    type_label = "SOURCE" if is_source else "DESTINATION"
    type_icon = "📥" if is_source else "📤"
    
    if mode in ["delete", "source_delete", "dest_delete"]:
        header_text = (
            f"🗑️ <b>MANAGE / DELETE SAVED {type_label} CHANNELS (Page {page}/{total_pages})</b>\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"<i>Click on any {type_label.lower()} channel below to directly remove it from memory:</i>\n"
        )
        for i, ch in enumerate(page_channels, start=start_idx + 1):
            ch_id = ch["channel_id"]
            thread_id = ch.get("thread_id") or 0
            title = ch.get("channel_title") or f"Chat {ch_id}"
            emoji = ch.get("emoji") or get_channel_emoji(i, title)
            btn_text = f"❌ Remove: {emoji} {title[:20]}"
            callback_data = f"ch_del:{ch_id}:{thread_id}:{page}:{ch_type}"
            buttons.append([InlineKeyboardButton(btn_text, callback_data=callback_data)])
    elif mode in ["view", "source_view", "dest_view"]:
        header_text = (
            f"{type_icon} <b>SAVED {type_label} CHANNELS (Page {page}/{total_pages})</b>\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"📊 <b>Total {type_label.capitalize()} Channels in Memory:</b> <code>{total_channels}</code>\n\n"
            f"<i>Click on any {type_label.lower()} channel below to view details, delete it, or manage settings:</i>\n"
        )
        for i, ch in enumerate(page_channels, start=start_idx + 1):
            ch_id = ch["channel_id"]
            thread_id = ch.get("thread_id") or 0
            title = ch.get("channel_title") or f"Chat {ch_id}"
            emoji = ch.get("emoji") or get_channel_emoji(i, title)
            btn_text = f"{emoji} {i}. {title[:22]}"
            callback_data = f"ch_inspect:{ch_id}:{thread_id}:{page}:{ch_type}"
            buttons.append([InlineKeyboardButton(btn_text, callback_data=callback_data)])
    elif mode == "watch_select":
        header_text = (
            f"👀 <b>SELECT SAVED SOURCE CHANNEL TO WATCH (Page {page}/{total_pages})</b>\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            "<i>Click on any saved source channel below to immediately start real-time forwarding/watching:</i>\n"
        )
        for i, ch in enumerate(page_channels, start=start_idx + 1):
            ch_id = ch["channel_id"]
            thread_id = ch.get("thread_id") or 0
            title = ch.get("channel_title") or f"Chat {ch_id}"
            emoji = ch.get("emoji") or get_channel_emoji(i, title)
            btn_text = f"👀 {emoji} {i}. {title[:20]}"
            callback_data = f"ch_watch_sel:{ch_id}:{thread_id}"
            buttons.append([InlineKeyboardButton(btn_text, callback_data=callback_data)])
    else:  # mode == "select" (quick-select destination during transfer)
        header_text = (
            f"👑 <b>QUICK-SELECT DESTINATION CHANNEL (Page {page}/{total_pages})</b> 👑\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            "<i>Select a saved destination channel from memory below (or enter a new ID/link):</i>\n"
        )
        for i, ch in enumerate(page_channels, start=start_idx + 1):
            ch_id = ch["channel_id"]
            thread_id = ch.get("thread_id") or 0
            title = ch.get("channel_title") or f"Chat {ch_id}"
            emoji = ch.get("emoji") or get_channel_emoji(i, title)
            btn_text = f"{emoji} {i}. {title[:22]}"
            callback_data = f"ch_sel:{ch_id}:{thread_id}"
            buttons.append([InlineKeyboardButton(btn_text, callback_data=callback_data)])

    # Pagination navigation row
    nav_row = []
    if total_pages > 1:
        if page > 1:
            nav_row.append(InlineKeyboardButton("◀️ Prev", callback_data=f"ch_page:{page-1}:{mode}:{ch_type}"))
        nav_row.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data=f"ch_page:{page}:{mode}:{ch_type}"))
        if page < total_pages:
            nav_row.append(InlineKeyboardButton("Next ▶️", callback_data=f"ch_page:{page+1}:{mode}:{ch_type}"))
        buttons.append(nav_row)

    # Bottom management action row
    if mode in ["delete", "source_delete", "dest_delete"]:
        buttons.append([
            InlineKeyboardButton("🔙 Back to Channel List", callback_data=f"ch_page:{page}:{ch_type}_view:{ch_type}"),
            InlineKeyboardButton("❌ Close", callback_data="ch_close")
        ])
    elif mode in ["view", "source_view", "dest_view"]:
        add_btn_text = "➕ Add Source Channel" if is_source else "➕ Add Destination Channel"
        add_cb = "prompt_add_source" if is_source else "prompt_add_dest"
        del_cb = f"ch_page:{page}:{ch_type}_delete:{ch_type}"
        action_row = [InlineKeyboardButton(add_btn_text, callback_data=add_cb)]
        if total_channels > 0:
            action_row.append(InlineKeyboardButton("🗑️ Bulk Delete Mode", callback_data=del_cb))
        buttons.append(action_row)
        buttons.append([InlineKeyboardButton("❌ Close", callback_data="ch_close")])
    elif mode == "watch_select":
        action_row = [
            InlineKeyboardButton("➕ Add Source", callback_data="prompt_add_source"),
            InlineKeyboardButton("✏️ Manual Link", callback_data="watch_manual"),
            InlineKeyboardButton("🛑 Cancel", callback_data="cancel_setup")
        ]
        buttons.append(action_row)
    else:  # destination select
        action_row = [InlineKeyboardButton("✏️ Enter Other ID/Link", callback_data="ch_manual")]
        if total_channels > 0:
            action_row.append(InlineKeyboardButton("🗑️ Delete Channels", callback_data=f"ch_page:{page}:dest_delete:dest"))
        action_row.append(InlineKeyboardButton("🛑 Cancel", callback_data="cancel_setup"))
        buttons.append(action_row)
    
    footer_text = f"\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n💎 <i>Showing {start_idx + 1 if total_channels else 0}–{end_idx} of {total_channels} saved {type_label.lower()} channels • 10/Page</i>"
    return header_text + footer_text, InlineKeyboardMarkup(buttons)

def cleanup_stale_pending_tasks():
    now = time.time()
    stale_keys = [uid for uid, t in PENDING_TASKS.items() if now - t.get("created_at", now) > 900]
    for uid in stale_keys:
        PENDING_TASKS.pop(uid, None)

@app.on_callback_query(filters.regex(r"^dm_dest:(saved_messages|bot_chat|back)$"))
async def dm_dest_choice_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id not in PENDING_TASKS:
        return await query.answer("❌ Task expired. Please send the link again.", show_alert=True)
    
    choice = query.data.split(":")[1]
    if choice == "back":
        buttons = [
            [InlineKeyboardButton("📂 Send to DM (Saved / Bot)", callback_data="dest_dm")],
            [InlineKeyboardButton("📢 Send to Channel/Group", callback_data="dest_custom")],
            [InlineKeyboardButton("❌ Cancel Setup", callback_data="cancel_setup")]
        ]
        await query.message.edit_text(
            "✨ <b>Destination Selection</b>\n\nWhere should I send the forwarded files?",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer()
        return

    if choice == "saved_messages":
        user_sess = await db.get_session(user_id)
        if not user_sess:
            return await query.answer(
                "⚠️ Saved Messages requires your account to be logged in (/login).\nPlease login first or choose 'Bot Private Chat'.",
                show_alert=True
            )
        PENDING_TASKS[user_id]["dest_chat_id"] = "me"
        PENDING_TASKS[user_id]["dest_thread_id"] = None
        PENDING_TASKS[user_id]["dest_title"] = "Saved Messages"
        PENDING_TASKS[user_id]["is_saved_messages"] = True
    else:
        PENDING_TASKS[user_id]["dest_chat_id"] = user_id
        PENDING_TASKS[user_id]["dest_thread_id"] = None
        PENDING_TASKS[user_id]["dest_title"] = "Bot Private Chat"
        PENDING_TASKS[user_id]["is_saved_messages"] = False

    await ask_for_speed(query.message)
    await query.answer()

@app.on_callback_query(filters.regex("^dest_"))
async def destination_callback(client: Client, query):
    user_id = query.from_user.id
    if user_id not in PENDING_TASKS:
        return await query.answer("❌ Task expired. Send link again.", show_alert=True)
    choice = query.data
    try:
        if choice == "dest_dm":
            buttons = [
                [InlineKeyboardButton("📥 Saved Messages (Your Account)", callback_data="dm_dest:saved_messages")],
                [InlineKeyboardButton("🤖 Bot Private Chat (Here)", callback_data="dm_dest:bot_chat")],
                [InlineKeyboardButton("🔙 Back to Destination Selection", callback_data="dm_dest:back")]
            ]
            await query.message.edit(
                "📂 <b>Direct Message (DM) Destination:</b>\n\n"
                "<i>Please select where you want the forwarded files delivered:</i>\n\n"
                "• 📥 <b>Saved Messages:</b> Direct to your personal Telegram Saved Messages cloud.\n"
                "• 🤖 <b>Bot Private Chat:</b> Direct here in this bot conversation.",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=enums.ParseMode.HTML
            )
            await query.answer()
            return
        elif choice == "dest_custom":
            saved_channels = await db.get_saved_channels(user_id, channel_type="dest")
            if saved_channels:
                PENDING_TASKS[user_id]["status"] = "waiting_channel_select"
                text, markup = build_channel_memory_ui(saved_channels, page=1, mode="select")
                await query.message.edit(text, reply_markup=markup)
            else:
                PENDING_TASKS[user_id]["status"] = "waiting_id"
                buttons = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_setup")]]
                await query.message.edit(
                    "📝 **Send the Target Chat ID or Link**\n\n"
                    "Examples:\n"
                    "• Channel/Group: `-100123456789`\n"
                    "• Specific Topic: `-100123456789/5`\n"
                    "• Public Link: `https://t.me/your_channel`\n\n"
                    "💡 <i>Tip: Channels you send to are automatically remembered in your Quick-Select memory!</i>\n"
                    "⚠️ __Make sure I am an admin in that chat with post permissions!__",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
            await query.answer()
    except Exception as e:
        print(f"[dest_callback notice]: {e}")
        try:
            await query.answer()
        except Exception:
            pass

# ======================================
# --- NAYA FORMAT MENU LOGIC START ---
# ======================================
def get_format_keyboard(current_formats):
    buttons = [
        [
            InlineKeyboardButton(f"{'✅' if 'Bold' in current_formats else '❌'} Bold", callback_data="format_toggle:Bold"),
            InlineKeyboardButton(f"{'✅' if 'Italic' in current_formats else '❌'} Italic", callback_data="format_toggle:Italic"),
            InlineKeyboardButton(f"{'✅' if 'Mono' in current_formats else '❌'} Mono", callback_data="format_toggle:Mono")
        ],
        [InlineKeyboardButton("✅ Default (Keep Original)", callback_data="format_none")],
        [InlineKeyboardButton("⏭ Next: Select Filters", callback_data="format_start")],
        [InlineKeyboardButton("🛑 Cancel Setup", callback_data="cancel_setup")]
    ]
    return InlineKeyboardMarkup(buttons)

async def show_format_menu(message_or_query, user_id):
    task_data = PENDING_TASKS.get(user_id)
    if not task_data: return
    
    if "text_format" not in task_data:
        task_data["text_format"] = [] 
    task_data["status"] = "waiting_format"
    
    kb = get_format_keyboard(task_data["text_format"])
    text = "📝 **Caption Formatting**\n\nChoose how your caption should look:\n*(Select multiple if you want, or leave Default)*"
    
    if isinstance(message_or_query, CallbackQuery):
        await message_or_query.message.edit_text(text, reply_markup=kb)
    else:
        await message_or_query.reply(text, reply_markup=kb, quote=True)

@app.on_callback_query(filters.regex("^format_toggle:(.+)"))
async def format_toggle_cb(client, query):
    user_id = query.from_user.id
    if user_id not in PENDING_TASKS: return await query.answer("Expired.", show_alert=True)
    fmt = query.data.split(":")[1]
    current = PENDING_TASKS[user_id].get("text_format", [])
    if fmt in current: current.remove(fmt)
    else: current.append(fmt)
    PENDING_TASKS[user_id]["text_format"] = current
    try: await query.message.edit_reply_markup(get_format_keyboard(current))
    except Exception: pass
    await query.answer()

@app.on_callback_query(filters.regex("^format_none$"))
async def format_none_cb(client, query):
    user_id = query.from_user.id
    if user_id not in PENDING_TASKS: return await query.answer("Expired.", show_alert=True)
    PENDING_TASKS[user_id]["text_format"] = []
    try: await query.message.edit_reply_markup(get_format_keyboard([]))
    except Exception: pass
    await query.answer()

@app.on_callback_query(filters.regex("^format_start$"))
async def format_start_cb(client, query):
    user_id = query.from_user.id
    if user_id not in PENDING_TASKS: return await query.answer("Expired.", show_alert=True)
    await show_filter_menu(query, user_id)
# ======================================
# --- NAYA FORMAT MENU LOGIC END ---
# ======================================

def get_filter_keyboard(current_types):
    buttons = []
    row = []
    for t in ALL_MSG_TYPES:
        icon = "✅" if t in current_types else "❌"
        row.append(InlineKeyboardButton(f"{icon} {t}", callback_data=f"filter_toggle:{t}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    buttons.append([
        InlineKeyboardButton("✅ Select All", callback_data="filter_all"), 
        InlineKeyboardButton("❌ Clear All", callback_data="filter_none")
    ])
    buttons.append([InlineKeyboardButton("🚀 Proceed / Save Setup", callback_data="filter_start")])
    buttons.append([InlineKeyboardButton("🛑 Cancel Setup", callback_data="cancel_setup")])
    return InlineKeyboardMarkup(buttons)

async def show_filter_menu(message_or_query, user_id):
    task_data = PENDING_TASKS.get(user_id)
    if not task_data: return
    
    if "allowed_types" not in task_data:
        task_data["allowed_types"] = ["Video", "Document"] 
    task_data["status"] = "waiting_filter"
    
    kb = get_filter_keyboard(task_data["allowed_types"])
    text = "🎛 **Content Filter**\n\nSelect the media types you want to forward or download.\n*(Default: Strictly Videos & Documents)*"
    
    if isinstance(message_or_query, CallbackQuery):
        await message_or_query.message.edit_text(text, reply_markup=kb)
    else:
        await message_or_query.reply(text, reply_markup=kb, quote=True)

@app.on_callback_query(filters.regex("^filter_toggle:(.+)"))
async def filter_toggle_cb(client, query):
    user_id = query.from_user.id
    if user_id not in PENDING_TASKS: return await query.answer("Expired.", show_alert=True)
    mtype = query.data.split(":")[1]
    allowed = PENDING_TASKS[user_id].get("allowed_types", ["Video", "Document"])
    if mtype in allowed: allowed.remove(mtype)
    else: allowed.append(mtype)
    PENDING_TASKS[user_id]["allowed_types"] = allowed
    try: await query.message.edit_reply_markup(get_filter_keyboard(allowed))
    except Exception: pass
    await query.answer()

@app.on_callback_query(filters.regex("^filter_all$"))
async def filter_all_cb(client, query):
    user_id = query.from_user.id
    if user_id not in PENDING_TASKS: return await query.answer("Expired.", show_alert=True)
    PENDING_TASKS[user_id]["allowed_types"] = ALL_MSG_TYPES.copy()
    try: await query.message.edit_reply_markup(get_filter_keyboard(ALL_MSG_TYPES))
    except Exception: pass
    await query.answer()

@app.on_callback_query(filters.regex("^filter_none$"))
async def filter_none_cb(client, query):
    user_id = query.from_user.id
    if user_id not in PENDING_TASKS: return await query.answer("Expired.", show_alert=True)
    PENDING_TASKS[user_id]["allowed_types"] = []
    try: await query.message.edit_reply_markup(get_filter_keyboard([]))
    except Exception: pass
    await query.answer()

@app.on_callback_query(filters.regex("^filter_start$"))
async def filter_start_cb(client, query):
    user_id = query.from_user.id
    if user_id not in PENDING_TASKS: return await query.answer("Expired.", show_alert=True)
    
    task_data = PENDING_TASKS.pop(user_id)
    allowed_types = task_data.get("allowed_types", ["Video", "Document"])
    
    if not allowed_types: 
        PENDING_TASKS[user_id] = task_data 
        return await query.answer("❌ Select at least one type!", show_alert=True)
        
    await query.answer("🚀 Proceeding...", show_alert=False)
    try: await query.message.edit_text("⏳ **Initializing Task... Please Wait!**")
    except Exception: pass
    
    delay = task_data.get("delay", 3)
    if task_data.get("mode") == "WATCHER":
        await finalize_watcher_setup(client, query.message, task_data, delay, user_id=user_id)
    else:
        await start_task_final(client, query.message, task_data, delay, user_id=user_id)

async def process_custom_destination(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else 0
    if not user_id: return
    try:
        if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.is_self:
            await message.reply_to_message.delete()
    except Exception:
        pass
    try:
        dest_chat_id = None
        dest_thread_id = None
        custom_title = None
        
        # 1. Forwarded message recognition (e.g. user forwarded a post from the destination channel)
        if getattr(message, "forward_from_chat", None):
            dest_chat_id = message.forward_from_chat.id
            custom_title = message.forward_from_chat.title
            dest_thread_id = getattr(message, "message_thread_id", None)
        elif getattr(message, "forward_from", None):
            dest_chat_id = message.forward_from.id
            custom_title = getattr(message.forward_from, "first_name", None)
        else:
            text = (message.text or message.caption or "").strip()
            if not text:
                await message.reply("❌ Please send a valid channel ID, link, or forward a message from the destination channel.", quote=True)
                return
            dest_chat_id, dest_thread_id, custom_title = parse_channel_input(text)
            
        if not dest_chat_id:
            await message.reply("❌ Invalid format. Please send a valid channel ID (e.g. `-100...`), @username, link, or forward a message from the channel.", quote=True)
            return

        try:
            canonical_chat_id, resolved_title, is_forum, resolve_error = await resolve_telegram_chat_title(client, user_id, dest_chat_id)
            if canonical_chat_id:
                dest_chat_id = canonical_chat_id
            title = custom_title or resolved_title or f"Chat {dest_chat_id}"
            if not is_forum:
                dest_thread_id = None
        except Exception as e:
            await message.reply(f"❌ **Invalid Chat ID/Link** or I am not an admin there.\nError: `{e}`", quote=True)
            return
            
        wait_msg = await message.reply("🔄 **Testing destination access...**", quote=True)
        success, error_msg = await test_destination_access(client, dest_chat_id, dest_thread_id, user_id=user_id)
        
        if not success:
            await wait_msg.edit(f"❌ **Setup Failed! Cannot write to destination.**\n\nPlease ensure I am an admin in `{title}` with posting permissions.\n**Error:** `{error_msg}`")
            return
            
        await wait_msg.delete()
            
        PENDING_TASKS[user_id]["dest_chat_id"] = dest_chat_id
        PENDING_TASKS[user_id]["dest_thread_id"] = dest_thread_id
        PENDING_TASKS[user_id]["dest_title"] = title
        PENDING_TASKS[user_id]["status"] = "waiting_speed"

        # Auto-save channel to user memory so it's remembered!
        try:
            await db.save_channel(
                user_id=user_id,
                channel_id=dest_chat_id,
                channel_title=title,
                channel_type="dest",
                thread_id=dest_thread_id
            )
        except Exception as e_save:
            print(f"[Memory AutoSave Notice]: {e_save}")

        await ask_for_speed(message)
    except Exception as e:
        await message.reply(f"❌ Invalid format. Please send a valid link or ID.\nError: `{e}`", quote=True)

async def ask_for_speed(message: Message):
    buttons = [
        [
            InlineKeyboardButton("⚡ 1 Sec", callback_data="speed_val:1"),
            InlineKeyboardButton("⚡ 2 Sec", callback_data="speed_val:2"),
            InlineKeyboardButton("⭐ 3 Sec (Default)", callback_data="speed_val:3")
        ],
        [
            InlineKeyboardButton("⏱️ 4 Sec", callback_data="speed_val:4"),
            InlineKeyboardButton("🛡️ 5 Sec", callback_data="speed_val:5"),
            InlineKeyboardButton("🛡️ 6 Sec", callback_data="speed_val:6")
        ],
        [
            InlineKeyboardButton("🛡️ 7 Sec", callback_data="speed_val:7"),
            InlineKeyboardButton("🛡️ 8 Sec", callback_data="speed_val:8"),
            InlineKeyboardButton("🛡️ 9 Sec", callback_data="speed_val:9")
        ],
        [
            InlineKeyboardButton("🛡️ 10 Sec", callback_data="speed_val:10"),
            InlineKeyboardButton("⚙️ Manual Custom", callback_data="speed_manual")
        ],
        [
            InlineKeyboardButton("❌ Cancel Setup", callback_data="cancel_setup")
        ]
    ]
    text = (
        "🚀 <b>Select Forwarding Delay & Speed</b>\n\n"
        "<pre><code>"
        "⚠️ DELAY SAFETY WARNING:\n"
        "• ⚡ 1s - 2s : FAST ➔ High Telegram FloodWait chances\n"
        "• ⭐ 3s (Default) : BALANCED ➔ Optimal speed & stability\n"
        "• 🛡️ 4s - 10s : SAFE ➔ Zero FloodWait risk for large batches"
        "</code></pre>\n\n"
        "<i>Tap a preset delay below or enter a custom duration:</i>"
    )
    if isinstance(message, Message) and message.from_user.is_bot:
        await message.edit(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=enums.ParseMode.HTML)
    else:
        await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=enums.ParseMode.HTML, quote=True)


# ==============================================================================
# --- CHANNEL MEMORY CALLBACKS & /channels COMMAND ---
# ==============================================================================



@app.on_callback_query(filters.regex(r"^(?:ch_page:(\d+):?(\w+)?:?(\w+)?|ch_pg:(\d+))"))
async def channel_memory_page_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied.", show_alert=True)
    
    try:
        match = query.matches[0]
        if match.group(1):
            page = int(match.group(1))
            arg2 = match.group(2) or "view"
            arg3 = match.group(3) or ""

            if arg2 in ["source", "dest"] and arg3 in ["view", "delete", "select"]:
                mode = arg3
                ch_type = arg2
            elif arg3 in ["source", "dest"]:
                mode = arg2
                ch_type = arg3
            elif "source" in arg2:
                mode = arg2
                ch_type = "source"
            elif "dest" in arg2:
                mode = arg2
                ch_type = "dest"
            else:
                mode = arg2
                ch_type = "dest"
        else:
            page = int(match.group(4))
            mode = "view"
            ch_type = "dest"
        
        page = max(1, page)
        saved_channels = await db.get_saved_channels(user_id, channel_type=ch_type)
        text, markup = build_channel_memory_ui(saved_channels, page=page, mode=mode, channel_type=ch_type)
        await query.message.edit_text(text, reply_markup=markup)
        await query.answer(f"Page {page} loaded ⚡")
    except Exception as e:
        print(f"[channel_memory_page_callback notice]: {e}")
        try:
            await query.answer()
        except Exception:
            pass

@app.on_callback_query(filters.regex(r"^ch_del:(-?\d+):?(\d+)?:?(\d+)?:?(\w+)?"))
async def channel_memory_delete_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied.", show_alert=True)

    match = query.matches[0]
    channel_id = int(match.group(1))
    thread_id = int(match.group(2)) if match.group(2) and match.group(2) != "0" else None
    page = int(match.group(3)) if match.group(3) else 1
    ch_type = match.group(4) or "dest"

    ch = await db.get_saved_channel(user_id, channel_id, thread_id=thread_id, channel_type=ch_type)
    title = ch.get("channel_title") if ch else f"Chat {channel_id}"

    deleted = await db.delete_saved_channel(user_id, channel_id, thread_id=thread_id, channel_type=ch_type)
    if deleted:
        await query.answer(f"🗑️ '{title[:25]}' removed from memory!", show_alert=True)
    else:
        await query.answer("Channel was already removed.", show_alert=False)

    saved_channels = await db.get_saved_channels(user_id, channel_type=ch_type)
    if not saved_channels:
        type_lbl = "SOURCE" if ch_type == "source" else "DESTINATION"
        add_btn = InlineKeyboardButton("➕ Add Source Channel", callback_data="prompt_add_source") if ch_type == "source" else InlineKeyboardButton("➕ Add Destination Channel", callback_data="prompt_add_dest")
        try:
            await query.message.edit_text(
                f"📁 <b>YOUR {type_lbl} CHANNEL MEMORY IS EMPTY</b>\n\nAll saved {type_lbl.lower()} channels have been removed from quick memory.",
                reply_markup=InlineKeyboardMarkup([[add_btn], [InlineKeyboardButton("❌ Close", callback_data="ch_close")]])
            )
        except Exception:
            pass
        return

    total_pages = max(1, math.ceil(len(saved_channels) / 10))
    if page > total_pages: page = total_pages
    text, markup = build_channel_memory_ui(saved_channels, page=page, mode="delete", channel_type=ch_type)
    try:
        await query.message.edit_text(text, reply_markup=markup)
    except Exception:
        pass

@app.on_callback_query(filters.regex(r"^ch_sel:(-?\d+):?(\d+)?"))
async def channel_memory_select_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied.", show_alert=True)
    if user_id not in PENDING_TASKS:
        return await query.answer("❌ Task expired. Send link again.", show_alert=True)

    match = query.matches[0]
    channel_id = int(match.group(1))
    thread_id = int(match.group(2)) if match.group(2) and match.group(2) != "0" else None

    ch = await db.get_saved_channel(user_id, channel_id, thread_id=thread_id, channel_type="dest")
    title = ch.get("channel_title") if ch else f"Chat {channel_id}"

    # Verify write access
    has_access, error_msg = await test_destination_access(client, channel_id, thread_id)
    if not has_access:
        return await query.message.edit_text(
            f"❌ <b>Destination Inaccessible</b>\n\n"
            f"I cannot post in <b>{html.escape(str(title))}</b> (<code>{channel_id}</code>).\n"
            f"<b>Details:</b> <code>{error_msg}</code>\n\n"
            f"<i>Make sure I am an administrator in that chat with post permissions.</i>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Saved Channels", callback_data="dest_custom")],
                [InlineKeyboardButton("🛑 Cancel", callback_data="cancel_setup")]
            ])
        )

    PENDING_TASKS[user_id]["dest_chat_id"] = channel_id
    PENDING_TASKS[user_id]["dest_thread_id"] = thread_id
    PENDING_TASKS[user_id]["dest_title"] = title
    PENDING_TASKS[user_id]["status"] = "waiting_speed"

    # Update use count
    await db.save_channel(user_id, channel_id, title, channel_type="dest", thread_id=thread_id)
    await ask_for_speed(query.message)

@app.on_callback_query(filters.regex(r"^ch_watch_sel:(-?\d+):?(\d+)?"))
async def channel_memory_watch_select_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied.", show_alert=True)

    match = query.matches[0]
    channel_id = int(match.group(1))
    thread_id = int(match.group(2)) if match.group(2) and match.group(2) != "0" else None

    ch = await db.get_saved_channel(user_id, channel_id, thread_id=thread_id, channel_type="source")
    raw_title = ch.get("channel_title") if ch else None
    title = await auto_resolve_channel_title(client, user_id, channel_id, raw_title, channel_type="source", thread_id=thread_id)

    # Generate canonical link representation for check_link_restriction
    clean_id = str(channel_id).replace("-100", "")
    link_repr = f"https://t.me/c/{clean_id}/{thread_id or 1}"
    is_restricted, status_text = await check_link_restriction(user_id, link_repr)

    PENDING_TASKS[user_id] = {
        "mode": "WATCHER",
        "link": link_repr,
        "source_chat_id": channel_id,
        "source_thread_id": thread_id,
        "source_title": title,
        "is_restricted": is_restricted,
        "status": "waiting_choice"
    }

    # Update use count
    await db.save_channel(user_id, channel_id, title, channel_type="source", thread_id=thread_id)

    buttons = [
        [InlineKeyboardButton("📂 Send to DM (Here)", callback_data="dest_dm")],
        [InlineKeyboardButton("📢 Send to Destination Channel", callback_data="dest_custom")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_setup")]
    ]

    await query.message.edit_text(
        f"👀 <b>Watcher Setup: Source Selected</b>\n\n"
        f"📥 <b>Source:</b> <b>{html.escape(str(title))}</b>\n"
        f"🆔 <code>{channel_id}</code>"
        + (f" (Topic: <code>{thread_id}</code>)\n" if thread_id else "\n")
        + f"{status_text}\n\n"
        "<b>Where should new incoming messages go?</b>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await query.answer(f"Source: {title[:20]}")

@app.on_callback_query(filters.regex(r"^ch_manual$"))
async def channel_memory_manual_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied.", show_alert=True)
    if user_id in PENDING_TASKS:
        PENDING_TASKS[user_id]["status"] = "waiting_id"
    
    buttons = [
        [InlineKeyboardButton("🔙 Back to Saved Channels", callback_data="dest_custom")],
        [InlineKeyboardButton("❌ Cancel Setup", callback_data="cancel_setup")]
    ]
    await query.message.edit_text(
        "📝 <b>Send the Target Destination Chat ID or Link</b>\n\n"
        "Examples:\n"
        "• Channel/Group: <code>-100123456789</code>\n"
        "• Specific Topic: <code>-100123456789/5</code>\n"
        "• Public Link: <code>https://t.me/your_channel</code>\n\n"
        "💡 <i>I will automatically save this channel to your quick destination memory!</i>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await query.answer()

@app.on_callback_query(filters.regex(r"^watch_manual$"))
async def watch_manual_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied.", show_alert=True)
    
    buttons = [
        [InlineKeyboardButton("➕ Add Source Channel", callback_data="prompt_add_source")],
        [InlineKeyboardButton("🔙 Back to Saved Sources", callback_data="ch_page:1:watch_select:source")],
        [InlineKeyboardButton("❌ Close", callback_data="ch_close")]
    ]
    await query.message.edit_text(
        "👀 <b>Manual Watcher Link Input</b>\n\n"
        "Simply send the watch command with the link directly in chat:\n\n"
        "• <code>/watch https://t.me/channel/123</code>\n"
        "• <code>/watch https://t.me/c/1234567890/45</code> <i>(with topic)</i>\n\n"
        "💡 <i>Or save it once with</i> <code>/addsourcechannel</code> <i>for 1-click watching!</i>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await query.answer()

@app.on_callback_query(filters.regex(r"^ch_inspect:(-?\d+):?(\d+)?:?(\d+)?:?(\w+)?"))
async def channel_memory_inspect_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied.", show_alert=True)

    match = query.matches[0]
    channel_id = int(match.group(1))
    thread_id = int(match.group(2)) if match.group(2) and match.group(2) != "0" else None
    page = int(match.group(3)) if match.group(3) else 1
    ch_type = match.group(4) or "dest"

    is_source = (ch_type == "source")
    type_label = "SOURCE" if is_source else "DESTINATION"

    ch = await db.get_saved_channel(user_id, channel_id, thread_id=thread_id, channel_type=ch_type)
    raw_title = ch.get("channel_title") if ch else None
    title = await auto_resolve_channel_title(client, user_id, channel_id, raw_title, channel_type=ch_type, thread_id=thread_id)
    use_count = ch.get("use_count", 1) if ch else 1
    last_used = ch.get("last_used") if ch else None
    last_used_str = last_used.strftime("%d-%b-%Y %I:%M %p") if isinstance(last_used, datetime.datetime) else "Recently"

    is_unres = not title or title.startswith("[Unresolved]") or title.startswith("Chat ")
    title_badge = " ⚠️ <i>(Unresolved)</i>" if is_unres else ""
    unres_note = "\n⚠️ <i>Real Telegram title not resolved yet. Ensure bot or connected account has access and tap 'Refresh Title' below.</i>\n" if is_unres else ""

    detail_text = (
        f"📢 <b>SAVED {type_label} CHANNEL DETAILS</b>\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"🏷️ <b>Channel Name:</b> {html.escape(str(title))}{title_badge}\n"
        f"🆔 <b>Channel ID:</b> <code>{channel_id}</code>\n"
        f"🧵 <b>Topic ID:</b> <code>{thread_id or 'General / None'}</code>\n"
        f"📂 <b>Channel Type:</b> <code>{type_label}</code>\n"
        f"📊 <b>Times Selected:</b> <code>{use_count}</code>\n"
        f"🕒 <b>Last Used:</b> <code>{last_used_str}</code>\n"
        + unres_note
        + "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "<i>What would you like to do with this saved channel?</i>"
    )

    buttons = []
    if is_source:
        buttons.append([InlineKeyboardButton("👀 Start Watching This Channel", callback_data=f"ch_watch_sel:{channel_id}:{thread_id or 0}")])
    buttons.append([
        InlineKeyboardButton("🔄 Refresh Title", callback_data=f"ch_refresh:{channel_id}:{thread_id or 0}:{page}:{ch_type}"),
        InlineKeyboardButton(f"🗑️ Delete Channel", callback_data=f"ch_promptdel:{channel_id}:{thread_id or 0}:{page}:{ch_type}")
    ])
    buttons.append([InlineKeyboardButton(f"🔙 Back to {type_label.capitalize()} Channels", callback_data=f"ch_page:{page}:{ch_type}_view:{ch_type}")])

    try:
        await query.message.edit_text(detail_text, reply_markup=InlineKeyboardMarkup(buttons))
    except Exception:
        pass
    await query.answer()

@app.on_callback_query(filters.regex(r"^ch_refresh:(-?\d+):?(\d+)?:?(\d+)?:?(\w+)?"))
async def channel_memory_refresh_title_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied.", show_alert=True)

    match = query.matches[0]
    channel_id = int(match.group(1))
    thread_id = int(match.group(2)) if match.group(2) and match.group(2) != "0" else None
    page = int(match.group(3)) if match.group(3) else 1
    ch_type = match.group(4) or "dest"

    await query.answer("🔄 Contacting Telegram to resolve real channel title...", show_alert=False)

    title = await auto_resolve_channel_title(client, user_id, channel_id, current_title=None, channel_type=ch_type, thread_id=thread_id, force=True)
    if title and not title.startswith("[Unresolved]") and not title.startswith("Chat "):
        await query.answer(f"✅ Resolved: {title[:30]}", show_alert=True)
    else:
        await query.answer("⚠️ Could not resolve title. Please ensure bot or connected account has access.", show_alert=True)

    await channel_memory_inspect_callback(client, query)

@app.on_callback_query(filters.regex(r"^ch_promptdel:(-?\d+):?(\d+)?:?(\d+)?:?(\w+)?"))
async def channel_memory_prompt_delete_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied.", show_alert=True)

    match = query.matches[0]
    channel_id = int(match.group(1))
    thread_id = int(match.group(2)) if match.group(2) and match.group(2) != "0" else None
    page = int(match.group(3)) if match.group(3) else 1
    ch_type = match.group(4) or "dest"

    is_source = (ch_type == "source")
    type_label = "SOURCE" if is_source else "DESTINATION"

    ch = await db.get_saved_channel(user_id, channel_id, thread_id=thread_id, channel_type=ch_type)
    title = ch.get("channel_title") if ch else f"Chat {channel_id}"

    confirm_text = (
        f"⚠️ <b>CONFIRM {type_label} CHANNEL DELETION</b>\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"Are you sure you want to permanently delete this {type_label.lower()} channel from saved memory?\n\n"
        f"📢 <b>Channel:</b> {html.escape(str(title))}\n"
        f"🆔 <b>ID:</b> <code>{channel_id}</code>\n"
        f"📂 <b>Type:</b> <code>{type_label}</code>\n\n"
        "<i>(Note: This only removes the quick-select shortcut from the bot. Your Telegram channel is completely safe.)</i>"
    )

    buttons = [
        [InlineKeyboardButton("✅ Yes, Confirm Delete", callback_data=f"ch_dodel:{channel_id}:{thread_id or 0}:{page}:{ch_type}")],
        [InlineKeyboardButton("❌ Cancel (Keep Channel)", callback_data=f"ch_inspect:{channel_id}:{thread_id or 0}:{page}:{ch_type}")]
    ]

    try:
        await query.message.edit_text(confirm_text, reply_markup=InlineKeyboardMarkup(buttons))
    except Exception:
        pass
    await query.answer()

@app.on_callback_query(filters.regex(r"^ch_dodel:(-?\d+):?(\d+)?:?(\d+)?:?(\w+)?"))
async def channel_memory_do_delete_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied.", show_alert=True)

    match = query.matches[0]
    channel_id = int(match.group(1))
    thread_id = int(match.group(2)) if match.group(2) and match.group(2) != "0" else None
    page = int(match.group(3)) if match.group(3) else 1
    ch_type = match.group(4) or "dest"

    is_source = (ch_type == "source")
    type_label = "SOURCE" if is_source else "DESTINATION"

    ch = await db.get_saved_channel(user_id, channel_id, thread_id=thread_id, channel_type=ch_type)
    title = ch.get("channel_title") if ch else f"Chat {channel_id}"

    deleted = await db.delete_saved_channel(user_id, channel_id, thread_id=thread_id, channel_type=ch_type)
    if deleted:
        await query.answer(f"🗑️ '{title[:25]}' removed from memory!", show_alert=True)
    else:
        await query.answer("Channel was already removed.", show_alert=False)

    saved_channels = await db.get_saved_channels(user_id, channel_type=ch_type)
    if not saved_channels:
        add_btn = InlineKeyboardButton("➕ Add Source Channel", callback_data="prompt_add_source") if is_source else InlineKeyboardButton("➕ Add Destination Channel", callback_data="prompt_add_dest")
        try:
            await query.message.edit_text(
                f"📁 <b>YOUR {type_label} CHANNEL MEMORY IS EMPTY</b>\n\nAll saved {type_label.lower()} channels have been removed from quick memory.",
                reply_markup=InlineKeyboardMarkup([[add_btn], [InlineKeyboardButton("❌ Close", callback_data="ch_close")]])
            )
        except Exception:
            pass
        return

    total_pages = max(1, math.ceil(len(saved_channels) / 10))
    if page > total_pages: page = total_pages
    text, markup = build_channel_memory_ui(saved_channels, page=page, mode="view", channel_type=ch_type)
    try:
        await query.message.edit_text(text, reply_markup=markup)
    except Exception:
        pass

@app.on_callback_query(filters.regex(r"^ch_close$"))
async def channel_memory_close_callback(client: Client, query: CallbackQuery):
    try:
        await query.message.delete()
    except Exception:
        await query.answer()

@app.on_message(filters.command(["viewsourcechannels", "viewsources", "viewsource", "sourcechannels", "sources"]) & filters.private)
async def view_source_channels_command(client: Client, message: Message):
    if not message.chat or message.chat.type != enums.ChatType.PRIVATE:
        return
    user_id = message.from_user.id if message.from_user else 0
    if not user_id or getattr(message.from_user, "is_bot", False):
        return
    if not is_authorized(user_id):
        return await message.reply("⛔ <b>Access Denied:</b> You are not authorized to use this bot.", quote=True)
        
    saved_channels = await db.get_saved_channels(user_id, channel_type="source")
    if not saved_channels:
        empty_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Source Channel", callback_data="prompt_add_source")],
            [InlineKeyboardButton("❌ Close", callback_data="ch_close")]
        ])
        return await message.reply(
            "📁 <b>YOUR SOURCE CHANNEL MEMORY IS EMPTY</b>\n\n"
            "You haven't saved any source channels yet.\n\n"
            "Source channels are the channels you watch with <code>/watch</code> or forward content from.\n"
            "You can save any channel using <code>/addsourcechannel</code> or the button below:\n\n"
            "<i>Your saved source channels will appear as quick-select buttons in <code>/watch</code> for 1-click real-time routing!</i>",
            reply_markup=empty_markup,
            quote=True
        )

    for ch in saved_channels[:10]:
        ch_id = ch["channel_id"]
        t = ch.get("channel_title")
        if not t or t.startswith("Chat ") or t.startswith("[Unresolved]") or t in ["Target Chat", "Destination", "Source"]:
            asyncio.create_task(auto_resolve_channel_title(client, user_id, ch_id, t, channel_type="source", thread_id=ch.get("thread_id")))

    text, markup = build_channel_memory_ui(saved_channels, page=1, mode="view", channel_type="source")
    await message.reply(text, reply_markup=markup, quote=True)

@app.on_message(filters.command(["viewdestinationchannels", "viewdestchannels", "viewdest", "viewdestination", "destchannels", "destinations"]) & filters.private)
async def view_destination_channels_command(client: Client, message: Message):
    if not message.chat or message.chat.type != enums.ChatType.PRIVATE:
        return
    user_id = message.from_user.id if message.from_user else 0
    if not user_id or getattr(message.from_user, "is_bot", False):
        return
    if not is_authorized(user_id):
        return await message.reply("⛔ <b>Access Denied:</b> You are not authorized to use this bot.", quote=True)
        
    saved_channels = await db.get_saved_channels(user_id, channel_type="dest")
    if not saved_channels:
        empty_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Destination Channel", callback_data="prompt_add_dest")],
            [InlineKeyboardButton("❌ Close", callback_data="ch_close")]
        ])
        return await message.reply(
            "📁 <b>YOUR DESTINATION CHANNEL MEMORY IS EMPTY</b>\n\n"
            "You haven't saved any destination channels yet.\n\n"
            "Whenever you send content to a channel or enter a channel ID/link, this bot automatically remembers it.\n"
            "You can also manually save any channel using <code>/adddestinationchannel</code> or the button below:\n\n"
            "<i>Your saved channels will appear as 10 quick-select buttons per page during forwarding setups!</i>",
            reply_markup=empty_markup,
            quote=True
        )

    for ch in saved_channels[:10]:
        ch_id = ch["channel_id"]
        t = ch.get("channel_title")
        if not t or t.startswith("Chat ") or t.startswith("[Unresolved]") or t in ["Target Chat", "Destination"]:
            asyncio.create_task(auto_resolve_channel_title(client, user_id, ch_id, t, channel_type="dest", thread_id=ch.get("thread_id")))

    text, markup = build_channel_memory_ui(saved_channels, page=1, mode="view", channel_type="dest")
    await message.reply(text, reply_markup=markup, quote=True)

@app.on_message(filters.command(["viewsavedchannels", "viewsaved", "savedchannels", "channels", "saved", "saved_channels"]) & filters.private)
async def legacy_saved_channels_command(client: Client, message: Message):
    if not message.chat or message.chat.type != enums.ChatType.PRIVATE:
        return
    user_id = message.from_user.id if message.from_user else 0
    if not user_id or getattr(message.from_user, "is_bot", False):
        return
    if not is_authorized(user_id):
        return await message.reply("⛔ <b>Access Denied:</b> You are not authorized to use this bot.", quote=True)
        
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 View Source Channels (Watch)", callback_data="ch_page:1:source_view:source")],
        [InlineKeyboardButton("📤 View Destination Channels (Forward)", callback_data="ch_page:1:dest_view:dest")],
        [InlineKeyboardButton("❌ Close", callback_data="ch_close")]
    ])
    await message.reply(
        "🗂️ <b>SAVED CHANNELS MANAGER</b>\n\n"
        "Channels are now organized into two dedicated categories:\n\n"
        "• 📥 <b>Source Channels:</b> Channels you monitor with <code>/watch</code>\n"
        "• 📤 <b>Destination Channels:</b> Channels you forward content to\n\n"
        "<i>Select which list you want to view:</i>",
        reply_markup=markup,
        quote=True
    )

async def process_add_channel_submission(client: Client, message: Message, raw_input: str, prompt_msg_id: int = None, channel_type: str = "dest"):
    user_id = message.from_user.id
    target_chat_id, dest_thread_id, custom_title = parse_channel_input(raw_input)
    ch_type = str(channel_type or "dest").lower()
    is_source = (ch_type == "source")
    type_label = "SOURCE" if is_source else "DESTINATION"

    if not target_chat_id and getattr(message, "forward_from_chat", None):
        target_chat_id = message.forward_from_chat.id
        custom_title = message.forward_from_chat.title
        dest_thread_id = getattr(message, "message_thread_id", None)
    elif not target_chat_id and getattr(message, "forward_from", None):
        target_chat_id = message.forward_from.id
        custom_title = getattr(message.forward_from, "first_name", None)

    if not target_chat_id:
        cmd_example = "/addsourcechannel" if is_source else "/adddestinationchannel"
        return await message.reply(
            f"❌ <b>Invalid Channel Input</b>\n\n"
            f"Please provide a valid channel ID (e.g. <code>-100xxxxxxxxxx</code>), @username, or link.\n\n"
            f"<b>Examples:</b>\n"
            f"• <code>{cmd_example} -1001234567890</code>\n"
            f"• <code>{cmd_example} -1001234567890 My Custom Name</code>\n"
            f"• <code>https://t.me/c/1234567890</code>\n"
            f"• <code>@channelusername</code>",
            quote=True
        )

    status_msg = await message.reply(f"🔄 <b>Auto-detecting {type_label.lower()} channel details...</b>", quote=True)

    # 1. Auto-recognize channel title and details
    canonical_chat_id, resolved_title, is_forum, resolve_error = await resolve_telegram_chat_title(client, user_id, target_chat_id)
    if canonical_chat_id:
        target_chat_id = canonical_chat_id
    if not is_forum:
        dest_thread_id = None

    is_unresolved = False
    if custom_title:
        final_title = custom_title
    elif resolved_title:
        final_title = resolved_title
    else:
        final_title = f"[Unresolved] Chat {target_chat_id}"
        is_unresolved = True

    # 2. Check permissions if destination
    has_access = True
    admin_note = ""
    if not is_source:
        has_access, error_msg = await test_destination_access(client, target_chat_id, dest_thread_id, user_id=user_id)
        admin_note = (
            "\n🤖 <b>Bot Status:</b> ✅ Administrator verified with post rights."
            if has_access
            else f"\n🤖 <b>Bot Status:</b> ⚠️ Bot is not an admin yet. Please add this bot to the channel with 'Post Messages' rights before forwarding content."
        )

    # 3. Save into MongoDB user memory
    try:
        await db.save_channel(
            user_id=user_id,
            channel_id=target_chat_id,
            channel_title=final_title,
            channel_type=ch_type,
            thread_id=dest_thread_id
        )
    except Exception as e_db:
        return await status_msg.edit(f"❌ <b>Database Error:</b> Failed to save channel: `{e_db}`")

    # 4. Count total saved channels for user
    total_saved = 0
    try:
        saved_list = await db.get_saved_channels(user_id, channel_type=ch_type)
        total_saved = len(saved_list)
    except Exception:
        pass

    help_note = (
        "<i>This channel will now appear in your saved source list during <code>/watch</code> setups for 1-tap real-time routing!</i>"
        if is_source
        else "<i>This channel will now appear in your saved destination list (10 buttons per page) during forwarding setups!</i>"
    )

    proceed_prompt = (
        "\n\n👉 <b>Active Task:</b> Would you like to proceed with this channel now?"
        if (user_id in PENDING_TASKS)
        else ""
    )

    unresolved_warning = ""
    if is_unresolved:
        has_sess = await db.get_session(user_id)
        if not has_sess:
            unresolved_warning = (
                "\n⚠️ <b>Resolution Notice:</b> Real channel title could not be fetched automatically.\n"
                "• The bot is not a member of this channel.\n"
                "💡 <i>Tip: For private channels, use <code>/login</code> to connect your Telegram account so the bot can access it!</i>\n"
            )
        else:
            unresolved_warning = (
                "\n⚠️ <b>Resolution Notice:</b> Real channel title could not be fetched automatically.\n"
                "• Neither this bot nor your connected account has access to this channel.\n"
                "💡 <i>Tip: Ensure your connected Telegram account has joined this channel. The real title will be automatically updated as soon as access is verified.</i>\n"
            )

    title_badge = " <i>(Custom Title)</i>" if custom_title else (" <i>(Verified via Telegram)</i>" if resolved_title else " ⚠️ <i>(Unresolved)</i>")

    success_text = (
        f"🎉 <b>{type_label} CHANNEL SAVED TO MEMORY!</b>\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"🏷️ <b>Channel Title:</b> <b>{html.escape(str(final_title))}</b>{title_badge}\n"
        f"🆔 <b>Channel ID:</b> <code>{target_chat_id}</code>\n"
        + (f"📌 <b>Topic ID:</b> <code>{dest_thread_id}</code>\n" if dest_thread_id else "")
        + admin_note
        + unresolved_warning
        + f"\n📊 <b>Total {type_label.capitalize()} Channels in Memory:</b> <code>{total_saved}</code>\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        + help_note
        + proceed_prompt
    )

    action_buttons = []
    if user_id in PENDING_TASKS:
        short_t = (final_title[:20] + "…") if len(final_title) > 20 else final_title
        if is_source:
            action_buttons.append([InlineKeyboardButton(f"🚀 Start Watching {short_t}", callback_data=f"ch_watch_sel:{target_chat_id}:{dest_thread_id or 0}")])
            action_buttons.append([
                InlineKeyboardButton("🔙 Back to Source Channels", callback_data="ch_page:1:watch_select:source"),
                InlineKeyboardButton("➕ Add Another Channel", callback_data="prompt_add_source")
            ])
        else:
            action_buttons.append([InlineKeyboardButton(f"🚀 Proceed with {short_t}", callback_data=f"ch_sel:{target_chat_id}:{dest_thread_id or 0}")])
            action_buttons.append([
                InlineKeyboardButton("🔙 Back to Select Channel", callback_data="dest_custom"),
                InlineKeyboardButton("➕ Add Another Channel", callback_data="prompt_add_dest")
            ])
        action_buttons.append([InlineKeyboardButton("❌ Cancel Setup", callback_data="cancel_setup")])
    else:
        if is_source:
            action_buttons.append([InlineKeyboardButton("👀 Start Watching Now", callback_data=f"ch_watch_sel:{target_chat_id}:{dest_thread_id or 0}")])
            action_buttons.append([
                InlineKeyboardButton("📋 View Source Channels", callback_data="ch_page:1:source_view:source"),
                InlineKeyboardButton("➕ Add Another", callback_data="prompt_add_source")
            ])
        else:
            action_buttons.append([
                InlineKeyboardButton("📑 View Destination Channels", callback_data="ch_page:1:dest_view:dest"),
                InlineKeyboardButton("➕ Add Another", callback_data="prompt_add_dest")
            ])
        action_buttons.append([InlineKeyboardButton("❌ Close", callback_data="ch_close")])

    await status_msg.edit(success_text, reply_markup=InlineKeyboardMarkup(action_buttons))

    if prompt_msg_id:
        try:
            await client.delete_messages(chat_id=message.chat.id, message_ids=prompt_msg_id)
        except Exception:
            pass

@app.on_message(filters.command(["addsourcechannel", "addsource", "savesourcechannel", "savesource"]) & filters.private)
async def add_source_channel_command(client: Client, message: Message):
    if not message.chat or message.chat.type != enums.ChatType.PRIVATE:
        return
    user_id = message.from_user.id if message.from_user else 0
    if not user_id or getattr(message.from_user, "is_bot", False):
        return
    if not is_authorized(user_id):
        return await message.reply("⛔ <b>Access Denied:</b> You are not authorized to use this bot.", quote=True)

    text = message.text.strip() if message.text else ""
    parts = text.split(maxsplit=1)
    
    if len(parts) > 1 and parts[1].strip():
        await process_add_channel_submission(client, message, parts[1].strip(), channel_type="source")
        return

    prompt_text = (
        "📥 <b>ADD SAVED SOURCE CHANNEL</b>\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "Please send the <b>Source Channel ID</b>, <b>@username</b>, or <b>invite link</b> of the channel you want to save for watching or forwarding.\n\n"
        "<b>Supported Formats:</b>\n"
        "• <code>-1001234567890</code>\n"
        "• <code>-1001234567890 Optional Custom Title</code>\n"
        "• <code>https://t.me/c/1234567890</code>\n"
        "• <code>https://t.me/c/1234567890/45</code> <i>(with Topic ID)</i>\n"
        "• <code>@channelusername</code>\n\n"
        "💡 <i>The bot will automatically recognize the channel's real name from Telegram!</i>\n\n"
        "<i>Or send</i> <code>/addsourcechannel -100xxxxxxxxxx</code> <i>anytime directly.</i>"
    )

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 View Source Channels", callback_data="ch_page:1:source_view:source")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_add_channel")]
    ])

    prompt_msg = await message.reply(prompt_text, reply_markup=markup, quote=True)
    PENDING_ADD_CHANNEL[user_id] = {"prompt_msg_id": prompt_msg.id, "channel_type": "source"}

@app.on_message(filters.command(["adddestinationchannel", "adddestination", "adddestchannel", "adddest", "savedestchannel", "savedestination"]) & filters.private)
async def add_destination_channel_command(client: Client, message: Message):
    if not message.chat or message.chat.type != enums.ChatType.PRIVATE:
        return
    user_id = message.from_user.id if message.from_user else 0
    if not user_id or getattr(message.from_user, "is_bot", False):
        return
    if not is_authorized(user_id):
        return await message.reply("⛔ <b>Access Denied:</b> You are not authorized to use this bot.", quote=True)

    text = message.text.strip() if message.text else ""
    parts = text.split(maxsplit=1)
    
    if len(parts) > 1 and parts[1].strip():
        await process_add_channel_submission(client, message, parts[1].strip(), channel_type="dest")
        return

    prompt_text = (
        "📤 <b>ADD SAVED DESTINATION CHANNEL</b>\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "Please send the <b>Destination Channel ID</b>, <b>@username</b>, or <b>invite link</b> of the channel you want to save.\n\n"
        "<b>Supported Formats:</b>\n"
        "• <code>-1001234567890</code>\n"
        "• <code>-1001234567890 Optional Custom Title</code>\n"
        "• <code>https://t.me/c/1234567890</code>\n"
        "• <code>https://t.me/c/1234567890/45</code> <i>(with Forum Topic ID)</i>\n"
        "• <code>@channelusername</code>\n\n"
        "💡 <i>The bot will automatically recognize the channel's real name from Telegram!</i>\n\n"
        "<i>Or send</i> <code>/adddestinationchannel -100xxxxxxxxxx</code> <i>anytime directly.</i>"
    )

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("📑 View Destination Channels", callback_data="ch_page:1:dest_view:dest")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_add_channel")]
    ])

    prompt_msg = await message.reply(prompt_text, reply_markup=markup, quote=True)
    PENDING_ADD_CHANNEL[user_id] = {"prompt_msg_id": prompt_msg.id, "channel_type": "dest"}

@app.on_message(filters.command(["addchannel", "addsavedchannel", "savechannel", "add_channel", "save_channel"]) & filters.private)
async def legacy_add_channel_command(client: Client, message: Message):
    if not message.chat or message.chat.type != enums.ChatType.PRIVATE:
        return
    user_id = message.from_user.id if message.from_user else 0
    if not user_id or getattr(message.from_user, "is_bot", False):
        return
    if not is_authorized(user_id):
        return await message.reply("⛔ <b>Access Denied:</b> You are not authorized to use this bot.", quote=True)

    text = message.text.strip() if message.text else ""
    parts = text.split(maxsplit=1)
    if len(parts) > 1 and parts[1].strip():
        await process_add_channel_submission(client, message, parts[1].strip(), channel_type="dest")
        return

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Add Source Channel (Watch)", callback_data="prompt_add_source")],
        [InlineKeyboardButton("📤 Add Destination Channel (Forward)", callback_data="prompt_add_dest")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_add_channel")]
    ])
    await message.reply(
        "➕ <b>ADD SAVED CHANNEL</b>\n\n"
        "Which type of channel would you like to save?\n\n"
        "• 📥 <b>Source Channel:</b> Channels you want to monitor with <code>/watch</code>\n"
        "• 📤 <b>Destination Channel:</b> Channels where forwarded files and messages go",
        reply_markup=markup,
        quote=True
    )

@app.on_callback_query(filters.regex(r"^prompt_add_source$"))
async def prompt_add_source_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied.", show_alert=True)
    
    prompt_text = (
        "📥 <b>ADD SAVED SOURCE CHANNEL</b>\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "Please send the <b>Source Channel ID</b>, <b>@username</b>, or <b>invite link</b> of the channel you want to save for watching.\n\n"
        "<b>Supported Formats:</b>\n"
        "• <code>-1001234567890</code>\n"
        "• <code>-1001234567890 Optional Custom Title</code>\n"
        "• <code>https://t.me/c/1234567890</code>\n"
        "• <code>https://t.me/c/1234567890/45</code> <i>(with Forum Topic ID)</i>\n"
        "• <code>@channelusername</code>\n\n"
        "💡 <i>The bot will automatically recognize the channel's real name from Telegram!</i>"
    )
    back_cb = "ch_page:1:watch_select:source" if user_id in PENDING_TASKS else "ch_page:1:source_view:source"
    cancel_cb = "cancel_setup" if user_id in PENDING_TASKS else "cancel_add_channel"
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Source Channels", callback_data=back_cb)],
        [InlineKeyboardButton("❌ Cancel", callback_data=cancel_cb)]
    ])
    try:
        await query.message.edit_text(prompt_text, reply_markup=markup)
        PENDING_ADD_CHANNEL[user_id] = {"prompt_msg_id": query.message.id, "channel_type": "source"}
    except Exception:
        pass

@app.on_callback_query(filters.regex(r"^prompt_add_dest$"))
async def prompt_add_dest_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied.", show_alert=True)
    
    prompt_text = (
        "📤 <b>ADD SAVED DESTINATION CHANNEL</b>\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "Please send the <b>Destination Channel ID</b>, <b>@username</b>, or <b>invite link</b> of the channel you want to save.\n\n"
        "<b>Supported Formats:</b>\n"
        "• <code>-1001234567890</code>\n"
        "• <code>-1001234567890 Optional Custom Title</code>\n"
        "• <code>https://t.me/c/1234567890</code>\n"
        "• <code>https://t.me/c/1234567890/45</code> <i>(with Forum Topic ID)</i>\n"
        "• <code>@channelusername</code>\n\n"
        "💡 <i>The bot will automatically recognize the channel's real name from Telegram!</i>"
    )
    back_cb = "dest_custom" if user_id in PENDING_TASKS else "ch_page:1:dest_view:dest"
    cancel_cb = "cancel_setup" if user_id in PENDING_TASKS else "cancel_add_channel"
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Destination Selection", callback_data=back_cb)],
        [InlineKeyboardButton("❌ Cancel", callback_data=cancel_cb)]
    ])
    try:
        await query.message.edit_text(prompt_text, reply_markup=markup)
        PENDING_ADD_CHANNEL[user_id] = {"prompt_msg_id": query.message.id, "channel_type": "dest"}
    except Exception:
        pass

@app.on_callback_query(filters.regex(r"^prompt_add_channel$"))
async def prompt_add_channel_legacy_callback(client: Client, query: CallbackQuery):
    await prompt_add_dest_callback(client, query)

@app.on_callback_query(filters.regex(r"^cancel_add_channel$"))
async def cancel_add_channel_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    PENDING_ADD_CHANNEL.pop(user_id, None)
    try:
        await query.message.edit_text(
            "❌ <b>Cancelled:</b> Adding channel was cancelled.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📑 View Saved Channels", callback_data="ch_pg:1")],
                [InlineKeyboardButton("❌ Close", callback_data="ch_close")]
            ])
        )
    except Exception:
        pass
    await query.answer("Cancelled.", show_alert=False)

@app.on_message(filters.command(["setcommands", "sync_commands", "updatecommands", "setbotcommands"]) & filters.private)
async def sync_commands_command(client: Client, message: Message):
    if not message.chat or message.chat.type != enums.ChatType.PRIVATE:
        return
    user_id = message.from_user.id if message.from_user else 0
    if not user_id or getattr(message.from_user, "is_bot", False):
        return
    if not is_authorized(user_id):
        return await message.reply("⛔ <b>Access Denied:</b> You are not authorized to use this bot.", quote=True)
        
    status_msg = await message.reply("🔄 <b>Synchronizing Telegram Bot Commands...</b>", quote=True)
    success = await register_bot_commands(client)
    if success:
        await status_msg.edit(
            "✅ <b>Telegram Bot Commands Synchronized Successfully!</b>\n\n"
            "The Telegram Menu button and <code>/</code> autocomplete list have been refreshed with all the latest commands:\n"
            "• <code>/addsourcechannel</code> - Add & save source channel\n"
            "• <code>/adddestinationchannel</code> - Add & save destination channel\n"
            "• <code>/viewsourcechannels</code> - View & manage saved sources\n"
            "• <code>/viewdestinationchannels</code> - View & manage saved destinations\n"
            "• and all system automation commands!\n\n"
            "<i>(Tip: If Telegram client app does not immediately refresh its cache, re-opening the chat or typing '/' triggers an instant cache reload.)</i>"
        )
    else:
        await status_msg.edit("❌ <b>Error:</b> Failed to sync bot commands with Telegram servers.")

@app.on_callback_query(filters.regex("^speed_"))
async def speed_callback(client: Client, query):
    user_id = query.from_user.id
    if user_id not in PENDING_TASKS:
        await query.answer("❌ Task expired.", show_alert=True)
        return
    
    choice = query.data
    task_data = PENDING_TASKS[user_id]
    
    if choice == "speed_manual":
        PENDING_TASKS[user_id]["status"] = "waiting_speed"
        await query.message.edit(
            "⏱ <b>Enter Custom Delay (Seconds)</b>\n\n"
            "<pre><code>"
            "Please send an integer number of seconds to wait between messages.\n"
            "Example: 15 or 30\n"
            "Higher delay prevents FloodWait on large channels."
            "</code></pre>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_setup")]])
        )
        await query.answer()
        return

    if choice.startswith("speed_val:"):
        val_sec = int(choice.split(":")[1])
        PENDING_TASKS[user_id]["delay"] = val_sec
        await query.answer(f"⏱ Delay set to {val_sec}s", show_alert=False)
        await show_format_menu(query, user_id)
        return

    if choice == "speed_default":
        PENDING_TASKS[user_id]["delay"] = 0 if task_data.get("mode") == "WATCHER" else 3
        await query.answer("⭐ Default 3s delay selected", show_alert=False)
        await show_format_menu(query, user_id)
        return

async def process_speed_input(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    if not text.isdigit(): return await message.reply("❌ Numbers only.")
    
    delay = int(text)
    if user_id in PENDING_TASKS:
        PENDING_TASKS[user_id]["delay"] = delay
        await show_format_menu(message, user_id)

async def finalize_watcher_setup(client, message, data, delay, user_id=None):
    if user_id is None:
        user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return 
    src_link = data['link']
    source_id = None
    source_title = "Unknown Source"
    
    user_session = await db.get_session(user_id)
    api_id = await db.get_api_id(user_id)
    api_hash = await db.get_api_hash(user_id)
    
    if not user_session:
        return await message.reply("❌ **You are not logged in.**\n\nWatcher mode requires your account to 'listen' for new messages.\nPlease /login first.")

    if user_id not in USER_CLIENTS:
        status_msg = await message.reply("🔄 **Starting your Listener Client...**")
        try:
            u_api = api_id or API_ID
            u_hash = api_hash or API_HASH
            
            new_client = Client(
                f"watcher_setup_{user_id}", 
                session_string=user_session, 
                api_id=u_api, 
                api_hash=u_hash, 
                workers=4, 
                ipv6=False,
                in_memory=True 
            )
            new_client.add_handler(MessageHandler(user_watcher_handler))
            
            await new_client.start()
            USER_CLIENTS[user_id] = new_client
            await status_msg.delete()
            
        except Exception as e:
            return await status_msg.edit(f"❌ **Session Error:** `{e}`\n\nTry /logout and /login again.")

    user_client = USER_CLIENTS[user_id]
    try:
        join_target = None
        if "t.me/c/" in src_link:
            chat_str = src_link.split("t.me/c/")[1].split("/")[0]
            source_id = int("-100" + chat_str)
            join_target = source_id
            try:
                chat = await user_client.get_chat(source_id)
                source_title = chat.title or str(source_id)
            except Exception:
                source_title = str(source_id)
        else:
            username = src_link.replace("https://", "").replace("http://", "").replace("t.me/", "").split("/")[0]
            chat = await user_client.get_chat(username)
            source_id = chat.id
            source_title = chat.title or str(source_id)
            join_target = username 
            
        try: 
            await user_client.join_chat(join_target)
        except UserAlreadyParticipant:
            pass 
        except Exception as e:
            print(f"⚠️ Auto-join warning for {join_target}: {e}")
            
        try:
            await user_client.get_chat_member(source_id, "me")
        except Exception:
            return await message.reply(f"❌ **Watcher Setup Blocked!**\n\nThe account you logged in with (`/login`) is **NOT** a member of `{source_title}`. Telegram blocks live updates to non-members.\n\n**Fix:** Please manually open Telegram on the account you logged into the bot with, and join the source channel first!")
        
    except Exception as e:
        return await message.reply(f"❌ **Could not access Source.**\nMake sure your User Account is a member of that channel.\nError: `{e}`")

    dest_chat_id = data.get('dest_chat_id')
    
    if dest_chat_id and dest_chat_id != user_id: 
        success, error_msg = await test_destination_access(app, dest_chat_id, data.get('dest_thread_id'))
        if not success:
            return await message.reply(f"❌ **Watcher Setup Failed!**\nCannot write to the target destination.\n**Error:** `{error_msg}`")

    await db.add_watcher(
        user_id=user_id,
        source_id=source_id,
        dest_id=dest_chat_id,
        source_thread=data.get('source_thread_id'),
        dest_thread=data.get('dest_thread_id'),
        delay=delay,
        is_restricted=data['is_restricted'],
        source_title=source_title,
        dest_title=data.get('dest_title', str(data.get('dest_chat_id'))),
        allowed_types=data.get('allowed_types'),
        text_format=data.get('text_format')
    )
    # Ensure source and destination channels are remembered in user memory
    try:
        await db.save_channel(
            user_id=user_id,
            channel_id=source_id,
            channel_title=source_title,
            channel_type="source",
            thread_id=data.get('source_thread_id')
        )
        if dest_chat_id and dest_chat_id != user_id:
            await db.save_channel(
                user_id=user_id,
                channel_id=dest_chat_id,
                channel_title=data.get('dest_title', str(dest_chat_id)),
                channel_type="dest",
                thread_id=data.get('dest_thread_id')
            )
    except Exception:
        pass
    
    fmt_str = ", ".join(data.get('text_format', [])) if data.get('text_format') else "Default"

    await message.reply(
        f"✅ **Watcher/Routing Active!**\n\n"
        f"👀 Source: `{source_title}`\n"
        f"📂 Source Topic: `{data.get('source_thread_id', 'All')}`\n"
        f"🎯 Destination: `{data.get('dest_title')}`\n"
        f"📂 Dest Topic: `{data.get('dest_thread_id', 'None')}`\n"
        f"⏱ Delay: `{delay}s`\n"
        f"📝 Format: `{fmt_str}`\n"
        f"🎛 Filter: `{', '.join(data.get('allowed_types', []))}`"
    )

def parse_log_channel(log_channel_str):
    if not log_channel_str:
        return None, None
    log_channel_str = str(log_channel_str).strip()
    topic_id = None
    
    if "t.me/c/" in log_channel_str:
        parts = log_channel_str.split("t.me/c/")[1].split("/")
        chat_part = parts[0].strip()
        if len(parts) > 1 and parts[1].strip().isdigit():
            topic_id = int(parts[1].strip())
        chat_id = int(f"-100{chat_part}") if not chat_part.startswith("-100") else int(chat_part)
        return chat_id, topic_id
    elif "t.me/" in log_channel_str:
        parts = log_channel_str.split("t.me/")[1].split("/")
        chat_part = parts[0].strip()
        if len(parts) > 1 and parts[1].strip().isdigit():
            topic_id = int(parts[1].strip())
        return chat_part, topic_id

    if "/" in log_channel_str:
        parts = log_channel_str.split("/")
        chat_part = parts[0].strip()
        if len(parts) > 1 and parts[1].strip().isdigit():
            topic_id = int(parts[1].strip())
    else:
        chat_part = log_channel_str.strip()

    clean_num = chat_part.lstrip("-")
    if clean_num.isdigit():
        num = int(chat_part)
        if num > 0:
            chat_id = int(f"-100{num}") if num > 10000000 else num
        elif not str(num).startswith("-100"):
            chat_id = int(f"-100{abs(num)}")
        else:
            chat_id = num
        return chat_id, topic_id
    else:
        return chat_part, topic_id

_LOG_FLOODWAIT_UNTIL = 0
_LAST_LOG_SENT = 0

async def send_log(text: str):
    global _LOG_FLOODWAIT_UNTIL, _LAST_LOG_SENT
    print(f"[BOT LOG] {text}")
    if not LOG_CHANNEL:
        return
    now = time.time()
    if now < _LOG_FLOODWAIT_UNTIL:
        return
    if now - _LAST_LOG_SENT < 2.0:
        return
    try:
        chat_id, topic_id = parse_log_channel(LOG_CHANNEL)
        if not chat_id:
            return
        await app.send_message(chat_id, text, reply_to_message_id=topic_id)
        _LAST_LOG_SENT = time.time()
    except FloodWait as fw:
        _LOG_FLOODWAIT_UNTIL = time.time() + fw.value + 5
        print(f"⚠️ [send_log] LOG_CHANNEL FloodWait: Pausing Telegram channel logging for {fw.value}s.")
    except Exception as e:
        print(f"❌ Failed to send log to Telegram: {e} | LOG_CHANNEL: '{LOG_CHANNEL}'. Please ensure Bot is an ADMIN in LOG_CHANNEL and ID has -100 prefix.")

DEFAULT_DISK_HEADROOM = 1536 * 1024 * 1024

async def check_disk_space(required_bytes=DEFAULT_DISK_HEADROOM):
    try:
        total, used, free = shutil.disk_usage(".")
        if free < required_bytes: 
            return False
        return True
    except Exception:
        return True

async def cleanup_watchdog():
    while True:
        await asyncio.sleep(600)
        try:
            download_path = Path("./downloads")
            if not download_path.exists(): continue

            current_time = time.time()
            max_age = 6 * 60 * 60

            for user_folder in download_path.iterdir():
                if not user_folder.is_dir():
                    continue
                try:
                    uid = int(user_folder.name)
                except (ValueError, TypeError):
                    continue  # album scratch folders are uuid-named
                active_tasks = ACTIVE_PROCESSES.get(uid, {})
                for task_folder in user_folder.iterdir():
                    if not task_folder.is_dir():
                        continue
                    # NEVER delete a folder that belongs to a task still running
                    if task_folder.name in active_tasks:
                        continue
                    if (current_time - task_folder.stat().st_mtime) > max_age:
                        await asyncio.to_thread(shutil.rmtree, task_folder, ignore_errors=True)
                        await send_log(f"🧹 **Auto-Cleanup:** Deleted stuck folder `{task_folder.name}` (Older than 6h)")
        except Exception as e:
            print(f"Watchdog Error: {e}")

async def start_task_final(client: Client, message_context: Message, task_data: dict, delay: int, user_id: int):
    if not await check_disk_space():
        msg = "⚠️ **Server Busy:** Disk is almost full. Please wait for other tasks to finish."
        if isinstance(message_context, Message):
             await message_context.reply(msg, quote=True)
        await send_log("🚨 **Critical:** Disk space low (under 1.5 GB free). Tasks rejected.")
        return

    if user_id not in SUPER_ADMINS and batch_temp.ACTIVE_TASKS.get(user_id, 0) >= MAX_CONCURRENT_TASKS_PER_USER:
        TASK_QUEUE[user_id].append({
            "client": client,
            "message": message_context,
            "data": task_data,
            "delay": delay
        })
        position = len(TASK_QUEUE[user_id])
        await message_context.reply(f"⏳ **Added to Queue:** Position #{position}\nTask will start automatically when your current tasks finish.", quote=True)
        return

    task_uuid = uuid.uuid4().hex
    dest = task_data.get("dest_title", "Direct Message")
    
    batch_temp.ACTIVE_TASKS[user_id] += 1

    auto_dl_active = await db.get_dl_status()
    auto_dl_notice = "\n⚠️ <i>Notice: Auto-Download is OFF (/toggledl to enable)</i>" if not auto_dl_active else ""
    start_msg = f"✅ <b>Task Started!</b>\nDestination: <code>{dest}</code>\nSpeed: <code>{delay}s</code> delay\nTask ID: <code>{task_uuid[:8]}</code>{auto_dl_notice}"
    try:
        if isinstance(message_context, Message):
            if message_context.from_user.is_bot:
                await message_context.edit(start_msg)
            else:
                await message_context.reply(start_msg)
    except Exception: pass
    
    await send_log(f"▶️ **Task Started**\nUser: `{user_id}`\nLink: `{task_data['link'][:40]}...`")

    if user_id not in ACTIVE_PROCESSES:
        ACTIVE_PROCESSES[user_id] = {}
    ACTIVE_PROCESSES[user_id][task_uuid] = {
        "user": task_data.get("dest_title", f"User({user_id})"),
        "dest_title_name": task_data.get("dest_title", "Direct Message"), 
        "item": task_data.get("link", "Unknown"),
        "started": time.time(),
        "total": 0,
        "fetched": 0,
        "success": 0,
        "duplicate": 0,
        "deleted": 0,
        "skipped": 0,
        "filtered": 0,
        "failed": 0,
        "current_status_text": "Starting Batch...",
        "confirming_cancel": False,
        "force_update_ui": False
    }
    
    is_restricted = task_data.get("is_restricted", False)

    targets = [{"dest_id": task_data.get("dest_chat_id"), "dest_thread": task_data.get("dest_thread_id"), "dest_title": dest}]
    asyncio.create_task(
        process_links_logic(
            client,
            message_context,
            task_data["link"],
            targets=targets,
            dest_title=dest, 
            delay=delay,
            acc_user_id=user_id,
            task_uuid=task_uuid,
            is_restricted=is_restricted,
            allowed_types=task_data.get('allowed_types'),
            text_format=task_data.get('text_format', [])
        )
    )   
    
async def process_links_logic(client: Client, message: Message, text: str, targets=None, dest_title="Direct Message", delay=3, acc_user_id=None, task_uuid=None, is_restricted=False, allowed_types=None, text_format=None):
    if text_format is None: text_format = []
    
    user_id = acc_user_id or (message.from_user.id if message.from_user else 0)
    user_mention = message.from_user.mention if getattr(message, "from_user", None) else f"User({user_id})"
    
    if user_id not in ACTIVE_PROCESSES: ACTIVE_PROCESSES[user_id] = {}
    if not task_uuid: task_uuid = uuid.uuid4().hex
    
    if task_uuid not in ACTIVE_PROCESSES[user_id]:
        ACTIVE_PROCESSES[user_id][task_uuid] = {}
        
    task_info = ACTIVE_PROCESSES[user_id][task_uuid]
    task_info.update({
        "user": user_mention, 
        "dest_title_name": dest_title,
        "item": text[:50]+"...", 
        "started": time.time(),
        "total": 0,
        "fetched": 0,
        "success": 0,
        "duplicate": 0,
        "deleted": 0,
        "skipped": 0,
        "filtered": 0,
        "failed": 0,
        "current_status_text": "Starting Batch...",
        "confirming_cancel": False,
        "force_update_ui": False
    })

    if "https://t.me/" in text:
        acc = None
        is_temp_client = False 
        status_message = None
        filter_thread_id = None 
        start_time = time.time()
        source_title = "Unknown Source"
        
        total_count = 0
        success_count = 0
        failed_count = 0
        was_cancelled = False

        try:
            clean_text = text.replace("https://", "").replace("http://", "").replace("t.me/", "").replace("c/", "")
            parts = clean_text.split("/")

            if len(parts) >= 3 and parts[1].isdigit(): 
                filter_thread_id = int(parts[1])

            user_data = await db.get_session(user_id)
            if not user_data:
                await message.reply("**/login First.**")
                return
            
            api_id = await db.get_api_id(user_id) or API_ID
            api_hash = await db.get_api_hash(user_id) or API_HASH
            
            is_temp_client = False
            if user_id in USER_CLIENTS and USER_CLIENTS[user_id].is_connected:
                acc = USER_CLIENTS[user_id]
            else:
                acc = Client(
                    f"task_{user_id}_{task_uuid}", 
                    session_string=user_data, 
                    api_hash=api_hash, 
                    api_id=api_id, 
                    no_updates=True,
                    workers=4,
                    sleep_threshold=60,
                    ipv6=False,
                    in_memory=True
                )
                await acc.start()
                is_temp_client = True

            try: chatid_check = int("-100" + parts[0]) if "https://t.me/c/" in text else parts[0]
            except Exception: chatid_check = parts[0]

            last_segment = parts[-1].strip()
            range_match = re.search(r"(\d+)\s*-\s*([a-zA-Z0-9]+)", text)
            
            if range_match:
                fromID = int(range_match.group(1))
                end_str = range_match.group(2).lower()
                
                if end_str == "all":
                    try:
                        async for last_msg in acc.get_chat_history(chatid_check, limit=1):
                            toID = last_msg.id
                    except Exception as e:
                        print(f"Failed to fetch last message for ALL: {e}")
                        toID = fromID
                else:
                    try: toID = int(end_str)
                    except Exception: toID = fromID
            else:
                fromID = toID = int(last_segment)

            if fromID > toID:
                fromID, toID = toID, fromID

            if fromID == toID:
                try:
                    media_group = await acc.get_media_group(chatid_check, fromID)
                    if media_group and len(media_group) > 1:
                        ids = [m.id for m in media_group]
                        fromID = min(ids)
                        toID = max(ids)
                except Exception:
                    pass

            # PER-TARGET RESUME: one destination must never hide another's gap
            target_cursors = {}
            for _t in targets:
                target_cursors[str(_t['dest_id'])] = await db.get_sync_progress(user_id, chatid_check, _t['dest_id'])
            saved_msg_id = min(target_cursors.values()) if target_cursors else 0

            skip_duplicates_amount = 0

            if target_cursors and saved_msg_id >= toID:
                skip_msg = (f"⏭ **DUPLICATE SKIPPED!**\n🤖 **Bot/User:** {user_mention}\n📂 **Source ID:** `{chatid_check}`\n🎯 **Destination:** `{dest_title}`\n✅ **Status:** Files up to ID `{toID}` are already synced to every destination.")
                try: await client.send_message(message.chat.id, skip_msg, reply_to_message_id=message.id)
                except Exception: pass
                if task_uuid in ACTIVE_PROCESSES.get(user_id, {}): del ACTIVE_PROCESSES[user_id][task_uuid]
                if is_temp_client: await acc.stop()
                return

            elif saved_msg_id >= fromID and saved_msg_id < toID:
                skip_duplicates_amount = (saved_msg_id - fromID) + 1
                fromID = saved_msg_id + 1
                resume_msg = (f"♻️ **AUTO-RESUME ACTIVATED!**\n🤖 **Bot/User:** {user_mention}\n📂 **Source ID:** `{chatid_check}`\n🎯 **Destination:** `{dest_title}`\n▶️ **Resuming From ID:** `{fromID}`")
                try: await client.send_message(message.chat.id, resume_msg, reply_to_message_id=message.id)
                except Exception: pass

            total_count = max(1, toID - fromID + 1)
            
            try:
                source_chat = await acc.get_chat(chatid_check)
                source_title = source_chat.title or "Private Chat"
            except Exception: pass

            task_info.update({
                "source_title": source_title, 
                "total": total_count, 
                "current": 0,
                "fetched": 0,
                "success": 0,
                "duplicate": 0, 
                "deleted": 0,
                "skipped": 0,
                "filtered": 0,
                "failed": 0,
                "current_status_text": "Starting Batch..."
            })

            status_text_header = f"**Batch Task Started!** 🚀\n"
            if filter_thread_id:
                status_text_header += f"**Filter:** `Topic {filter_thread_id} Only` 🎯\n"

            cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Cancel Task", callback_data=f"ask_cancel:{task_uuid}")]])

            try:
                initial_ui = generate_aesthetic_progress_ui(task_info, current_status="Starting Batch...", percent=0.0, footer_status="FORWARDING")
                status_message = await client.send_message(
                    message.chat.id,
                    initial_ui,
                    reply_markup=cancel_btn,
                    reply_to_message_id=message.id
                )
                task_info["status_msg_id"] = status_message.id
                task_info["status_chat_id"] = status_message.chat.id
            except Exception as e:
                pass

            last_update_time = time.time()
            inner_header = f"Filter: Topic {filter_thread_id} Only 🎯" if filter_thread_id else ""

            for index, msgid in enumerate(range(fromID, toID+1), start=1):
                loop_start_time = time.time()

                if task_uuid in ACTIVE_PROCESSES.get(user_id, {}):
                    ACTIVE_PROCESSES[user_id][task_uuid]["current"] = index

                if CANCEL_FLAGS.get(task_uuid):
                    was_cancelled = True; break

                is_success = False
                status_reason = "failed"
                active_targets = targets
                try:
                    chat_id = int("-100" + parts[0]) if "https://t.me/c/" in text else parts[0]
                    
                    active_targets = [t for t in targets if target_cursors.get(str(t['dest_id']), 0) < msgid]
                    if not active_targets:
                        is_success, status_reason = False, "duplicate"
                    else:
                        is_success, status_reason = await handle_private(
                            client, acc, message, chat_id, msgid, index, total_count,
                            status_message, active_targets, delay,
                            user_id, task_uuid,
                            is_restricted=is_restricted,
                            header_text=inner_header,
                            filter_thread_id=filter_thread_id,
                            allowed_types=allowed_types,
                            text_format=text_format
                        )
                
                except FloodWait as e:
                    wait_time = e.value + 5
                    wait_msg = f"⏳ **Rate Limiting Detected**\nSleeping for {wait_time} seconds..."
                    try: 
                        if not is_restricted and not task_info.get("confirming_cancel"): await client.edit_message_text(task_info.get("status_chat_id"), task_info.get("status_msg_id"), wait_msg)
                    except Exception: pass
                    await asyncio.sleep(wait_time)
                    continue
                    
                except Exception as e: 
                    print(f"Error processing {msgid}: {e}")
                    status_reason = "failed"

                task_info["fetched"] += 1
                if status_reason == "success": task_info["success"] += 1
                elif status_reason == "deleted": task_info["deleted"] += 1
                elif status_reason == "filtered": task_info["filtered"] += 1
                elif status_reason == "dl_disabled": task_info["skipped"] += 1
                elif status_reason == "skipped": task_info["skipped"] += 1
                elif status_reason == "duplicate": task_info["duplicate"] += 1
                elif status_reason == "cancelled": was_cancelled = True; break
                else: task_info["failed"] += 1

                if is_success: success_count += 1
                elif status_reason != "duplicate": failed_count += 1

                if index < total_count:
                    if is_success:
                        elapsed_time = time.time() - loop_start_time
                        actual_sleep = max(0, delay - elapsed_time)
                        await asyncio.sleep(actual_sleep)
                    else:
                        await asyncio.sleep(0.05)
                        
                if task_info["fetched"] % 100 == 0:
                    gc.collect()

                if not was_cancelled and is_success:
                    for _t in active_targets:
                        target_cursors[str(_t['dest_id'])] = msgid
                        await db.save_sync_progress(user_id, chatid_check, _t['dest_id'], msgid)

                needs_refresh = task_info.get("needs_refresh", False)
                force_update = task_info.get("force_update_ui", False)
                
                if not task_info.get("confirming_cancel"):
                    current_now = time.time()
                    if (task_info["fetched"] % 20 == 0) or msgid == toID or needs_refresh or force_update:
                        task_info["force_update_ui"] = False
                        percent = (task_info["fetched"] / total_count) * 100.0 if total_count > 0 else 0.0
                        
                        eta_str = "..."
                        if task_info["fetched"] > 0:
                            elapsed = current_now - start_time
                            if (task_info["fetched"] / elapsed) > 0:
                                eta_sec = int(((total_count - task_info["fetched"]) / (task_info["fetched"] / elapsed)))
                                eta_str = get_readable_time(eta_sec)
                            
                        fresh_status_ui = generate_aesthetic_progress_ui(
                            task_info, 
                            current_status=f"Forwarding...\n║┣⪼⏳ ETA: {eta_str}", 
                            percent=percent, 
                            footer_status="FORWARDING"
                        )
                        
                        try:
                            active_chat = task_info.get("status_chat_id", message.chat.id)
                            active_msg_id = task_info.get("status_msg_id", status_message.id if status_message else 0)
                            
                            if needs_refresh:
                                try: await client.delete_messages(active_chat, active_msg_id)
                                except Exception: pass
                                new_msg = await client.send_message(message.chat.id, fresh_status_ui, reply_markup=cancel_btn, reply_to_message_id=message.id)
                                task_info["status_msg_id"] = new_msg.id
                                task_info["status_chat_id"] = new_msg.chat.id
                                task_info["needs_refresh"] = False
                            elif active_msg_id:
                                await client.edit_message_text(
                                    chat_id=active_chat,
                                    message_id=active_msg_id,
                                    text=fresh_status_ui,
                                    reply_markup=cancel_btn
                                )
                            last_update_time = current_now
                        except Exception: 
                            pass
                    
        except Exception as e:
            import traceback
            print(f"❌ Task Crashed traceback:\n{traceback.format_exc()}")
            await send_log(f"❌ **Task Crashed**\nUser: `{user_id}`\nError: `{e}`")

        finally:
            if 'was_cancelled' in locals() and was_cancelled:
                footer_tag = "ᴄᴀɴᴄᴇʟʟᴇᴅ"
                status_word = "Cancelled"
                header = f"Batch was Cancelled! 🛑 {user_mention} ✨"
            else:
                footer_tag = "ᴄᴏᴍᴘʟᴇᴛᴇᴅ"
                status_word = "Completed"
                header = f"Batch was Completed! ✅ {user_mention} ✨"

            try:
                tot = task_info.get("total", 1)
                if tot == 0: tot = 1
                fet = task_info.get("fetched", 0)
                final_percent = (fet / tot * 100.0) if tot > 0 else 0.0
                if final_percent > 100.0: final_percent = 100.0
                
                final_status_ui = generate_aesthetic_progress_ui(
                    task_info,
                    current_status=status_word,
                    percent=final_percent,
                    footer_status=footer_tag
                )
                active_chat = task_info.get("status_chat_id", message.chat.id)
                active_msg_id = task_info.get("status_msg_id", status_message.id if status_message else 0)
                if active_msg_id:
                    await client.edit_message_text(chat_id=active_chat, message_id=active_msg_id, text=final_status_ui)
            except Exception: pass

            if task_uuid in ACTIVE_PROCESSES.get(user_id, {}):
                try: del ACTIVE_PROCESSES[user_id][task_uuid]
                except Exception: pass
            
            CANCEL_FLAGS.pop(task_uuid, None)

            batch_temp.ACTIVE_TASKS[user_id] -= 1
            if batch_temp.ACTIVE_TASKS[user_id] < 0: batch_temp.ACTIVE_TASKS[user_id] = 0
            
            if TASK_QUEUE[user_id]:
                next_item = TASK_QUEUE[user_id].pop(0)
                try:
                    asyncio.create_task(start_task_final(next_item["client"], next_item["message"], next_item["data"], next_item["delay"], user_id))
                except Exception as e:
                    print(f"❌ Queue Execution Failed for {user_id}: {e}")
                    batch_temp.ACTIVE_TASKS[user_id] -= 1 

            if acc and is_temp_client: 
                try: await acc.stop()
                except Exception: pass

            duration = time.time() - start_time
            time_taken_str = get_readable_time(int(duration))

            final_box = (
                f"╔════❰ {footer_tag} ❱═❍⊱❁۪۪\n"
                f"║╭━━━━━━━━━━━━━━━➣\n"
                f"║┣⪼ 📝 Task : {source_title} → {dest_title}\n"
                f"║┣⪼ ⏱ Time Taken: {time_taken_str}\n"
                f"║┣⪼ 📥 Total Requested: {total_count}\n"
                f"║┣⪼ ✅ Successful: {success_count}\n"
                f"║┣⪼ ❌ Failed/Skipped: {failed_count}\n"
                f"║╰━━━━━━━━━━━━━━━➣\n"
                f"╚════❰ ʙᴀᴛᴄʜ ᴄᴏᴍᴘʟᴇᴛᴇ ❱══❍⊱❁۪۪"
            )
            final_text = f"<b>{header}</b>\n\n<pre><code>{html.escape(final_box)}</code></pre>"
            
            try: await client.send_message(message.chat.id, final_text, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
            except Exception: pass

async def safe_copy_message(client_obj, **kwargs):
    """Copy a message and return the sent Message, or None on empty/failure.

    Pyrogram's Message.copy() logs "Empty messages cannot be copied." and returns None
    instead of raising, so callers must test the return value.
    """
    try:
        result = await client_obj.copy_message(**kwargs)
        return result
    except FloodWait as e:
        await asyncio.sleep(e.value + 5)
        try:
            return await client_obj.copy_message(**kwargs)
        except Exception as e2:
            print(f"Copy retry failed: {e2}")
            return None
    except Exception as e:
        print(f"Copy failed: {e}")
        return None


async def bridge_fast_copy(client, acc, source_chat_id, message_id, dest_chat_id, dest_thread_id,
                            caption, fallback_caption, reply_markup, is_bot_dm, user_id):
    """Userbot -> bot PM -> destination, with no download and verified delivery.

    Message.copy() logs "Empty messages cannot be copied." and returns None instead of raising;
    callers must treat None as failure, otherwise the bridge gets deleted without a final copy.
    """
    bot_user = getattr(client, "me", None) or getattr(app, "me", None)
    if not bot_user:
        return False
    bot_id = getattr(bot_user, "id", None)
    bot_target = f"@{bot_user.username}" if getattr(bot_user, "username", None) else bot_id
    bridge_msg = None
    success = False
    try:
        # Blank caption: the bridge must never look like a new source link to the save handler.
        bridge_msg = await acc.copy_message(chat_id=bot_target, from_chat_id=source_chat_id, message_id=message_id, caption=" ")
        if not bridge_msg or getattr(bridge_msg, "empty", False):
            print("[BRIDGE] bridge message is empty; aborting")
            return False

        sender_id = getattr(getattr(acc, "me", None), "id", None) or user_id
        print(f"[BRIDGE] id={bridge_msg.id} chat={bridge_msg.chat.id} empty={bridge_msg.empty} "
              f"media={bool(bridge_msg.media)} sender={sender_id} dest={dest_chat_id}")

        # Warm the peer cache; a cold access hash can make getMessages return an empty message.
        try:
            await client.get_chat(sender_id)
        except Exception as e:
            print(f"[BRIDGE] get_chat({sender_id}) failed: {e}")

        await asyncio.sleep(0.2)
        for attempt in range(2):
            result = await client.copy_message(
                chat_id=dest_chat_id, from_chat_id=sender_id, message_id=bridge_msg.id,
                reply_to_message_id=dest_thread_id, caption=caption,
                parse_mode=enums.ParseMode.HTML, reply_markup=reply_markup
            )
            if result:
                success = True
                return True
            print(f"[BRIDGE] copy attempt {attempt + 1} returned None")
            await asyncio.sleep(0.4)

        try:
            result = await client.copy_message(
                chat_id=dest_chat_id, from_chat_id=sender_id, message_id=bridge_msg.id,
                reply_to_message_id=dest_thread_id, caption=fallback_caption,
                reply_markup=reply_markup
            )
            if result:
                success = True
                return True
            print("[BRIDGE] fallback copy returned None")
        except Exception as e:
            print(f"[BRIDGE] fallback copy failed: {e}")

        try:
            forwarded = await client.forward_messages(
                chat_id=dest_chat_id, from_chat_id=sender_id, message_ids=bridge_msg.id
            )
            if forwarded:
                success = True
                return True
            print("[BRIDGE] forward returned None")
        except Exception as e:
            print(f"[BRIDGE] forward failed: {e}")

        return False
    except Exception as e:
        print(f"Bridge Copy Notice: {e}")
        return False
    finally:
        # On a Bot-PM destination keep the bridge if final delivery failed, so the file does not vanish.
        if bridge_msg and (success or not is_bot_dm):
            try:
                await bridge_msg.delete()
            except Exception:
                pass


async def handle_private(client: Client, acc, message: Message, chatid, msgid: int, index: int, total_count: int, status_message: Message, targets: list, delay, user_id, task_uuid=None, is_restricted=False, header_text="", filter_thread_id=None, allowed_types=None, text_format=None):
    if not task_uuid:
        task_uuid = "default"
        
    msg = None
    try:
        msg = await acc.get_messages(chatid, msgid)
    except UserNotParticipant:
        print(f"❌ [handle_private] UserNotParticipant: user session is not in chat {chatid} (msg {msgid})")
        return False, "failed"
    except Exception as e_get:
        print(f"❌ [handle_private] get_messages failed for chat {chatid} msg {msgid}: {e_get}")
        return False, "failed"

    if not msg or msg.empty: return False, "deleted"
    
    if filter_thread_id is not None:
        if getattr(msg, "message_thread_id", None) != filter_thread_id:
            return False, "filtered"

    msg_type = get_message_type(msg)
    if not msg_type: return False, "filtered"

    if allowed_types is not None and msg_type not in allowed_types:
        return False, "filtered"

    # 🛡️ STRICT FORWARDER FILTER: Drop part001-part999 splits & standalone .srt
    is_blocked, block_reason, matched_name = is_message_blocked(msg)
    if is_blocked:
        print(f"🚫 [BATCH/LINK DROP] Dropping message {msgid} due to {block_reason}: '{matched_name}'")
        return False, "filtered"

    if task_uuid and CANCEL_FLAGS.get(task_uuid): return False, "cancelled"

    try:
        if status_message:
            m_id = status_message.id
            chat_id = status_message.chat.id
            if f"{chat_id}:{m_id}:down" in PROGRESS: del PROGRESS[f"{chat_id}:{m_id}:down"]
            if f"{chat_id}:{m_id}:up" in PROGRESS: del PROGRESS[f"{chat_id}:{m_id}:up"]
    except Exception: pass

    original_caption = ""
    if msg_type == "Text" and msg.text:
        original_caption = msg.text.html
    elif msg.caption:
        original_caption = msg.caption.html
    else:
        if getattr(msg, "document", None) and getattr(msg.document, "file_name", None): original_caption = msg.document.file_name
        elif getattr(msg, "video", None) and getattr(msg.video, "file_name", None): original_caption = msg.video.file_name
        elif getattr(msg, "audio", None) and getattr(msg.audio, "file_name", None): original_caption = msg.audio.file_name
        elif msg_type == "Photo": original_caption = f"{msgid}.jpg"
        elif msg_type == "Voice": original_caption = f"{msgid}.ogg"

    # 🚀 SAFE SMART CAPTION CLONER (Direct HTML edit, completely safe for formatting)
    media_file_size = (
        getattr(getattr(msg, "document", None), "file_size", 0) or
        getattr(getattr(msg, "video", None), "file_size", 0) or
        getattr(getattr(msg, "audio", None), "file_size", 0) or
        getattr(getattr(msg, "photo", None), "file_size", 0) or
        getattr(getattr(msg, "animation", None), "file_size", 0) or
        getattr(getattr(msg, "voice", None), "file_size", 0) or
        0
    )

    clean_caption = smart_caption(original_caption, link_fallback=(msg_type != "Text"))
    if not clean_caption.strip() and msg_type in ["Video", "Document", "Audio"]:
        fallback_fn = (
            getattr(getattr(msg, "document", None), "file_name", None) or
            getattr(getattr(msg, "video", None), "file_name", None) or
            getattr(getattr(msg, "audio", None), "file_name", None) or
            ""
        )
        if fallback_fn:
            clean_caption = smart_caption(fallback_fn, link_fallback=True)

    clean_caption = apply_text_format(clean_caption, text_format)

    if msg_type != "Text":
        clean_caption = append_media_footer(clean_caption, media_file_size)
    clean_caption = await apply_user_replacements(clean_caption, user_id)

    # 🚀 EXACT TEXT MESSAGE CLONE WITH NEW CAPTION
    if "Text" == msg_type:
        for dest in targets:
            dest_target = dest['dest_id']
            dest_thread = dest.get('dest_thread')
            is_me = (dest_target == "me" or str(dest_target).lower() == "me")
            if is_me:
                try:
                    await acc.send_message(
                        chat_id="me",
                        text=clean_caption,
                        parse_mode=enums.ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                except Exception:
                    clean_caption_short = re.sub(r'<[^>]+>', '', clean_caption)[:4000]
                    try: await acc.send_message(chat_id="me", text=clean_caption_short, disable_web_page_preview=True)
                    except Exception: pass
            else:
                try: 
                    await client.send_message(
                        chat_id=dest_target, 
                        text=clean_caption,
                        reply_markup=msg.reply_markup,
                        reply_to_message_id=dest_thread,
                        parse_mode=enums.ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                except Exception as e_text:
                    if "TOO_LONG" in str(e_text):
                        clean_caption_short = re.sub(r'<[^>]+>', '', clean_caption)[:4000]
                        try: await client.send_message(chat_id=dest_target, text=clean_caption_short, reply_markup=msg.reply_markup, reply_to_message_id=dest_thread, disable_web_page_preview=True)
                        except Exception: pass
                    else:
                        try:
                            await acc.send_message(
                                chat_id=dest_target, 
                                text=clean_caption,
                                reply_markup=None if dest_target == user_id else msg.reply_markup,
                                reply_to_message_id=dest_thread,
                                parse_mode=enums.ParseMode.HTML,
                                disable_web_page_preview=True
                            )
                        except Exception as e_text2:
                            if "TOO_LONG" in str(e_text2):
                                clean_caption_short = re.sub(r'<[^>]+>', '', clean_caption)[:4000]
                                try: await acc.send_message(chat_id=dest_target, text=clean_caption_short, disable_web_page_preview=True)
                                except Exception: pass
        await db.inc_forward_stats(user_id, is_fast_copy=True, size_bytes=0, source_id=chatid)
        return True, "success"

    original_filename = "unknown_file"
    if getattr(msg, "document", None) and getattr(msg.document, "file_name", None): original_filename = msg.document.file_name
    elif getattr(msg, "video", None) and getattr(msg.video, "file_name", None): original_filename = msg.video.file_name
    elif getattr(msg, "audio", None) and getattr(msg.audio, "file_name", None): original_filename = msg.audio.file_name

    has_dotted_ext = bool(re.search(r'\.[a-zA-Z0-9]{2,4}(?:\.\d{2,4})?$', original_filename))
    auto_dl = await db.get_dl_status()

    # 🚀 FAST FORWARD EXACT CLONE WITH CAPTION REPLACEMENT
    # If the message or chat has explicit Telegram content protection, fast-copy is blocked by Telegram.
    # Otherwise, ALWAYS attempt server-side fast-copy via client/acc FIRST!
    # Even if restricted mode was selected, attempting copy_message takes 0.1s: if Telegram permits it,
    # it finishes in 1 second instead of taking 15 minutes to download/split/upload 4GB!
    is_content_protected = getattr(msg, "has_protected_content", False) or getattr(msg.chat, "has_protected_content", False)
    allow_fast_copy = not is_content_protected
    if allow_fast_copy:
        forward_success = False
        bot_user = getattr(client, "me", None) or getattr(app, "me", None)
        bot_id = getattr(bot_user, "id", None) if bot_user else None
        for dest in targets:
            dest_chat_id = dest['dest_id']
            try:
                if isinstance(dest_chat_id, str) and (dest_chat_id.startswith("-100") or dest_chat_id.lstrip("-").isdigit()):
                    dest_chat_id = int(dest_chat_id)
            except Exception:
                pass
            dest_thread_id = dest.get('dest_thread')
            is_me = (dest_chat_id == "me" or str(dest_chat_id).lower() == "me")
            is_bot_dm = (dest_chat_id == user_id or str(dest_chat_id) == str(user_id))
            fallback_cap = prepare_caption_fallback(clean_caption, media_file_size)

            if is_me:
                if await safe_copy_message(acc, chat_id="me", from_chat_id=chatid, message_id=msgid, reply_to_message_id=dest_thread_id, caption=clean_caption, parse_mode=enums.ParseMode.HTML, reply_markup=None):
                    forward_success = True
                continue

            # 1. Bot direct server-side copy
            if await safe_copy_message(client, chat_id=dest_chat_id, from_chat_id=chatid, message_id=msgid, reply_to_message_id=dest_thread_id, caption=clean_caption, parse_mode=enums.ParseMode.HTML, reply_markup=msg.reply_markup):
                forward_success = True
                continue

            # 2. Bot copy with a shortened/plain fallback caption
            if await safe_copy_message(client, chat_id=dest_chat_id, from_chat_id=chatid, message_id=msgid, reply_to_message_id=dest_thread_id, caption=fallback_cap, reply_markup=msg.reply_markup):
                forward_success = True
                continue

            # 3. Userbot direct copy (never for the bot's own PM: that would be Saved Messages)
            if not is_bot_dm:
                if await safe_copy_message(acc, chat_id=dest_chat_id, from_chat_id=chatid, message_id=msgid, reply_to_message_id=dest_thread_id, caption=clean_caption, parse_mode=enums.ParseMode.HTML, reply_markup=None):
                    forward_success = True
                    continue
                if await safe_copy_message(acc, chat_id=dest_chat_id, from_chat_id=chatid, message_id=msgid, reply_to_message_id=dest_thread_id, caption=fallback_cap, reply_markup=None):
                    forward_success = True
                    continue

            # 4. Bridge: userbot -> bot PM -> destination (zero download)
            if bot_id and await bridge_fast_copy(
                client, acc, chatid, msgid, dest_chat_id, dest_thread_id,
                clean_caption, fallback_cap, msg.reply_markup, is_bot_dm, user_id
            ):
                forward_success = True

        if forward_success:
            await db.inc_forward_stats(user_id, is_fast_copy=True, size_bytes=media_file_size, source_id=chatid)
            return True, "success"

    # 🌟 DOWNLOAD TOGGLE SAFETY CHECK
    if not auto_dl:
        if msg_type in ["Video", "Document"]:
            chat_title = getattr(msg.chat, "title", None) or str(chatid)
            print(f"[BOT LOG] 🚫 File Skipped (Auto-Download OFF) - Source: {chat_title} ({chatid}) - Msg ID: {msgid} - Type: {msg_type}")
        return False, "dl_disabled"

    task_folder_path = Path(f"./downloads/{user_id}/{task_uuid}/{msgid}/")
    task_folder_path.mkdir(parents=True, exist_ok=True)

    safe_filename = sanitize_filename(original_filename)
    if not safe_filename.strip(): safe_filename = f"{msgid}.dat"
    file_path_to_save = task_folder_path / safe_filename

    chat_for_status = status_message.chat.id if status_message else message.chat.id
    down_task = asyncio.create_task(downstatus(client, status_message, chat_for_status, index, total_count, header_text, task_uuid, user_id))
    file_path = None
    ph_path = None
    download_success = False

    split_limit = 2000 * 1024 * 1024 

    try: 
        for attempt in range(3):
            if task_uuid and CANCEL_FLAGS.get(task_uuid): return False, "cancelled"
            try:
                msg_fresh = await acc.get_messages(chatid, msgid)
                if msg_fresh.empty: return False, "deleted"
                
                file_size = getattr(msg_fresh.document, "file_size", 0) or getattr(msg_fresh.video, "file_size", 0) or getattr(msg_fresh.audio, "file_size", 0)

                if not await check_disk_space(int(file_size * 1.15) + 200 * 1024 * 1024):
                    print(f"🚫 [DISK] Insufficient free space for {file_size} bytes (msg {msgid}); aborting item.")
                    if down_task and not down_task.done():
                        down_task.cancel()
                    return False, "failed"

                if file_size > split_limit:
                    file_path = await acc.download_media(msg_fresh, file_name=str(file_path_to_save), progress=progress, progress_args=[task_uuid, "down"])
                    
                    if down_task and not down_task.done(): down_task.cancel()
                    parts = await split_file_python(file_path, chunk_size=1900*1024*1024)
                    
                    up_task = asyncio.create_task(upstatus(client, status_message, chat_for_status, index, total_count, header_text, task_uuid, user_id))
                    
                    async with USER_SEMAPHORES[user_id]:
                        async with SERVER_UPLOAD_LIMIT:
                            for part in parts:
                                if task_uuid and CANCEL_FLAGS.get(task_uuid): raise Exception("CANCELLED")
                                for dest in targets:
                                    dest_chat_id = dest['dest_id']
                                    dest_thread_id = dest.get('dest_thread')
                                    is_me = (dest_chat_id == "me" or str(dest_chat_id).lower() == "me")
                                    sender = acc if is_me else client
                                    retry_part = 0
                                    while retry_part < 5: 
                                        try:
                                            await sender.send_document(
                                                dest_chat_id, str(part), caption=clean_caption, 
                                                parse_mode=enums.ParseMode.HTML, 
                                                reply_markup=None if is_me else msg.reply_markup, 
                                                reply_to_message_id=dest_thread_id, 
                                                progress=progress, progress_args=[task_uuid, "up"]
                                            )
                                            break
                                        except FloodWait as e: 
                                            await asyncio.sleep(e.value + 5)
                                        except Exception as e: 
                                            if "CANCELLED" in str(e): raise e
                                            if "CAPTION_TOO_LONG" in str(e):
                                                clean_caption = prepare_caption_fallback(clean_caption, media_file_size)
                                            retry_part += 1
                                            await asyncio.sleep(3)
                                try: os.remove(part)
                                except Exception: pass
                    
                    if up_task and not up_task.done(): up_task.cancel()
                    try: os.remove(file_path)
                    except Exception: pass
                    await db.inc_forward_stats(user_id, is_fast_copy=False, size_bytes=file_size, source_id=chatid)
                    return True, "success" 
                else:
                    try:
                        file_path = await asyncio.wait_for(
                            acc.download_media(msg_fresh, file_name=str(file_path_to_save), progress=progress, progress_args=[task_uuid, "down"]),
                            timeout=1200
                        )
                    except asyncio.TimeoutError:
                        return False, "failed"
                
                try:
                    thumb = None
                    if msg_fresh.document and msg_fresh.document.thumbs: thumb = msg_fresh.document.thumbs[0]
                    elif msg_fresh.video and msg_fresh.video.thumbs: thumb = msg_fresh.video.thumbs[0]
                    elif msg_fresh.audio and msg_fresh.audio.thumbs: thumb = msg_fresh.audio.thumbs[0]
                    custom_user_thumb = await get_or_download_user_thumb(user_id, client)
                    if custom_user_thumb and os.path.exists(custom_user_thumb):
                        ph_path = custom_user_thumb
                    elif thumb:
                        ph_path = await acc.download_media(thumb.file_id, file_name=str(task_folder_path / "thumb.jpg"))
                except Exception: pass

                download_success = True
                break
            except FloodWait as e: 
                await asyncio.sleep(e.value + 5)
            except Exception as e:
                if "CANCELLED" in str(e): return False, "cancelled"
                await asyncio.sleep(5)

        if down_task and not down_task.done(): down_task.cancel()
        if not download_success:
            if allow_fast_copy:
                for dest in targets:
                    dest_chat_id = dest['dest_id']
                    dest_thread_id = dest.get('dest_thread')
                    if await safe_copy_message(client, chat_id=dest_chat_id, from_chat_id=chatid, message_id=msgid, reply_to_message_id=dest_thread_id, caption=clean_caption, parse_mode=enums.ParseMode.HTML, reply_markup=msg.reply_markup):
                        download_success = True
                    else:
                        fallback_cap = prepare_caption_fallback(clean_caption, media_file_size)
                        if await safe_copy_message(client, chat_id=dest_chat_id, from_chat_id=chatid, message_id=msgid, reply_to_message_id=dest_thread_id, caption=fallback_cap, reply_markup=msg.reply_markup):
                            download_success = True
                if download_success:
                    return True, "success"
            return False, "failed"
        if task_uuid and CANCEL_FLAGS.get(task_uuid): return False, "cancelled"


        up_task = asyncio.create_task(upstatus(client, status_message, chat_for_status, index, total_count, header_text, task_uuid, user_id))
        
        uploader = client 
        upload_success = False
        
        async def upload_to_dest(dest):
            dest_chat_id = dest['dest_id']
            dest_thread_id = dest.get('dest_thread')
            is_me = (dest_chat_id == "me" or str(dest_chat_id).lower() == "me")
            uploader = acc if is_me else client
            rmarkup = None if is_me else msg.reply_markup
            success_local = False
            async with SERVER_UPLOAD_LIMIT:
                async with USER_SEMAPHORES[user_id]:
                    retry_count = 0
                    while retry_count < 5: 
                        if task_uuid and CANCEL_FLAGS.get(task_uuid): break
                        try:
                            # 🚀 EXACT UPLOAD CLONE WITH CLEAN CAPTION AND DOTTED FILENAME
                            if "Document" == msg_type: await uploader.send_document(dest_chat_id, file_path, thumb=ph_path, caption=clean_caption, file_name=safe_filename, parse_mode=enums.ParseMode.HTML, reply_markup=rmarkup, reply_to_message_id=dest_thread_id, progress=progress, progress_args=[task_uuid,"up"])
                            elif "Video" == msg_type: await uploader.send_video(dest_chat_id, file_path, duration=getattr(msg.video, 'duration', 0), width=getattr(msg.video, 'width', 0), height=getattr(msg.video, 'height', 0), thumb=ph_path, caption=clean_caption, file_name=safe_filename, parse_mode=enums.ParseMode.HTML, reply_markup=rmarkup, reply_to_message_id=dest_thread_id, progress=progress, progress_args=[task_uuid,"up"])
                            elif "Audio" == msg_type: await uploader.send_audio(dest_chat_id, file_path, thumb=ph_path, caption=clean_caption, file_name=safe_filename, parse_mode=enums.ParseMode.HTML, reply_markup=rmarkup, reply_to_message_id=dest_thread_id, progress=progress, progress_args=[task_uuid,"up"])
                            elif "Photo" == msg_type: await uploader.send_photo(dest_chat_id, file_path, caption=clean_caption, parse_mode=enums.ParseMode.HTML, reply_markup=rmarkup, reply_to_message_id=dest_thread_id)
                            elif "Voice" == msg_type: await uploader.send_voice(dest_chat_id, file_path, caption=clean_caption, parse_mode=enums.ParseMode.HTML, reply_markup=rmarkup, reply_to_message_id=dest_thread_id, progress=progress, progress_args=[task_uuid,"up"])
                            elif "Animation" == msg_type: await uploader.send_animation(dest_chat_id, file_path, caption=clean_caption, parse_mode=enums.ParseMode.HTML, reply_markup=rmarkup, reply_to_message_id=dest_thread_id)
                            elif "Sticker" == msg_type: await uploader.send_sticker(dest_chat_id, file_path, reply_markup=rmarkup, reply_to_message_id=dest_thread_id)
                            success_local = True
                            break 
                        except FloodWait as e:
                            await asyncio.sleep(e.value + 5)
                        except Exception as e:
                            if "CANCELLED" in str(e): break
                            if "CAPTION_TOO_LONG" in str(e):
                                clean_caption = prepare_caption_fallback(clean_caption, media_file_size)
                            retry_count += 1
                            await asyncio.sleep(3)
            return success_local

        for dest in targets:
            if task_uuid and CANCEL_FLAGS.get(task_uuid): break
            if await upload_to_dest(dest):
                upload_success = True
        
        if up_task and not up_task.done(): up_task.cancel()
        if upload_success:
            await db.inc_forward_stats(user_id, is_fast_copy=False, size_bytes=media_file_size, source_id=chatid)
            return True, "success"
        return False, "failed"

    finally:
        try: await asyncio.to_thread(shutil.rmtree, task_folder_path, ignore_errors=True)
        except Exception: pass

try:
    from aiohttp import web
except ImportError:
    web = None

async def _koyeb_health_handler(request):
    return web.Response(text="OK", status=200)

async def start_koyeb_health_check(host: str = "0.0.0.0", port: int | str = 8080):
    if web is None:
        print("aiohttp not installed; Koyeb health check not started.")
        return
    try:
        port = int(os.environ.get("PORT", str(port)))
    except Exception:
        port = 8080
    app_web = web.Application()
    app_web.router.add_get("/", _koyeb_health_handler)
    app_web.router.add_get("/health", _koyeb_health_handler)
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    print(f"Starting Koyeb health check server on port {port}...")

from pyrogram.handlers import MessageHandler

WATCHER_LOCKS = {} 


# ==============================================================================
# --- FEATURE 1: CUSTOM RE-BRANDING & REPLACEMENT ENGINE (/replace) ---
# ==============================================================================

@app.on_message(filters.command(["replace", "rebrand", "replacements"]) & filters.private & ~filters.bot)
async def replace_command(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return await message.reply("⛔ Access Denied: You are not authorized.", quote=True)

    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        raw_text = args[1].strip()
        sep = None
        for s in ["->", "=>", "➜", "|"]:
            if s in raw_text:
                sep = s
                break
        
        if not sep:
            return await message.reply(
                "⚠️ <b>Invalid Syntax!</b>\n\n"
                "Use <code>-></code> to separate the target and replacement words.\n\n"
                "<b>Examples:</b>\n"
                "• <code>/replace @OldChannel -> @NewChannel</code>\n"
                "• <code>/replace https://t.me/old -> https://t.me/new</code>\n"
                "• <code>/replace [OldBranding] -> [MyBranding]</code>",
                quote=True
            )

        parts = raw_text.split(sep, 1)
        find_str = parts[0].strip()
        replace_str = parts[1].strip()

        if not find_str:
            return await message.reply("⚠️ The text to find cannot be empty!", quote=True)

        await db.add_replacement(user_id, find_str, replace_str)
        USER_REPLACEMENTS[int(user_id)] = await db.get_replacements(user_id)

        return await message.reply(
            "✅ <b>Re-Branding Rule Saved!</b>\n\n"
            f"🔍 <b>Find:</b> <code>{html.escape(find_str)}</code>\n"
            f"🎯 <b>Replace With:</b> <code>{html.escape(replace_str)}</code>\n\n"
            "💡 <i>All matching text/links in forwarded captions will now be automatically replaced!</i>",
            quote=True
        )

    rules = await db.get_replacements(user_id)
    USER_REPLACEMENTS[int(user_id)] = rules
    
    if not rules:
        return await message.reply(
            "🏷️ <b>Custom Word & Link Re-Branding Engine</b>\n\n"
            "You have no replacement rules saved yet.\n\n"
            "<b>How to add rules:</b>\n"
            "• <code>/replace @OldChannel -> @MyChannel</code>\n"
            "• <code>/replace https://t.me/spam -> https://t.me/mychannel</code>\n"
            "• <code>/replace [OldName] -> [MyBranding]</code>\n\n"
            "💡 <i>Every post forwarded via Watchers or Downloaded will be automatically re-branded!</i>",
            quote=True
        )

    text = (
        "🏷️ <b>Your Active Re-Branding Rules:</b>\n"
        f"📊 Total Rules: <code>{len(rules)}</code>\n"
        "─────────────────────────\n\n"
    )
    buttons = []
    for idx, r in enumerate(rules, 1):
        f_s = r.get("find", "")
        r_s = r.get("replace", "")
        text += f"<b>{idx}.</b> <code>{html.escape(f_s)}</code> ➜ <code>{html.escape(r_s)}</code>\n"
        if idx <= 6:
            buttons.append([InlineKeyboardButton(f"🗑️ Delete #{idx} ({f_s[:15]})", callback_data=f"del_rep:{idx-1}")])

    text += "\n─────────────────────────\n"
    text += "💡 <i>To add:</i> <code>/replace &lt;old&gt; -> &lt;new&gt;</code>\n"
    text += "🗑 <i>To clear all:</i> <code>/clearreplace</code>"

    buttons.append([InlineKeyboardButton("🗑 Clear All Rules", callback_data="clear_all_rep")])
    buttons.append([InlineKeyboardButton("❌ Close", callback_data="close_menu")])

    await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons), quote=True)

@app.on_message(filters.command(["clearreplace", "clearreplacements"]) & filters.private & ~filters.bot)
async def clear_replace_command(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return await message.reply("⛔ Access Denied.", quote=True)

    await db.clear_replacements(user_id)
    USER_REPLACEMENTS[int(user_id)] = []
    await message.reply("🗑️ <b>All Re-Branding rules have been cleared!</b>", quote=True)

@app.on_callback_query(filters.regex(r"^del_rep:(\d+)$"))
async def del_rep_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied.", show_alert=True)
    idx = int(query.matches[0].group(1))
    rules = await db.get_replacements(user_id)
    if 0 <= idx < len(rules):
        target_rule = rules[idx]
        await db.delete_replacement(user_id, target_rule["find"])
        USER_REPLACEMENTS[int(user_id)] = await db.get_replacements(user_id)
        await query.answer(f"🗑️ Deleted #{idx+1}", show_alert=True)
    else:
        await query.answer("Rule already deleted.", show_alert=False)
    
    # Refresh menu
    rules = await db.get_replacements(user_id)
    if not rules:
        return await query.message.edit_text("🏷️ <b>Re-Branding Engine:</b> All rules cleared! Use <code>/replace &lt;old&gt; -> &lt;new&gt;</code> to add.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close_menu")]]))
    
    text = f"🏷️ <b>Your Active Re-Branding Rules:</b>\n📊 Total Rules: <code>{len(rules)}</code>\n─────────────────────────\n\n"
    buttons = []
    for i, r in enumerate(rules, 1):
        text += f"<b>{i}.</b> <code>{html.escape(r.get('find',''))}</code> ➜ <code>{html.escape(r.get('replace',''))}</code>\n"
        if i <= 6:
            buttons.append([InlineKeyboardButton(f"🗑️ Delete #{i}", callback_data=f"del_rep:{i-1}")])
    buttons.append([InlineKeyboardButton("🗑 Clear All Rules", callback_data="clear_all_rep")])
    buttons.append([InlineKeyboardButton("❌ Close", callback_data="close_menu")])
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"^clear_all_rep$"))
async def clear_all_rep_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied.", show_alert=True)
    await db.clear_replacements(user_id)
    USER_REPLACEMENTS[int(user_id)] = []
    await query.answer("All rules cleared!", show_alert=True)
    await query.message.edit_text("🏷️ <b>Re-Branding Engine:</b> All rules cleared! Use <code>/replace &lt;old&gt; -> &lt;new&gt;</code> to add new rules.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close_menu")]]))


# ==============================================================================
# --- FEATURE 2: CUSTOM THUMBNAIL INSERTER (/setthumb) ---
# ==============================================================================

@app.on_message(filters.command(["setthumb", "setthumbnail"]) & filters.private & ~filters.bot)
async def set_thumb_command(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return await message.reply("⛔ Access Denied.", quote=True)

    photo = None
    if message.reply_to_message and message.reply_to_message.photo:
        photo = message.reply_to_message.photo
    elif message.photo:
        photo = message.photo

    if not photo:
        return await message.reply(
            "🖼️ <b>How to Set Custom Thumbnail:</b>\n\n"
            "Send or reply to any photo with <code>/setthumb</code> to save your channel's custom thumbnail.\n\n"
            "• <code>/viewthumb</code> - Preview your active thumbnail\n"
            "• <code>/delthumb</code> - Remove your thumbnail and revert to default",
            quote=True
        )

    status_msg = await message.reply("⏳ <i>Saving custom thumbnail...</i>", quote=True)
    try:
        thumb_dir = Path("./thumbnails")
        thumb_dir.mkdir(parents=True, exist_ok=True)
        thumb_path = thumb_dir / f"{user_id}.jpg"
        
        await client.download_media(photo.file_id, file_name=str(thumb_path))
        await db.set_user_thumb(user_id, photo.file_id)
        
        await status_msg.edit(
            "✅ <b>Custom Thumbnail Saved Successfully!</b>\n\n"
            "🖼️ This image will now automatically be attached as the cover thumbnail for all your uploaded videos and documents.\n\n"
            "Use <code>/viewthumb</code> to view or <code>/delthumb</code> to delete.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👀 View Thumbnail", callback_data="view_thumb_act")],
                [InlineKeyboardButton("🗑 Delete Thumbnail", callback_data="del_thumb_act")]
            ])
        )
    except Exception as e:
        await status_msg.edit(f"❌ <b>Failed to save thumbnail:</b> <code>{e}</code>")

@app.on_message(filters.command(["viewthumb", "mythumb", "thumbnail"]) & filters.private & ~filters.bot)
async def view_thumb_command(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return await message.reply("⛔ Access Denied.", quote=True)

    thumb_file = await get_or_download_user_thumb(user_id, client)
    if not thumb_file or not os.path.exists(thumb_file):
        return await message.reply(
            "⚠️ <b>No Custom Thumbnail Found</b>\n\n"
            "You haven't set a custom thumbnail yet.\n"
            "Reply to any image with <code>/setthumb</code> to save one!",
            quote=True
        )

    try:
        await client.send_photo(
            chat_id=message.chat.id,
            photo=str(thumb_file),
            caption=(
                "🖼️ <b>Your Active Custom Thumbnail</b>\n\n"
                "This thumbnail is automatically attached to all your uploaded videos and files.\n\n"
                "Use <code>/delthumb</code> if you want to delete it."
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑 Delete Thumbnail", callback_data="del_thumb_act")],
                [InlineKeyboardButton("❌ Close", callback_data="close_menu")]
            ])
        )
    except Exception as e:
        await message.reply(f"❌ Could not send thumbnail: {e}")

@app.on_message(filters.command(["delthumb", "clearthumb", "deletethumb"]) & filters.private & ~filters.bot)
async def del_thumb_command(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return await message.reply("⛔ Access Denied.", quote=True)

    thumb_path = Path(f"./thumbnails/{user_id}.jpg")
    deleted = False
    if thumb_path.exists():
        try:
            thumb_path.unlink()
            deleted = True
        except Exception:
            pass
    await db.del_user_thumb(user_id)
    
    if deleted:
        await message.reply("🗑️ <b>Custom Thumbnail Deleted!</b>\n\nReverted back to default media thumbnails.", quote=True)
    else:
        await message.reply("⚠️ You didn't have any custom thumbnail saved.", quote=True)

@app.on_callback_query(filters.regex(r"^del_thumb_act$"))
async def del_thumb_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied.", show_alert=True)
    thumb_path = Path(f"./thumbnails/{user_id}.jpg")
    if thumb_path.exists():
        try: thumb_path.unlink()
        except Exception: pass
    await db.del_user_thumb(user_id)
    await query.answer("Thumbnail deleted!", show_alert=True)
    try:
        await query.message.delete()
    except Exception:
        pass

@app.on_callback_query(filters.regex(r"^view_thumb_act$"))
async def view_thumb_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied.", show_alert=True)
    thumb_file = await get_or_download_user_thumb(user_id, client)
    if not thumb_file or not os.path.exists(thumb_file):
        return await query.answer("No custom thumbnail saved yet.", show_alert=True)
    await query.answer()
    try:
        await client.send_photo(
            chat_id=query.message.chat.id,
            photo=str(thumb_file),
            caption="🖼️ <b>Your Active Custom Thumbnail</b>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🗑 Delete Thumbnail", callback_data="del_thumb_act")]])
        )
    except Exception as e:
        await query.answer(f"Error: {e}", show_alert=True)


# ==============================================================================
# --- FEATURE 10: ANALYTICS & HEALTH DASHBOARD (/channelstats & /mywatchers) ---
# ==============================================================================

async def build_channel_stats_ui(user_id: int, user_first_name: str = "User"):
    cpu_pct = psutil.cpu_percent()
    mem = psutil.virtual_memory()
    used_mb = int((mem.total - mem.available) / (1024 * 1024))
    total_mb = int(mem.total / (1024 * 1024))
    mem_percent = mem.percent

    uptime_seconds = int(time.time() - BOT_START_TIME)
    uptime_str = get_readable_time(uptime_seconds)

    user_watchers = await db.get_user_watchers(user_id)
    watchers_count = len(user_watchers)
    total_targets = sum(len(w.get("targets", [])) for w in user_watchers)

    saved_sources = await db.get_saved_channels(user_id, channel_type="source")
    saved_dests = await db.get_saved_channels(user_id, channel_type="dest")
    sources_count = len(saved_sources)
    dests_count = len(saved_dests)

    rules = await db.get_replacements(user_id)
    rules_count = len(rules)

    file_id = await db.get_user_thumb(user_id)
    local_thumb = Path(f"./thumbnails/{user_id}.jpg").exists()
    has_thumb = "✅ Active" if (file_id or local_thumb) else "❌ None"

    f_stats = await db.get_forward_stats(user_id)
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    year, week_num, _ = now.isocalendar()
    week_str = f"{year}-W{week_num:02d}"
    month_str = now.strftime("%Y-%m")

    today_forwards = f_stats.get("daily", {}).get(today_str, 0)
    weekly_forwards = f_stats.get("weekly", {}).get(week_str, 0)
    monthly_forwards = f_stats.get("monthly", {}).get(month_str, 0)
    total_forwards = f_stats.get("total_forwards", 0)

    fast_copy_count = f_stats.get("fast_copy_count", 0)
    dl_count = f_stats.get("download_count", 0)
    total_ops = fast_copy_count + dl_count
    fast_ratio = round((fast_copy_count / max(1, total_ops)) * 100, 1) if total_ops > 0 else 100.0
    saved_gb = round((fast_copy_count * 200) / 1024, 2)

    card_body = (
        "📊 PERFORMANCE & CHANNEL INTELLIGENCE DASHBOARD\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"👤 Operator: {user_first_name} ({user_id})\n"
        f"⏱ System Uptime: {uptime_str}\n\n"
        "🛰️ SURVEILLANCE NETWORK:\n"
        f"├ 📥 Active Watchers: {watchers_count} channels\n"
        f"├ 🎯 Target Endpoints: {total_targets} destinations\n"
        f"├ 📂 Saved Sources: {sources_count} | Destinations: {dests_count}\n"
        f"├ 🏷️ Re-Branding Rules: {rules_count} active\n"
        f"└ 🖼️ Custom Thumbnail: {has_thumb}\n\n"
        "⚡ DELIVERY ENGINE METRICS:\n"
        f"├ 📅 Today's Deliveries: {today_forwards} posts\n"
        f"├ 🗓️ This Week's Deliveries: {weekly_forwards} posts\n"
        f"├ 📆 This Month's Deliveries: {monthly_forwards} posts\n"
        f"├ 📦 Lifetime Deliveries: {total_forwards} posts\n"
        f"├ 🚀 Fast-Copy Efficiency: {fast_ratio}% (Tag-Free Copy)\n"
        f"├ 📚 Smart Album Grouping: ✅ Active (Fast-Copy MTProto)\n"
        f"└ 🛡️ Server Bandwidth Saved: ~{saved_gb} GB (Sevalla Friendly)\n\n"
        "💻 SERVER HARDWARE TELEMETRY:\n"
        f"├ 🧠 RAM Allocation: {used_mb} MB / {total_mb} MB ({mem_percent}%)\n"
        f"├ ⚙️ CPU Workload: {cpu_pct}%\n"
        "└ 🟢 Engine Status: Online & Ultra-Fast\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
    )

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Refresh Dashboard", callback_data="refresh_stats_ui"),
            InlineKeyboardButton("📜 See Separate Channel History", callback_data="ch_hist:0")
        ],
        [
            InlineKeyboardButton("🛰️ View Watchers", callback_data="watchers_pg:0:0"),
            InlineKeyboardButton("🏷️ Re-Brand Rules", callback_data="view_rebrand_ui")
        ],
        [
            InlineKeyboardButton("🖼️ My Thumbnail", callback_data="view_thumb_act"),
            InlineKeyboardButton("❌ Close Dashboard", callback_data="close_menu")
        ]
    ])

    return f"<pre>{html.escape(card_body)}</pre>", markup

async def build_channel_history_ui(user_id: int, page: int = 0):
    user_watchers = await db.get_user_watchers(user_id)
    total_watchers = len(user_watchers)
    if total_watchers == 0:
        raw_empty = (
            "📜 SEPARATE CHANNEL FORWARD HISTORY\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
            "❌ No Active Surveillance Channels Found!\n\n"
            "You currently have 0 watchers active.\n"
            "Add channels with /watch to monitor individual delivery stats.\n\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
        )
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Overview", callback_data="refresh_stats_ui")]
        ])
        return f"<pre>{html.escape(raw_empty)}</pre>", markup

    page = max(0, min(page, total_watchers - 1))
    w = user_watchers[page]
    source_id = w.get("source_id")
    source_name = w.get("source_title") or w.get("source_name") or f"Channel {source_id}"
    targets = w.get("targets", [])
    if not targets and 'dest_id' in w:
        targets = [{"dest_id": w.get('dest_id'), "dest_title": w.get('dest_title')}]

    f_stats = await db.get_forward_stats(user_id)
    ch_key = str(source_id).replace(".", "_")
    ch_data = f_stats.get("channels", {}).get(ch_key, {})

    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    year, week_num, _ = now.isocalendar()
    week_str = f"{year}-W{week_num:02d}"
    month_str = now.strftime("%Y-%m")

    ch_today = ch_data.get("daily", {}).get(today_str, 0)
    ch_week = ch_data.get("weekly", {}).get(week_str, 0)
    ch_month = ch_data.get("monthly", {}).get(month_str, 0)
    ch_total = ch_data.get("total", 0)

    delay_sec = w.get("delay", 0)
    allowed = w.get("allowed_types", ["All Media"])
    types_str = ", ".join(allowed) if isinstance(allowed, list) else str(allowed)

    dest_summaries = []
    for t in targets[:3]:
        t_id = t.get("dest_id", "Unknown")
        t_title = t.get("dest_title", str(t_id))
        dest_summaries.append(f"• {t_title} ({t_id})")
    if len(targets) > 3:
        dest_summaries.append(f"• ...and {len(targets) - 3} more")
    dest_str = "\n".join(dest_summaries) if dest_summaries else "• None"

    card_body = (
        f"📊 CHANNEL TELEMETRY & AUDIT DOSSIER\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"📑 Page: {page + 1}/{total_watchers} • Channel: #{page + 1}\n\n"
        f"🛰️ SOURCE SURVEILLANCE CHANNEL:\n"
        f"├ 🏷️ Name: {source_name}\n"
        f"├ 🆔 Channel ID: {source_id}\n"
        f"├ ⏱ Delay: {delay_sec}s | 🎛 Filters: {types_str}\n"
        f"└ 🎯 Target Endpoints ({len(targets)}):\n{dest_str}\n\n"
        f"⚡ INDIVIDUAL CHANNEL FORWARD STATUS:\n"
        f"├ 📅 Today's Deliveries: {ch_today} posts\n"
        f"├ 🗓️ This Week's Deliveries: {ch_week} posts\n"
        f"├ 📆 This Month's Deliveries: {ch_month} posts\n"
        f"└ 📦 Lifetime Deliveries: {ch_total} posts\n\n"
        f"🟢 Engine Status: Online & Ultra-Fast\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
    )

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️ Prev", callback_data=f"ch_hist:{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"📄 {page + 1}/{total_watchers}", callback_data=f"ch_hist:{page}"))
    if page < total_watchers - 1:
        nav_row.append(InlineKeyboardButton("Next ▶️", callback_data=f"ch_hist:{page + 1}"))

    buttons = []
    if nav_row:
        buttons.append(nav_row)
    buttons.append([
        InlineKeyboardButton("🔄 Refresh Channel", callback_data=f"ch_hist:{page}"),
        InlineKeyboardButton("🔙 Back to Overview", callback_data="refresh_stats_ui")
    ])

    return f"<pre>{html.escape(card_body)}</pre>", InlineKeyboardMarkup(buttons)

@app.on_callback_query(filters.regex(r"^ch_hist:(\d+)$"))
async def channel_history_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied.", show_alert=True)
    match = re.match(r"^ch_hist:(\d+)$", query.data)
    page = int(match.group(1)) if match else 0
    text, markup = await build_channel_history_ui(user_id, page=page)
    try:
        await query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except Exception:
        pass
    await query.answer()

@app.on_message(filters.command(["channelstats", "watchstats", "channelhistory", "stats", "analytics"]) & filters.private & ~filters.bot)
async def channel_stats_command(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return await message.reply("⛔ Access Denied.", quote=True)

    text, markup = await build_channel_stats_ui(user_id, message.from_user.first_name)
    await message.reply(text, reply_markup=markup, quote=True, parse_mode=enums.ParseMode.HTML)

@app.on_message(filters.command(["mywatchers"]) & filters.private & ~filters.bot)
async def my_watchers_command(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return await message.reply("⛔ Access Denied.", quote=True)
    await list_watchers(client, message)

@app.on_callback_query(filters.regex(r"^refresh_stats_ui$"))
async def refresh_stats_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied.", show_alert=True)
    text, markup = await build_channel_stats_ui(user_id, query.from_user.first_name)
    try:
        await query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except Exception:
        pass
    await query.answer("Dashboard Refreshed ⚡")

@app.on_callback_query(filters.regex(r"^view_rebrand_ui$"))
async def view_rebrand_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return await query.answer("⛔ Access Denied.", show_alert=True)
    rules = await db.get_replacements(user_id)
    if not rules:
        return await query.answer("No rules yet! Use /replace <old> -> <new>", show_alert=True)
    await query.answer()
    text = f"🏷️ <b>Your Active Re-Branding Rules:</b>\n📊 Total Rules: <code>{len(rules)}</code>\n─────────────────────────\n\n"
    buttons = []
    for i, r in enumerate(rules, 1):
        text += f"<b>{i}.</b> <code>{html.escape(r.get('find',''))}</code> ➜ <code>{html.escape(r.get('replace',''))}</code>\n"
        if i <= 5:
            buttons.append([InlineKeyboardButton(f"🗑️ Delete #{i}", callback_data=f"del_rep:{i-1}")])
    buttons.append([InlineKeyboardButton("🔙 Back to Dashboard", callback_data="refresh_stats_ui")])
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))


# ==============================================================================
# --- FEATURE 4: SMART MEDIA ALBUMS GROUPING (Multiple Photos/Videos) ---
# ==============================================================================

async def process_media_album(client, chat_id, media_group_id, watcher, targets):
    album_key = f"{chat_id}_{media_group_id}"
    # Debounce delay: allow all parts of the album (up to 10 items) to arrive
    await asyncio.sleep(2.0)
    
    messages = ALBUM_BUFFERS.pop(album_key, [])
    if not messages:
        return

    # 🛡️ STRICT FORWARDER FILTER: Filter out blocked files from media album
    filtered_messages = []
    for m in messages:
        blocked, reason, matched_fn = is_message_blocked(m)
        if blocked:
            print(f"🚫 [ALBUM DROP] Dropping item {m.id} from album {media_group_id} ({reason}: '{matched_fn}')")
        else:
            filtered_messages.append(m)

    # Content-type filter must apply to albums too (the single-message path already does this)
    allowed_types = watcher.get('allowed_types')
    if allowed_types is not None:
        filtered_messages = [m for m in filtered_messages if get_message_type(m) in allowed_types]

    if not filtered_messages:
        print(f"🚫 [ALBUM DROP] All items in album {media_group_id} filtered out. Dropping album.")
        return

    messages = filtered_messages

    # Sort messages by message ID ascending to preserve correct media ordering
    messages.sort(key=lambda m: m.id)

    owner_id = watcher['user_id']
    delay = watcher.get('delay', 0)
    text_format = watcher.get('text_format', [])
    source_name = getattr(messages[0].chat, "title", str(chat_id)) or str(chat_id)

    # Extract primary caption from the album
    original_caption = ""
    for m in messages:
        if m.caption:
            original_caption = m.caption.html
            break

    clean_caption = smart_caption(original_caption, link_fallback=True)
    clean_caption = apply_text_format(clean_caption, text_format)

    clean_caption = await apply_user_replacements(clean_caption, owner_id)

    lock_key = f"watcher_{chat_id}_{owner_id}"
    if lock_key not in WATCHER_LOCKS:
        WATCHER_LOCKS[lock_key] = asyncio.Lock()

    async with WATCHER_LOCKS[lock_key]:
        if delay > 0:
            await asyncio.sleep(delay)

        msg_ids = [m.id for m in messages]
        is_content_protected = any(
            getattr(m, "has_protected_content", False) or getattr(m.chat, "has_protected_content", False)
            for m in messages
        )

        owner_client = USER_CLIENTS.get(owner_id)
        if not owner_client:
            user_session = await db.get_session(owner_id)
            if user_session:
                try: owner_client = await get_user_client(owner_id, user_session)
                except Exception: owner_client = None

        fast_copy_success = False

        if not is_content_protected:
            # Mode A: Fast-Copy MTProto ForwardMessages (ZERO Bandwidth, Intact Album Layout!)
            for t in targets:
                dest_id = t['dest_id']
                try: dest_id = int(dest_id)
                except (ValueError, TypeError): pass
                dest_thread = t.get('dest_thread')

                # Try Bot MTProto ForwardMessages first
                try:
                    peer = await app.resolve_peer(dest_id)
                    from_peer = await app.resolve_peer(chat_id)
                    req = raw.functions.messages.ForwardMessages(
                        to_peer=peer,
                        from_peer=from_peer,
                        id=msg_ids,
                        random_id=[random.randint(1, 2**31) for _ in msg_ids],
                        drop_author=True,
                        top_msg_id=dest_thread
                    )
                    r = await app.invoke(req)
                    await db.inc_forward_stats(owner_id, is_fast_copy=True, size_bytes=0)
                    fast_copy_success = True
                    continue
                except Exception:
                    pass

                # Try Userbot MTProto ForwardMessages
                if owner_client:
                    try:
                        peer = await owner_client.resolve_peer(dest_id)
                        from_peer = await owner_client.resolve_peer(chat_id)
                        req = raw.functions.messages.ForwardMessages(
                            to_peer=peer,
                            from_peer=from_peer,
                            id=msg_ids,
                            random_id=[random.randint(1, 2**31) for _ in msg_ids],
                            drop_author=True,
                            top_msg_id=dest_thread
                        )
                        r = await owner_client.invoke(req)
                        await db.inc_forward_stats(owner_id, is_fast_copy=True, size_bytes=0)
                        fast_copy_success = True
                        continue
                    except Exception:
                        pass

        if fast_copy_success:
            return

        # If Fast-copy failed (e.g. protected content channel):
        auto_dl = await db.get_dl_status()
        if not auto_dl:
            alert_text = (
                f"🚫 **Watcher Album Skipped (Download OFF)**\n"
                f"📂 **Source:** `{source_name}` (`{chat_id}`)\n"
                f"🆔 **Album Size:** `{len(messages)} items`\n"
                f"*(Fast-copy failed, downloading disabled to save bandwidth!)*"
            )
            try: await app.send_message(owner_id, alert_text)
            except Exception: pass
            return

        # Mode B: Clean Download & send_media_group
        notify_text = (
            f"⬇️ **Watcher Album Alert (Download Mode)**\n"
            f"📂 **Source:** `{source_name}`\n"
            f"🆔 **Album Size:** `{len(messages)} items`\n"
            f"*(Fast-copy failed, starting album download...)*"
        )
        try: await app.send_message(owner_id, notify_text)
        except Exception: pass

        album_uuid = uuid.uuid4().hex
        album_folder = Path(f"./downloads/{album_uuid}")
        album_folder.mkdir(parents=True, exist_ok=True)
        media_items = []
        total_album_bytes = 0

        try:
            dl_client = owner_client if owner_client else app
            for idx, m in enumerate(messages):
                m_type = get_message_type(m)
                f_size = (
                    getattr(getattr(m, "document", None), "file_size", 0) or
                    getattr(getattr(m, "video", None), "file_size", 0) or
                    getattr(getattr(m, "photo", None), "file_size", 0) or
                    getattr(getattr(m, "audio", None), "file_size", 0) or 0
                )
                total_album_bytes += f_size

                f_path = await dl_client.download_media(m, file_name=str(album_folder / f"item_{idx}"))
                if not f_path or not os.path.exists(f_path):
                    continue

                cap = clean_caption if idx == 0 else ""
                pm = enums.ParseMode.HTML if cap else None

                if m_type == "Photo":
                    media_items.append(InputMediaPhoto(media=str(f_path), caption=cap, parse_mode=pm))
                elif m_type == "Video":
                    media_items.append(InputMediaVideo(media=str(f_path), caption=cap, parse_mode=pm))
                elif m_type == "Document":
                    media_items.append(InputMediaDocument(media=str(f_path), caption=cap, parse_mode=pm))
                elif m_type == "Audio":
                    media_items.append(InputMediaAudio(media=str(f_path), caption=cap, parse_mode=pm))

            if media_items:
                for t in targets:
                    dest_id = t['dest_id']
                    try: dest_id = int(dest_id)
                    except (ValueError, TypeError): pass
                    dest_thread = t.get('dest_thread')
                    sent = False
                    try:
                        await app.send_media_group(chat_id=dest_id, media=media_items, reply_to_message_id=dest_thread)
                        sent = True
                    except Exception:
                        if owner_client:
                            try:
                                await owner_client.send_media_group(chat_id=dest_id, media=media_items, reply_to_message_id=dest_thread)
                                sent = True
                            except Exception:
                                pass
                    if sent:
                        await db.inc_forward_stats(owner_id, is_fast_copy=False, size_bytes=total_album_bytes)
        except Exception as e:
            try: await app.send_message(owner_id, f"❌ **Album forward failed:** <code>{e}</code>")
            except Exception: pass
        finally:
            await asyncio.to_thread(shutil.rmtree, album_folder, ignore_errors=True)

async def process_watcher_message(client, message):
    chat_id = message.chat.id
    topic_id = getattr(message, "message_thread_id", None)

    # MULTI-TENANT ISOLATION: resolve the bot user that owns this userbot client,
    # so two users watching the same source can never share routes.
    owner_uid = next((uid for uid, c in USER_CLIENTS.items() if c is client), None)
    if owner_uid is None:
        return
    
    watcher = await db.get_watcher(chat_id, topic_id, user_id=owner_uid)
    if not watcher:
        watcher = await db.get_watcher(chat_id, None, user_id=owner_uid)
        
    if not watcher: 
        return

    targets = watcher.get('targets', [])
    if not targets and 'dest_id' in watcher:
        targets = [{"dest_id": watcher['dest_id'], "dest_thread": watcher.get('dest_thread'), "dest_title": watcher.get('dest_title')}]
        
    if not targets: 
        return

    # 📚 Smart Media Albums Grouping Interceptor
    media_group_id = getattr(message, "media_group_id", None)
    if media_group_id:
        album_key = f"{chat_id}_{media_group_id}"
        if album_key not in ALBUM_BUFFERS:
            ALBUM_BUFFERS[album_key] = [message]
            asyncio.create_task(process_media_album(client, chat_id, media_group_id, watcher, targets))
        else:
            ALBUM_BUFFERS[album_key].append(message)
        return

    allowed_types = watcher.get('allowed_types', ["Video", "Document"])
    msg_type = get_message_type(message)
    
    if msg_type not in allowed_types: 
        return

    # 🛡️ STRICT FORWARDER FILTER: Check Telegram metadata & blocklist
    is_blocked, block_reason, matched_name = is_message_blocked(message)
    if is_blocked:
        print(f"🚫 [WATCHER DROP] Dropping message {message.id} due to {block_reason}: '{matched_name}'")
        return

    delay = watcher.get('delay', 0)
    owner_id = watcher['user_id']
    is_restricted = watcher.get('is_restricted', False)
    text_format = watcher.get('text_format', [])

    lock_key = f"watcher_{chat_id}_{owner_id}"
    if lock_key not in WATCHER_LOCKS:
        WATCHER_LOCKS[lock_key] = asyncio.Lock()

    async with WATCHER_LOCKS[lock_key]:
        if delay > 0:
            await asyncio.sleep(delay)

        is_content_protected = getattr(message, "has_protected_content", False) or getattr(message.chat, "has_protected_content", False)
        
        fallback_to_download = True 

        if not is_content_protected:
            fallback_to_download = False
            safe_source_id = message.chat.username if message.chat.username else chat_id
            
            # 🚀 EXACT TEXT WATCHER CLONE WITH CLEAN TEXT
            if msg_type == "Text":
                original_caption = message.text.html if message.text else ""
                clean_caption = smart_caption(original_caption)
                clean_caption = apply_text_format(clean_caption, text_format)
                clean_caption = await apply_user_replacements(clean_caption, owner_id)
                for t in targets:
                    dest_chat = t['dest_id']
                    dest_th = t.get('dest_thread')
                    sent = False
                    try: 
                        await app.send_message(
                            chat_id=dest_chat, 
                            text=clean_caption,
                            reply_markup=message.reply_markup,
                            reply_to_message_id=dest_th,
                            parse_mode=enums.ParseMode.HTML,
                            disable_web_page_preview=True
                        )
                        sent = True
                    except Exception:
                        pass
                    if not sent:
                        try:
                            await client.send_message(
                                chat_id=dest_chat, 
                                text=clean_caption,
                                reply_markup=None,
                                reply_to_message_id=dest_th,
                                parse_mode=enums.ParseMode.HTML,
                                disable_web_page_preview=True
                            )
                        except Exception as e_text:
                            if "TOO_LONG" in str(e_text):
                                clean_caption_short = re.sub(r'<[^>]+>', '', clean_caption)[:4000]
                                try: await client.send_message(chat_id=dest_chat, text=clean_caption_short, reply_markup=None, reply_to_message_id=dest_th, disable_web_page_preview=True)
                                except Exception: pass
                return

            original_caption = ""
            if message.caption:
                original_caption = message.caption.html
            else:
                if getattr(message, "document", None) and getattr(message.document, "file_name", None): original_caption = message.document.file_name
                elif getattr(message, "video", None) and getattr(message.video, "file_name", None): original_caption = message.video.file_name
                elif getattr(message, "audio", None) and getattr(message.audio, "file_name", None): original_caption = message.audio.file_name

            media_file_size = (
                getattr(getattr(message, "document", None), "file_size", 0) or
                getattr(getattr(message, "video", None), "file_size", 0) or
                getattr(getattr(message, "audio", None), "file_size", 0) or
                getattr(getattr(message, "photo", None), "file_size", 0) or
                getattr(getattr(message, "animation", None), "file_size", 0) or
                getattr(getattr(message, "voice", None), "file_size", 0) or
                0
            )

            clean_caption = smart_caption(original_caption, link_fallback=(msg_type != "Text"))
            if not clean_caption.strip() and msg_type in ["Video", "Document", "Audio"]:
                fallback_fn = (
                    getattr(getattr(message, "document", None), "file_name", None) or
                    getattr(getattr(message, "video", None), "file_name", None) or
                    getattr(getattr(message, "audio", None), "file_name", None) or
                    ""
                )
                if fallback_fn:
                    clean_caption = smart_caption(fallback_fn, link_fallback=True)

            clean_caption = apply_text_format(clean_caption, text_format)

            clean_caption = append_media_footer(clean_caption, media_file_size)
            clean_caption = await apply_user_replacements(clean_caption, owner_id)

            original_filename = "unknown_file"
            if getattr(message, "document", None) and getattr(message.document, "file_name", None): original_filename = message.document.file_name
            elif getattr(message, "video", None) and getattr(message.video, "file_name", None): original_filename = message.video.file_name
            elif getattr(message, "audio", None) and getattr(message.audio, "file_name", None): original_filename = message.audio.file_name

            has_dotted_ext = bool(re.search(r'\.[a-zA-Z0-9]{2,4}(?:\.\d{2,4})?$', original_filename))
            auto_dl = await db.get_dl_status()

            fallback_to_download = False
            for t in targets:
                    success = False
                    dest_id = t['dest_id']
                    try:
                        dest_id = int(dest_id)
                    except (ValueError, TypeError):
                        pass
                    dest_thread = t.get('dest_thread')
                    
                    # 🚀 FAST FORWARD CLONE WITHOUT FORWARDING TAG
                    # 1. Try bot copy_message (Bot API copyMessage creates a 100% clean copy without forward tag)
                    try: 
                        await app.copy_message(chat_id=dest_id, from_chat_id=safe_source_id, message_id=message.id, reply_to_message_id=dest_thread, caption=clean_caption, parse_mode=enums.ParseMode.HTML, reply_markup=None)
                        success = True
                    except FloodWait as fw1:
                        await asyncio.sleep(fw1.value + 5)
                        try:
                            await app.copy_message(chat_id=dest_id, from_chat_id=safe_source_id, message_id=message.id, reply_to_message_id=dest_thread, caption=clean_caption, parse_mode=enums.ParseMode.HTML, reply_markup=None)
                            success = True
                        except Exception: pass
                    except Exception as e1:
                        try:
                            fallback_cap = prepare_caption_fallback(clean_caption, media_file_size)
                            await app.copy_message(chat_id=dest_id, from_chat_id=safe_source_id, message_id=message.id, reply_to_message_id=dest_thread, caption=fallback_cap, reply_markup=None)
                            success = True
                            continue
                        except Exception: pass
                        try:
                            await client.get_chat(dest_id)
                        except Exception:
                            pass

                        # 2. Try user client copy_message (reply_markup must be None for user accounts)
                        try: 
                            await client.copy_message(chat_id=dest_id, from_chat_id=chat_id, message_id=message.id, reply_to_message_id=dest_thread, caption=clean_caption, parse_mode=enums.ParseMode.HTML, reply_markup=None)
                            success = True
                        except FloodWait as fw2:
                            await asyncio.sleep(fw2.value + 5)
                            try:
                                await client.copy_message(chat_id=dest_id, from_chat_id=chat_id, message_id=message.id, reply_to_message_id=dest_thread, caption=clean_caption, parse_mode=enums.ParseMode.HTML, reply_markup=None)
                                success = True
                                await db.inc_forward_stats(owner_id, is_fast_copy=True, size_bytes=media_file_size)
                                continue
                            except Exception: pass
                        except Exception as e2:
                            try:
                                fallback_cap = prepare_caption_fallback(clean_caption, media_file_size)
                                await client.copy_message(chat_id=dest_id, from_chat_id=chat_id, message_id=message.id, reply_to_message_id=dest_thread, caption=fallback_cap, reply_markup=None)
                                success = True
                                await db.inc_forward_stats(owner_id, is_fast_copy=True, size_bytes=media_file_size)
                                continue
                            except Exception: pass

                            # 3. Try MTProto ForwardMessages with drop_author=True (Zero Forward Header)
                            try:
                                to_peer = await client.resolve_peer(dest_id)
                                from_peer = await client.resolve_peer(chat_id)
                                r = await client.invoke(
                                    raw.functions.messages.ForwardMessages(
                                        to_peer=to_peer,
                                        from_peer=from_peer,
                                        id=[message.id],
                                        random_id=[client.rnd_id()],
                                        drop_author=True,
                                        top_msg_id=dest_thread or None
                                    )
                                )
                                success = True
                                await db.inc_forward_stats(owner_id, is_fast_copy=True, size_bytes=media_file_size)
                                if clean_caption and hasattr(r, "updates"):
                                    try:
                                        new_msg_id = None
                                        for upd in r.updates:
                                            if isinstance(upd, (raw.types.UpdateNewMessage, raw.types.UpdateNewChannelMessage)):
                                                new_msg_id = upd.message.id
                                                break
                                        if new_msg_id:
                                            try:
                                                await client.edit_message_caption(
                                                    chat_id=dest_id,
                                                    message_id=new_msg_id,
                                                    caption=clean_caption,
                                                    parse_mode=enums.ParseMode.HTML
                                                )
                                            except FloodWait as fw_edit:
                                                await asyncio.sleep(fw_edit.value + 5)
                                                try:
                                                    await client.edit_message_caption(
                                                        chat_id=dest_id,
                                                        message_id=new_msg_id,
                                                        caption=clean_caption,
                                                        parse_mode=enums.ParseMode.HTML
                                                    )
                                                except Exception: pass
                                            except Exception:
                                                fallback_cap = prepare_caption_fallback(clean_caption, media_file_size)
                                                await client.edit_message_caption(
                                                    chat_id=dest_id,
                                                    message_id=new_msg_id,
                                                    caption=fallback_cap
                                                )
                                    except Exception:
                                        pass
                            except FloodWait as fw3:
                                await asyncio.sleep(fw3.value + 5)
                            except Exception as e3:
                                # DO NOT forward with author tag!
                                # Let success remain False so Mode B (clean download & re-upload) executes!
                                pass
                    
                    if not success:
                        fallback_to_download = True

        if not fallback_to_download:
            return 
                
        owner_client = USER_CLIENTS.get(owner_id)
        if not owner_client: 
            return 

        try:
            source_name = message.chat.title or str(chat_id)
            dest_name = targets[0].get('dest_title', str(targets[0]['dest_id'])) if targets else "Unknown Target"
            
            auto_dl = await db.get_dl_status()
            if not auto_dl:
                alert_text = f"🚫 **Watcher Skipped (Download OFF)**\n📂 **Source:** `{source_name}` (`{chat_id}`)\n🎯 **Dest:** `{dest_name}`\n🆔 **Msg ID:** `{message.id}`\n*(Fast-copy failed, downloading disabled to save bandwidth!)*"
                try: await app.send_message(owner_id, alert_text)
                except Exception: pass
                if msg_type in ["Video", "Document"]:
                    await send_log(alert_text)
                return

            notify_text = f"⬇️ **Watcher Alert (Download Mode)**\n📂 **Source:** `{source_name}`\n🎯 **Dest:** `{dest_name}`\n🆔 **Msg ID:** `{message.id}`\n*(Fast-copy failed, starting manual download...)*"
            try: await app.send_message(owner_id, notify_text)
            except Exception: pass
            
            await send_log(notify_text)

            task_uuid = uuid.uuid4().hex
            if owner_id not in ACTIVE_PROCESSES: 
                ACTIVE_PROCESSES[owner_id] = {}
            ACTIVE_PROCESSES[owner_id][task_uuid] = {
                "user": f"Watcher({owner_id})",
                "dest_title_name": dest_name,
                "item": f"Live Download: ID {message.id}",
                "started": time.time()
            }

            dummy_status = None
            try:
                dummy_status = await app.send_message(owner_id, f"⏳ **Watcher processing ID `{message.id}` from `{source_name}`...**")
            except Exception:
                dummy_status = None

            try:
                await handle_private(
                    client=app,
                    acc=owner_client,
                    message=message, 
                    chatid=chat_id, 
                    msgid=message.id, 
                    index=1, 
                    total_count=1, 
                    status_message=dummy_status, 
                    targets=targets,
                    delay=0, 
                    user_id=owner_id, 
                    task_uuid=task_uuid,
                    is_restricted=True,
                    allowed_types=allowed_types,
                    text_format=text_format
                )
            finally:
                if task_uuid in ACTIVE_PROCESSES.get(owner_id, {}):
                    del ACTIVE_PROCESSES[owner_id][task_uuid]
                CANCEL_FLAGS.pop(task_uuid, None)
                if dummy_status:
                    try:
                        await dummy_status.delete()
                    except Exception:
                        pass
        except Exception as e:
            print(f"❌ [DEBUG WATCHER] Watcher Mode B Fail: {e}")
            
async def user_watcher_handler(client, message):
    await process_watcher_message(client, message)

async def cleanup_startup():
    folder = Path("./downloads")
    if folder.exists():
        try:
            shutil.rmtree(folder)
            print("🧹 Startup: Cleared temporary downloads folder.")
        except Exception as e:
            print(f"⚠️ Could not clean downloads folder: {e}")
    folder.mkdir(parents=True, exist_ok=True)

async def register_bot_commands(bot_client: Client) -> bool:
    try:
        public_commands = [
            BotCommand("start", "⚡ Check Bot Is Working Or Not"),
            BotCommand("help", "🔎 Check How To Use Bot"),
            BotCommand("addsourcechannel", "📥 Save Source Channel (Watch)"),
            BotCommand("adddestinationchannel", "📤 Save Destination Channel"),
            BotCommand("viewsourcechannels", "📋 View & Manage Saved Sources"),
            BotCommand("viewdestinationchannels", "📑 View & Manage Saved Destinations"),
            BotCommand("login", "📍 Login Your Telegram String Session"),
            BotCommand("accounts", "👥 Manage & Switch Multi-Accounts"),
            BotCommand("logout", "🚨 Logout Your Session"),
            BotCommand("dl", "🦥 Reply to the link to forward"),
            BotCommand("watch", "👀 To live forward"),
            BotCommand("unwatch", "🗑 Stop watching a source"),
            BotCommand("watchers", "📋 List your active watchers"),
            BotCommand("tasks", "📊 View live task progress"),
            BotCommand("toggledl", "🔛 Turn Auto-Download ON/OFF"),
            BotCommand("pixel", "✨ Bypass Pixeldrain Links"),
            BotCommand("cancel", "❌ Cancel Your Any Ongoing Task"),
            BotCommand("replace", "🏷️ Re-Brand Captions & Links"),
            BotCommand("setthumb", "🖼️ Set Custom Media Thumbnail"),
            BotCommand("viewthumb", "👀 View Saved Thumbnail"),
            BotCommand("delthumb", "🗑️ Delete Custom Thumbnail"),
            BotCommand("channelstats", "📊 Live Stats & Telemetry"),
            BotCommand("watchstats", "📊 Channel Intelligence Stats"),
            BotCommand("mywatchers", "👀 Quick View Active Watchers")
        ]

        admin_commands = public_commands + [
            BotCommand("broadcast", "🗞 Broadcast Message"),
            BotCommand("botstats", "🔎 Check User Stats"),
            BotCommand("kickuser", "🚪 Logout / Kick User Session"),
            BotCommand("status", "🦥 Check System Status"),
            BotCommand("log", "📄 Fetch Bot Logs"),
            BotCommand("setcommands", "🔄 Refresh Telegram Bot Commands")
        ]

        await bot_client.set_bot_commands(public_commands, scope=BotCommandScopeDefault())

        all_admins = set(SUPER_ADMINS)
        for admin_id in all_admins:
            try:
                await bot_client.set_bot_commands(
                    admin_commands, 
                    scope=BotCommandScopeChat(chat_id=admin_id)
                )
            except Exception:
                pass
        return True
    except Exception as e:
        print(f"[Register Commands Notice]: {e}")
        return False

async def main():
    global USER_CLIENTS
    
    await cleanup_startup()
    asyncio.create_task(cleanup_watchdog())

    await app.start()
    print("🤖 Bot Started")
    try:
        await db.init_indexes()
    except Exception as e:
        print(f"⚠️ [STARTUP] Database index initialisation failed: {e}")
    
    await register_bot_commands(app)
    
    active_watcher_users = set()
    cursor = await db.get_all_watchers()
    async for w in cursor:
        active_watcher_users.add(w['user_id'])

    for user_id in active_watcher_users:
        user_session = await db.get_session(user_id)
        if not user_session:
            continue
            
        try:
            if user_id in USER_CLIENTS: continue

            u_api = await db.get_api_id(user_id) or API_ID
            u_hash = await db.get_api_hash(user_id) or API_HASH
            
            user_client = Client(
                f"watcher_main_{user_id}", 
                session_string=user_session, 
                api_id=u_api, 
                api_hash=u_hash, 
                workers=4, 
                ipv6=False,
                in_memory=True
            )
            
            user_client.add_handler(MessageHandler(user_watcher_handler))
            await user_client.start()
            USER_CLIENTS[user_id] = user_client
            
            if db and db.db is not None:
                user_watchers = await db.db.watchers.find({'user_id': user_id}).to_list(length=None)
                for w in user_watchers:
                    target_source = w.get('source_id')
                    if target_source:
                        try:
                            await user_client.get_chat_member(target_source, "me")
                            await user_client.get_chat(target_source)
                            async for _ in user_client.get_chat_history(target_source, limit=1):
                                break
                        except Exception:
                            pass
            
        except Exception as e:
            print(f"⚠️ [STARTUP] Watcher restore failed for user {user_id}: {e}")
            try:
                await send_log(f"⚠️ **Watcher restore failed** for `{user_id}`: `{e}`")
            except Exception:
                pass

    if not AUTH_USERS:
        print("⚠️ [SECURITY] No ADMINS/AUTH_USERS configured — set OWNER_ID/ADMINS or ALLOW_OPEN_ACCESS=true.")
        try:
            await send_log("⚠️ **Security warning:** no ADMINS/AUTH_USERS configured; access is restricted unless ALLOW_OPEN_ACCESS=true.")
        except Exception:
            pass

    if SESSION_ENC_KEY_FALLBACK:
        print("⚠️ [SECURITY] SESSION_ENC_KEY not set — deriving the encryption key from BOT_TOKEN. Set SESSION_ENC_KEY explicitly; rotating BOT_TOKEN will make old sessions unreadable.")
        try:
            await send_log("⚠️ **Security warning:** SESSION_ENC_KEY not set; using a BOT_TOKEN-derived key. Set SESSION_ENC_KEY explicitly.")
        except Exception:
            pass
    elif not SESSION_ENC_KEY:
        print("⚠️ [SECURITY] No SESSION_ENC_KEY or BOT_TOKEN — MTProto sessions are stored unencrypted.")
        try:
            await send_log("⚠️ **Security warning:** no SESSION_ENC_KEY/BOT_TOKEN; MTProto sessions are stored unencrypted.")
        except Exception:
            pass

    asyncio.create_task(start_koyeb_health_check())
    await idle()
    
    await app.stop()
    for uid, client in USER_CLIENTS.items():
        try: await client.stop()
        except Exception: pass
        
if __name__ == "__main__":
    app.run(main())
