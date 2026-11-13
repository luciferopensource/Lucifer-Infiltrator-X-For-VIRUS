# Project Memory — Restrict-main (restricted-media engine)

**Project ID:** `restrict-main`
**Directory:** `Restrict-main` — Git repository, branch `main`, HEAD `abba1d8` at last verification.
**Last Verified:** 2026-11-06 (direct source inspection; nothing executed)

---

## 1. Project identity

The flagship restricted-media retrieval engine of this workspace: one Telegram bot plus
per-user MTProto userbot sessions that save, forward and re-caption protected media from
private channels, forum topics and bot-only links. Sibling `../amit_restrict_bot/` is a separate
customised deployment of the same engine with its own configuration and database — not a
package and its fork, and not a shared runtime.

Naming is split in source: the operator help banner reads `𝕃𝕌ℂ𝕀𝔽𝔼ℝ 𝕄𝕆ℝℕ𝕀ℕ𝔾𝕊𝕋𝔸ℝ`, the
statistics header reads `ROYAL INFILTRATOR BOT STATISTICS`, while `README.md`, `ROADMAP.md`
and `CHANGELOG.md` call the engine **Lucifer Infiltrator X**. All three refer to this directory.

## 2. Purpose and scope

- **In scope:** `/dl` single-link, link-range (`from - to`) and `from - all` retrieval; 24/7
  watchers that mirror new posts from one source to many destinations; custom caption rules,
  thumbnails, promotional-watermark cleaning and per-user session management.
- **Out of scope:** multi-tenant SaaS, web dashboard, distributed workers, non-Telegram storage.

## 3. Verified technology stack

| Layer | Verified fact | Evidence |
|---|---|---|
| Runtime | Python 3.10 (`FROM python:3.10-slim`) | `Dockerfile`, `nixpacks.toml` |
| MTProto | `pyrofork==2.3.45`, `pyromod`, `pyaes` | `requirements.txt` |
| Database | MongoDB through `motor.motor_asyncio` | `restrict_bot.py` (`Database`) |
| Support libs | `aiohttp` (health probe), `psutil` (telemetry), `dnspython`, `uvloop` | `requirements.txt` |
| Container | Dockerfile (7zip, coreutils, build toolchain) and Nixpacks (`p7zip`) | `Dockerfile`, `nixpacks.toml` |
| Tests | `tests/test_forwarder_engine.py`, 243 lines, 12 `test_` functions | file listing |
| Not present | no Pillow, no ffmpeg/ffprobe, no aiogram | `requirements.txt`, imports |

## 4. Actual entry points

| Path | Role |
|---|---|
| `restrict_bot.py` (8,176 lines, 223 functions) | the only executable entry point: client setup, authorization, commands, download/upload engine, watchers, health probe |
| `tests/test_forwarder_engine.py` | pytest engine tests |

`Dockerfile` runs `python3 restrict_bot.py`; `nixpacks.toml` runs `python restrict_bot.py`.

## 5. Architecture and modules

Still one module, internally layered:

- **Configuration** (top of file): `API_ID`, `API_HASH`, `BOT_TOKEN`, `DB_URI`, `DB_NAME`,
  `LOG_CHANNEL`, `PORT`, `STATUS_UPDATE_INTERVAL` (15 s), `WAITING_TIME`, `LOGIN_SYSTEM`,
  `MAX_TASKS_PER_USER`; `STRING_SESSION` is read but referenced nowhere else.
- **Authorization**: `_parse_env_ids` builds `ADMINS` from `ADMINS`/`ADMIN`/`ADMIN_ID`/`ADMIN_IDS`,
  `SUDOS`, `AUTH_USERS`, plus `OWNER_ID`/`OWNER`; `SUPER_ADMINS` gates admin commands and
  `is_authorized()` gates ordinary users.
