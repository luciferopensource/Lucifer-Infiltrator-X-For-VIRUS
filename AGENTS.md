# AGENTS.md — Lucifer Infiltrator X For VIRUS

**Scope:** instructions for `Lucifer Infiltrator X For VIRUS` only. Workspace rules live in [`../AGENTS.md`](../AGENTS.md) — read that file whenever it is not already in your context.

## 1. Identity and purpose
The specialised restricted-media retrieval engine distribution for other Telegram users: saves and forwards protected media from private channels and topics over MTProto, with strict blocklist/whitelist filtering, watermark sanitisation, native Lucifer Cloud Engine cinematic template preservation, per-user caption templates and thumbnail assignment.

## 2. Independent project boundary
A dedicated repository for other Telegram users, hosted at `https://gitlab.com/luciferopensource/Lucifer-InfiltratorX-For-Virus`. Independent of `../Restrict-main/` and `../amit_restrict_bot/`. Never commit or push changes from here to the personal or Amit repositories.

## 3. Verified technology stack
- Python 3.10+, `pyrofork` (MTProto user client), Motor/MongoDB, Docker (`Dockerfile`) and Nixpacks (`nixpacks.toml`).
- No aiogram: bot and forwarding engine are one module.

## 4. Entry points
- `restrict_bot.py` — the only executable entry point (~8,200 lines: client, handlers, forwarding engine, templating).
- `tests/test_forwarder_engine.py` — pytest suite for the forwarding engine.

## 5. Module responsibilities
- `restrict_bot.py` — startup, privilege validation, `/batch` ranges, media transfer, topic routing, caption/thumbnail logic.
- `assets/` — brand and thumbnail material.
- `tests/` — engine tests, runnable without live credentials.
- `bot.log` — runtime log, not source.

## 6. Data and integration boundaries
- MongoDB: user permissions, channel targets, custom thumbnails, sync state (see `PROJECT_MEMORY.md`).
- One MTProto user session performs all transfers; no worker pool, so FloodWait is the binding constraint.
- Telegram is the only external integration.

## 7. Architectural invariants
- Keep the single-module structure; propose a split before performing one.
- Privilege validation gates every command; never bypass it for a test or convenience.
- Batch range semantics (inclusive bounds, link parsing, resumable state) must be preserved exactly.
- Topic/forum routing must not be collapsed to plain channel posting.
- Media handling must not stage full files on disk where streaming is possible.

## 8. Mandatory documentation reading
Read in order: [`../AGENTS.md`](../AGENTS.md), `PROJECT_MEMORY.md`, `GEMINI.md`, `README.md`, `ROADMAP.md`, then `../LUCIFER_WORKSPACE_MEMORY/projects/restrict-main/00_PROJECT_MASTER_PROFILE.md`. Treat those memory files as read-only input for a code task.

## 9. Coding and modification rules
- Locate the exact region of `restrict_bot.py` before editing; never patch by line number from memory.
- Preserve user-facing formatting and command names unless the task is a UI change.
- No new dependency without justification; container build stays lean.

## 10. Testing and verification
- Run `pytest tests/test_forwarder_engine.py` for engine changes and report the actual result.
- Live transfer requires a real session and channels — label it untested when it was not exercised.
- Never describe FloodWait behaviour as verified without a live run.

## 11. Security restrictions
- Never print, log or commit the session string, Mongo URI, API hashes or `.env` contents.
- Never copy this session to `../amit_restrict_bot/` or any other project.
- No destructive MongoDB operations; no re-seeding live collections.

## 12. Git and backup rules
- Repository root is this directory (branch `main`). Check `git status` before edits; pre-existing changes are user-owned.
- Commit or push only when explicitly authorised; never force-push, rewrite history or change remotes.
- `.gitignore` ignores `AGENTS.md`; the Phase 6 root-level `!AGENTS.md` exception makes this file versionable. Do not widen it to `.env`, `bot.log`, `assets/` or other Markdown.

## 13. Agent handoff
Record in `PROJECT_MEMORY.md` before handoff: branch and commit, modified/untracked paths, work done, work remaining, tests actually executed, next action.

## 14. Memory and status upkeep
Update `PROJECT_MEMORY.md` for durable architecture and decisions; use a status/changelog document for progress. Never invent verification or transfer results.