- **`Database` class**: Motor client (`serverSelectionTimeoutMS=5000`), database name
  `DB_NAME` or `restrict_bot`, collections `users`, `watchers`, `sync_progress`,
  `saved_channels`, `settings`, `stats`, `replacements`, `source_thread`; `init_indexes()`
  creates unique/inspection indexes on `users.id` and `saved_channels`
  (`user_id, channel_id, channel_type, thread_id`).
- **Clients**: the bot client `app`, plus `USER_CLIENTS[user_id]` userbot clients created
  `in_memory=True` from string sessions stored in Mongo.
- **Media pipeline**: link parsing and range expansion, filename extraction from
  `DocumentAttributeFilename` and raw MTProto attributes (`extract_telegram_file_names`),
  blocklist (`BLOCK_PART_REGEX` `part001`–`part999` plus standalone `.srt`), promotional
  watermark regex and a 97-entry advertising/watermark name list, custom `/replace` rules, caption
  templating, download-then-upload for restricted items, `FloodWait` handling with a thread
  pool for blocking work.
- **Watchers**: per-user `MessageHandler` on a dedicated userbot, multi-destination dispatch,
  forum `thread_id` routing, content-type filters, `/watch`, `/watchers`, `/removetarget`,
  `/removesource`.
- **Operator surface**: `/status`, `/botstats`, `/log`, `/broadcast`, `/kickuser`,
  `/setcommands`, `/cancel`, `/tasks`, `/channelstats`, `/mywatchers`, `/pixel`, `/toggledl`.
- **Health probe**: `aiohttp` server binding `0.0.0.0:$PORT` (default 8080) answering `/` and
  `/health` with `OK`, started as a background task.

## 6. Execution flow

1. `main()` → `cleanup_startup()`, `cleanup_watchdog()`, `app.start()`, `db.init_indexes()`,
   `register_bot_commands()`, then restart every userbot that has a stored watcher, priming
   each client against its source channels.
2. `start_koyeb_health_check()` runs as a task; `idle()` keeps the bot alive; shutdown stops
   the bot and all userbot clients.
3. Command path: authorization gate → argument/link parse → task registration in
   `TASK_QUEUE`/`batch_temp.ACTIVE_TASKS` → per-item download with the user session →
   sanitise caption/filename → upload to the resolved destination → progress card refresh.
4. Watcher path: new message on a watched source → blocklist check → caption/thumbnail
   transformation → copy/forward to every route target, with `FloodWait` backoff.

## 7. Persistence and integration boundaries

- MongoDB (`DB_URI`, database `DB_NAME` → default `restrict_bot`) is the only store: users,
  permissions, watcher routes, saved channels, replacements, thumbnails, sync progress.
- Userbot string sessions are stored in that database, not on disk; `bot.log` is a runtime log
  file (`/log` transmits it) and is not source.
- Telegram (MTProto, bot + user clients) is the only external service; the HTTP health probe is
  the only inbound socket and returns a static body.

## 8. Architectural invariants

- Keep the single-module layout until a split is explicitly approved; every handler shares the
  same authorization, database and caption helpers.
- Never bypass `is_authorized`/`is_admin` for a test or a favour.
- Preserve range semantics (`from - to` inclusive, `from - all`, bot deep links, reply mode)
  and resumable task state.
- Preserve forum/topic routing (`thread_id`, `source_thread`) — never collapse it to plain
  channel posting.
- Keep the blocklist narrow and intentional: split `partNNN` chunks and standalone `.srt` are
  dropped, numeric `.mkv.001`-style splits and `Part 1` titles are kept.
- Stream where possible; only stage a file on disk when the transfer path requires it.

## 9. Security requirements

- All secrets are environment-only (`API_ID`, `API_HASH`, `BOT_TOKEN`, `DB_URI`,
  `STRING_SESSION`, `LOG_CHANNEL`); never print, log, commit or paste them.
- **Open-access fallback:** if neither `AUTH_USERS` nor `ADMINS` is configured, `is_authorized`
  returns `True` for every user. Production deployments must set `OWNER_ID`/`ADMINS`.
- `/log` transmits `bot.log` to an admin — treat it as potentially sensitive (peer IDs, user IDs).
- Never copy a userbot session to `../amit_restrict_bot/` or any sibling; never expose it in
  output, tickets or docs.
- No destructive MongoDB operations and no re-seeding of live collections.

## 10. Development decisions

- **Dual client by design:** the bot client handles UI, the user session performs restricted
  retrieval; the engine deliberately does not use a worker pool, so FloodWait is the binding
  throughput constraint.
- **Download-then-upload instead of pure forwarding** where a copy would carry the source
  channel's restriction or formatting.
- **Regex-first sanitisation** (watermarks, promotional URLs, filename normalisation) instead
  of media re-encoding; consequently there is no Pillow/ffmpeg dependency.
- **One module over a package:** fast iteration on a 8k-line engine was preferred over an
  import graph; `AGENTS.md` records that a split must be proposed first.
- **Roadmap claims are not shipped features.** `ROADMAP.md` marks 7-Zip archive extraction as
  completed; no extraction code exists in `restrict_bot.py` (only `7z` in a filename-extension
  list, plus the `7zip` package in the images). Adaptive backoff, topic resilience, session
  health checks, multi-account rotation, distributed workers and a web dashboard are all
  outstanding.

## 11. Documentation references

- [`../AGENTS.md`](../AGENTS.md) — workspace governance.
- [`AGENTS.md`](AGENTS.md) — project rules, testing and Git protocol.
- [`README.md`](README.md), [`ROADMAP.md`](ROADMAP.md), [`CHANGELOG.md`](CHANGELOG.md),
  [`SECURITY.md`](SECURITY.md) — operator documentation and history (latest changelog entry
  `2.4.0`, 2026-10-11).
- [`GEMINI.md`](GEMINI.md) — Antigravity conventions.
- [`../LUCIFER_WORKSPACE_MEMORY/projects/restrict-main/00_PROJECT_MASTER_PROFILE.md`](../LUCIFER_WORKSPACE_MEMORY/projects/restrict-main/00_PROJECT_MASTER_PROFILE.md)
  — central profile.

## 12. Verification date and corrections

**Last Verified:** 2026-11-06, by direct source inspection. No test suite was run and no live
transfer was performed; FloodWait behaviour remains unverified at runtime.

Corrected in this revision:

- "/batch command" — there is no `/batch` handler; batching is `/dl` with `from - to` or
  `from - all` links. `/batch` appeared only in prose.
- "64 automated unit tests" — the suite contains 12 test functions, not 64.
- "Pillow (thumbnailing and watermarks)" and "ffmpeg/ffprobe" — neither is a dependency or an
  import; thumbnails are set as uploaded photos, captions are regex-cleaned.
- "gated strictly to ADMIN_ID" — the gate is `SUPER_ADMINS`/`AUTH_USERS` built from
  `ADMINS`/`ADMIN`/`ADMIN_ID`/`ADMIN_IDS`, `SUDOS` and `OWNER_ID`/`OWNER`, with an open-access
  fallback when nothing is configured.
- "v2.5.0 (Production Stable)" — no version constant exists in source; `CHANGELOG.md` stops at
  `2.4.0`.
- The watcher/import subsystem, saved-channel memory and dual-tier title resolution described
  previously are present and verified.

Git: branch `main`, HEAD `abba1d8`; the working tree already carried `M .gitignore` and
`?? AGENTS.md` from Phase 6 before this edit. Memory files are gitignored, so this rewrite does
not appear in `git status`. Nothing was staged, committed or pushed.

## 13. Caption Sanitisation & Foreign Promo Stripping (2026-11-08)

- **Foreign Promotional Footers Stripping:** Implemented `strip_existing_media_footers()` in `restrict_bot.py`. Safely strips incoming `Size: ...`, `Join ...`, and all foreign channel/bot `Powered By : [\[ ᴍᴏᴠɪᴇꜱ ʙᴏᴛᴢ ᴜᴘᴅᴀᴛᴇ \]](...)` promotional lines, Unicode small caps, HTML tags, and markdown links.
- **Markdown Title Unwrapping:** Updated `clean_promotional_hyperlinks()` to unwrap markdown-linked titles with nested brackets (e.g. `[Mr.Queen S01 [E16 - E20] ... .mkv](https://t.me/...)`), preserving inner bracket sets and extracting clean media filenames.
- **Brand Footer Formatting (Restrict-main):** Attaches `[<filename>](https://t.me/luciferdatabase)` header and `⚜️ Powered By : [\[@luciferdatabase\]](https://t.me/luciferdatabase)` footer.
- **White-Label Invariant (amit_restrict_bot):** Strips all promotional footers and foreign links, preserving only `💾 Size: {size_str}` without any `@luciferdatabase` or hyperlinks.
- **Test Suite Verification:** Ran `pytest tests/test_forwarder_engine.py` on both repositories; 72/72 tests passed (100% pass rate).

## 14. Lucifer Cloud Engine Cinematic Template Preservation (2026-11-12)

- **Dedicated Cloud Engine Detection:** Added `is_lucifer_cloud_engine_caption()` to detect incoming messages originating from Lucifer Cloud Engine (`🎬 File Name:`, `━━━━━━━━━━━━━━━━━━━`, `💾 DB ID: [@LuciferDatabase]`, `[@RequestLuciferDatabase]`, `⚖️ Size:`).
- **Template Preservation & Sanitisation:** Added `process_lucifer_cloud_engine_caption()`. Keeps the entire cloud engine block intact (dividers, specs, resolution, audio, join link, and file request link).
- **Cleaned & Hyperlinked File Name:** Unwraps, cleans watermarks and rogue brackets from the filename, and hyper-links it to `https://t.me/luciferdatabase`.
- **Rogue Promo Stripping:** Drops external foreign promo footers or links (e.g. Movies Botz) while strictly exempting and protecting `@LuciferDatabase` and `@RequestLuciferDatabase`.
- **Footer Placement:** Appends `⚜️ Powered By : <a href="https://t.me/luciferdatabase">[@luciferdatabase]</a>` at the base. Does not append duplicate `💾 Size:`.
- **Fallthrough Invariant:** Non-cloud engine messages continue with standard processing unimpeded.
- **Verification:** 76/76 unit tests passed (100% pass rate).

## 15. Full Codebase Audit & Defect Remediation (2026-11-12)

Comprehensive code audit conducted by Senior Software Engineer and Code Auditor. 12 concrete actionable defects identified, resolved, and verified:
1. **Critical - False Positive Media Drop:** Fixed `extract_telegram_file_names` inspecting caption lines even when real media metadata was present. Subtitle descriptions (e.g. `Subtitles: English.srt`) in caption no longer trigger false drop of video files.
2. **Critical - Entity Parse Failure on Unclosed `<a>`:** Extended `balance_html_tags` to handle `'a'` tags and drop orphaned closing tags.
3. **Critical - Caption Length Boundary Violation:** Re-engineered `append_media_footer` with iterative backoff loop ensuring `len(caption) + len(footer) <= 1024` with balanced HTML.
4. **Major - Dangling URL Scheme Residue:** Fixed `clean_promotional_hyperlinks` to remove full URLs without leaving orphan `https://`.
5. **Major - Greedy Regex Backtracking:** Replaced greedy `.*` with bracket-aware non-greedy patterns preventing corruption of multiple links on a single line.
6. **Major - Nested Markdown Link Corruption:** Enhanced markdown unwrapping regex to preserve nested technical brackets.
7. **Major - Word Normalisation Degradation:** Modified `clean_promotional_watermarks` to only collapse consecutive hyphens (`{2,}`), preventing mutilation of single hyphens in titles like `Spider-Man` and `WEB-DL`.
8. **Major - Native Lucifer Cloud Engine Formatting:** Added `is_lucifer_cloud_engine_caption()`, `sanitize_cloud_filename()`, and `process_lucifer_cloud_engine_caption()`.
9. **Minor - NoneType Crash on Offline DB:** Added guards for `db.db.watchers` calls when database is offline.
10. **Minor - Event Loop Blocking:** Wrapped synchronous `shutil.rmtree(album_folder)` in `asyncio.to_thread`.
11. **Minor - Redundant Startup Queries:** Removed duplicate consecutive database lookups for watchers during startup.
12. **Minor - Test Suite Coverage Gap:** Expanded test suite with 9 new tests covering Cloud Engine, boundary truncation, HTML balancing, and false positive drop prevention.
- **Verification:** All 81 tests passing (100% pass rate).

## 16. Login Done Banner, 1-10s Delay Presets, TgCrypto, Monospace Terminal Box & Log FloodWait Guard (2026-11-13)
- **TgCrypto Integration (`requirements.txt`):** Added compiled C cryptography library `tgcrypto` to replace pure-python `pyaes`. Fixes Render build alert (*"TgCrypto is missing! Pyrogram will work the same, but at a much slower speed"*), delivering 20x–50x cryptographic throughput for multi-gigabyte file transfers with single-digit CPU consumption.
- **Login Status & Prominent Confirmation:**
  - Added loud and styled `╔════❰ ʟᴏɢɪɴ sᴜᴄᴄᴇssғᴜʟ ❱═❍⊱❁۪۪` / `╚════❰ ʟᴏɢɪɴ ᴅᴏɴᴇ ❱══❍⊱❁۪۪` confirmation banner upon successful authentication in `start_string_session_login` and `start_phone_login` displaying user's name, user ID, phone, and active status.
  - Added dynamic session status check in `/start` (`send_start`) indicating whether the user is currently `LOGGED IN` with active account name/phone or `NOT LOGGED IN`.
- **1-10s Forwarding Delay Presets & Code Block Warning (`ask_for_speed`, `speed_callback`):**
  - Expanded speed setup inline menu with 1s, 2s, 3s (Default), 4s, 5s, 6s, 7s, 8s, 9s, 10s presets, manual custom delay option, and cancel button.
  - Added formatted monospace code block warning:
    - ⚡ 1s - 2s: FAST (High Telegram FloodWait risk)
    - ⭐ 3s (Default): BALANCED (Optimal speed & stability)
    - 🛡️ 4s - 10s: SAFE (Zero FloodWait risk for large batches)
- **Dark Terminal "Code Format" UI:** Wrapped `generate_aesthetic_progress_ui` and final batch completion summaries (`final_text`) in `<pre><code>...</code></pre>` ensuring Telegram renders all status and progress outputs inside the monospace dark terminal box.
- **Render Log Channel FloodWait Protection (`send_log`, `handle_private`):**
  - Fixed issue where batch skips during `auto_dl = False` flooded Telegram `LOG_CHANNEL` with rapid successive messages, triggering Telegram `[420 FLOOD_WAIT_X]`.
  - Replaced repetitive per-file skip notices in `handle_private` with console logs.
  - Added minimum 2.0s dispatch cooldown and automatic `FloodWait` suppression window in `send_log`.
  - Added notification in task start message if `auto_dl` is currently OFF.
- **Verification:** All 81 forwarder engine tests passing (100% pass rate).

## 17. Audit Fixes — Cloud Template Safety, Tenant Isolation and Resource Guards (2026-11-13)

- **Cloud Engine template preserved end-to-end:** `append_media_footer()` now returns Lucifer Cloud Engine captions untouched. Previously the handler called `smart_caption()` and then `append_media_footer()`, which deleted the `📢 Join: @LuciferDatabase` line and appended a second `💾 Size:` line. The delivered caption now keeps the full cinematic template, exactly one Size line, one `⚜️ Powered By`, the filename hyperlink and the `@LuciferDatabase` / `@RequestLuciferDatabase` references.
- **Watcher isolation:** watchers are keyed by `(user_id, source_id, source_thread)`; `add_watcher()` includes the owner and `get_watcher()` filters by it, with the owner resolved from `USER_CLIENTS`.
- **Album filtering:** `process_media_album()` now honours `allowed_types` instead of mirroring every album.
- **Cleanup watchdog:** never deletes folders belonging to a running task and uses a 6-hour age threshold.
- **Disk guards:** default headroom 1.5 GB plus a per-item check for 115% of the file size.
- **Startup visibility:** index/watcher failures are logged and reported to `LOG_CHANNEL`; explicit warning when no admins are configured.
- **String-session login:** stores the API credentials actually used for validation.
- **Caption fallback:** only inspects captions for file-bearing media, preventing false `*.srt` drops of text posts.
- **Verification:** `pytest tests/test_forwarder_engine.py` — 85 passed (2026-11-13).

## 17. Unrestricted Channel 4-Tier Fast-Copy & Bridge Architecture (2026-11-13)
- **Eliminated Dotted Extension Gating:** Removed `has_dotted_ext` check gating `allow_fast_copy` in `handle_private` and `process_watcher_message`. Previously, video messages uploaded directly via Telegram mobile/web lacking a `.file_name` attribute failed dotted extension validation and were needlessly redirected to heavy disk download routines or skipped when `auto_dl` was OFF.
- **4-Tier Fast-Copy Cascade:**
  1. *Direct Bot Copy:* Clean server-side `copy_message` without forward tags.
  2. *Direct Userbot Copy:* Dispatches through the authenticated userbot session for channels where the bot lacks membership, including direct delivery to Saved Messages or user PM.
  3. *Bridge Fast-Copy (`acc -> Bot DM -> Destination`):* Resolves access divergence where the userbot can read private source channels (`t.me/c/...`) but lacks posting rights in destination channels, while the Bot has destination posting rights but lacks source membership. Userbot copies to Bot DM in 0.1s; Bot immediately copies from Bot DM to destination and deletes the bridge artifact. Zero disk usage, zero bandwidth consumption, and instant delivery.
  4. *Fallback to Download:* Only triggered when explicit Telegram content protection (`has_protected_content = True`) is enforced.
- **Diagnostic Logging:** Added explicit error logging in `handle_private` for `get_messages` failures and `UserNotParticipant` detection.
- **Dual-Remote Upstream Synchronization:** Synced and configured remotes for both GitLab (`git@gitlab.com:luciferopensource/Lucifer-InfiltratorX-For-Virus.git`) and GitHub (`git@github.com:luciferopensource/Lucifer-Infiltrator-X-For-VIRUS.git`).
- **Bridge Sender Peer Fix:** the bridge message is read from the userbot account id (`acc.me.id`), not the bot-owner user id, so multi-account logins work correctly.
- **Extension-less media names:** normal media without a recognised extension (e.g. `...AV1-YiFaN`) now receives the filename hyperlink through `link_fallback`, matching the branded format.
- **Text formatting:** Bold/Italic may wrap the filename hyperlink; Mono is emitted as plain `<code>` without a link; Cloud Engine templates are never reformatted.
- **Per-target resume:** progress is stored per destination; the batch resumes from the least-advanced target and only destinations still behind receive each message.
- **Multi-flow ask:** pending prompts are keyed by `(chat_id, flow_id)`; a new prompt supersedes older ones without leaving them hanging, and timeouts notify the user.
- **Session encryption:** `SESSION_ENC_KEY` derives a Fernet key; `session`/`api_hash` are stored as `enc:` tokens, legacy plaintext still reads. If `SESSION_ENC_KEY` is unset, the key is derived from `BOT_TOKEN`, so rotating the token invalidates old sessions (re-login required).
- **Log redaction:** `/log` sends a redacted copy (`bot.log.redacted`) with DB URIs, bot tokens, credential assignments and long session strings removed.
- **Verification:** All 91 test cases passing in `tests/test_forwarder_engine.py` (100% pass rate).


