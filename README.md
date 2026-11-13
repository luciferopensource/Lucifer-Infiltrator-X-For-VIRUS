<div align="center">

<img src="./assets/logo.png" alt="Lucifer Morningstar Banner" width="100%" />

<br><br>

# 🜏 𝕃𝕌ℂ𝕀𝔽𝔼ℝ 𝕄𝕆ℝℕ𝕀ℕ𝔾𝕊𝕋𝔸ℝ

### ⚜️ Precision-Built Telegram Automation, Synchronisation & Media Processing Engine ⚜️

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Telegram API](https://img.shields.io/badge/Telegram-MTProto-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://core.telegram.org/)
[![Pyrofork](https://img.shields.io/badge/Framework-Pyrofork_v2.3.45-8A2BE2?style=for-the-badge&logo=telegram&logoColor=white)](https://pypi.org/project/pyrofork/)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB_Motor-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Docker](https://img.shields.io/badge/Container-Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Linux](https://img.shields.io/badge/OS-Linux_Ubuntu_Debian-FCC624?style=for-the-badge&logo=linux&logoColor=black)](https://www.kernel.org/)
[![Render](https://img.shields.io/badge/Cloud-Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)](https://render.com/)
[![Koyeb](https://img.shields.io/badge/Cloud-Koyeb-121212?style=for-the-badge&logo=koyeb&logoColor=white)](https://www.koyeb.com/)
[![Sevalla](https://img.shields.io/badge/Cloud-Sevalla-5B21B6?style=for-the-badge&logo=cloud&logoColor=white)](https://sevalla.com/)
[![Hugging Face](https://img.shields.io/badge/Cloud-Hugging_Face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/spaces)
[![Uptime Monitor](https://img.shields.io/badge/Health_Check-HTTP_8080-00E676?style=for-the-badge&logo=statuspage&logoColor=white)](https://uptimerobot.com/)
[![License](https://img.shields.io/badge/Licence-MIT-blueviolet?style=for-the-badge)](https://opensource.org/licenses/MIT)

<br>

> *“In a digital landscape constrained by proprietary restrictions, volatile network links, and promotional clutter, this engine serves as the definitive bridge connecting restricted archives directly to sovereign destinations with clean, catalogued perfection.”*

<br>

◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
### 🏛️ OFFICIAL CITADEL & SUPPORT

> 📢 **Official Channel:** [@LuciferOpenSource](https://t.me/LuciferOpenSource)  
> 💬 **Support Group:** [@LuciferOpenSourceDiscussionGroup](https://t.me/LuciferOpenSourceDiscussionGroup)  
> 🍿 **Movie Request Group:** [@RequestLuciferDatabase](https://t.me/RequestLuciferDatabase)  
> 🌟 **GitHub Repository:** [Auto-Filter-Bot-Lucifer](https://github.com/ailuciferbaba-pixel/Auto-Filter-Bot-Lucifer/)  
> 👨‍💻 **GitHub Profile:** [ailuciferbaba-pixel](https://github.com/ailuciferbaba-pixel)  
> 👑 **Lead Developer:** **Lucifer Morningstar**  
◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈

</div>

<br>

---

## 📜 TABLE OF CONTENTS

```text
01. 👑 Executive Project Overview
02. ⚔️ Core Capabilities & Production Highlights
03. 🧠 How the System Works (Full End-to-End Pipeline)
04. 🏛️ Architecture & Concurrency Model
05. 🧩 Implemented Feature Matrix
06. ⚙️ Prerequisites & System Requirements
07. 🗝️ Telegram API Credential Acquisition
08. 🤖 BotFather Telegram Bot Creation
09. 🍃 MongoDB Atlas Configuration & Setup
10. 🔐 Master Environment Variables Reference
11. 📜 Complete Command Codex (Detailed Reference)
12. 🛰️ Live Watcher Surveillance & Auto-Routing Engine
13. 🧹 Media Cleaning & Stremio Processing Pipeline
14. 📊 Progress UI, Task Queue & Cancellation Subsystem
15. 🍃 MongoDB Database Architecture & Collections
16. 💻 Local Deployment (Windows, macOS, Linux)
17. 🐧 Production VPS Deployment (Ubuntu/Debian + Systemd)
18. 🐳 Containerised Docker Deployment
19. ☁️ Render Cloud Platform Deployment
20. ☁️ Koyeb Cloud Platform Deployment
21. ☁️ Sevalla Cloud Platform Deployment
22. 🤗 Hugging Face Spaces Deployment
23. 🧬 Multi-Instance Distributed Scaling Architecture
24. 📁 Official Project Structure
25. 🛠️ Comprehensive Troubleshooting Manual
26. ❓ Frequently Asked Questions (FAQ)
27. 🔒 Security Best Practices & Credential Hygiene
28. 🔄 Maintenance, Backups & Update Procedures
29. 📜 Licence Information
30. 👑 The Lucifer Morningstar Citadel
```

---

<br>

## 👑 01. EXECUTIVE PROJECT OVERVIEW

**Lucifer Morningstar** represents an advanced, high-throughput Telegram synchronisation, restricted-content extraction, and media sanitisation engine engineered with Python 3.10+, Pyrogram/Pyrofork v2, and MongoDB Motor.

In standard operational environments, transferring media libraries between Telegram channels presents severe operational hurdles:
1. **Restricted Channel Protections:** Channels with disabled forwarding, restricted saving permissions, or private invite architectures block direct transmission.
2. **Promotional Clutter:** Media files and captions frequently arrive inundated with spam anchors, website links, watermarks, tracking URLs, and bloated advertising prefixes.
3. **Transient Server Failures & Rate Limits:** Extended multi-thousand-file batch jobs on standard bots face socket timeouts, memory exhaustion, or Telegram `FloodWait` penalties, losing state and forcing administrators to start over.

This project delivers a resilient, autonomous solution. Utilizing a dual-client MTProto framework (coupling an administrative Telegram Bot token with high-performance Userbot MTProto sessions), the system executes rapid server-side cloning when permitted, falling back intelligently to streamed chunked downloads, local 7zip splitting for 2GB+ files, and high-speed multi-part uploads.

Crucially, every media file and caption undergoes an automated sanitisation pass tailored for **Stremio, Kodi, and Plex** media catalogues. All promotional hyperlinks and 100+ known piracy/promotional domain identifiers are excised while preserving critical audio tags, codecs, season/episode metadata, and true file extensions. With stateful MongoDB logging and built-in HTTP health probes, the system guarantees idempotent recovery across arbitrary restarts.

---

<br>

## ⚔️ 02. CORE CAPABILITIES & PRODUCTION HIGHLIGHTS

* 🔓 **Dual-Mode Restricted Content Bypass:** Infiltrates protected and private channels through authenticated Userbot sessions, extracting restricted video and document streams without front-end interface constraints.
* ⚡ **Zero-Bandwidth Fast-Forwarding:** Automatically inspects target destinations. When direct forwarding is permissible, media is synchronised server-side within milliseconds without touching host disk storage or consuming VPS bandwidth.
* 🛡️ **Graceful Download/Upload Fallback:** If server-side copying is blocked by channel permissions or restricted flags, the system seamlessly transitions into a chunked background download/upload pipeline with live progress telemetry.
* 🧹 **Stremio-Optimised Media Sanitiser:** Strips hidden HTML promotional hyperlinks and cleans over 100 promotional domain names (e.g., *VegaMovies, 4kHdHub, Bollyflix, 1XBET*) while rigorously protecting bracketed technical metadata (`[Hindi]`, `[Dual Audio]`, `[HEVC]`, `[S01E01]`, `[4K]`).
* 📦 **True Extension & Split-Suffix Parser:** Accurately distinguishes between actual media extensions (`.mkv`, `.mp4`) and Telegram split suffixes (`.001` to `.999`). Injects missing quality markers (e.g. `720p`) before the true extension (`Movie 720p.mkv.001`), completely eliminating corrupted split-file naming.
* 💾 **Standardised Media Footers:** Automatically computes true file size in human-readable decimal format (`💾 Size: 1015.20 MB`) and appends sovereign channel signatures (`⚜️ Powered By : [@luciferdatabase]`) with idempotent deduplication across retries.
* ✂️ **Automatic 2GB+ File Splitting:** Detects files exceeding Telegram's 2000MB bot threshold and transparently splits them into 1900MB parts using native `split` or `7z/7za` before uploading.
* 🛰️ **Autonomous Multi-Target Watchers:** Monitors source channels and forum topics 24/7. When new posts arrive, they are filtered by media type (Video, Document, Photo, Audio, etc.), sanitised, and dispatched to multiple destinations simultaneously with configurable inter-message delay.
* 🧠 **Persistent Resumption Brain:** Synchronisation progress is tracked post-by-post in MongoDB (`sync_progress` collection). Abrupt host restarts resume cleanly from the exact last successful message ID.
* 🛑 **Live Interactive Task Controller:** Provides real-time aesthetic progress cards, speed calculations, ETA estimations, and instant task cancellation via `/cancel` or refresh via `/tasks`.
* 🌐 **Built-in HTTP Health Monitor:** Operates an integrated `aiohttp` web server on port `PORT` (default: 8080) serving `/` and `/health`, keeping cloud deployments alive on Render, Koyeb, Sevalla, and Hugging Face.

---

<br>

## 🧠 03. HOW THE SYSTEM WORKS (END-TO-END PIPELINE)

The synchronisation pipeline operates across distinct, fault-tolerant phases:

```text
                      📥 SOURCE TELEGRAM CHANNEL / FORUM TOPIC
                                         │
                                         ▼
                             🔍 MESSAGE & LINK PARSING
               (Single Post / Batch 'From - To' / 'From - all' / /watch)
                                         │
                                         ▼
                           🧠 SOURCE ACCESS & RESTRICTION
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
            🔓 Direct Copy Viable                     🔒 Restricted / Protected
                    │                                         │
                    ▼                                         ▼
           Telegram Server-Side                      📥 Streamed MTProto
             Message Forward                           Download to Disk
                    │                                         │
                    │                                         ▼
                    │                              ✂️ 2GB+ Split Check
                    │                              (Native split / 7zip)
                    │                                         │
                    └────────────────────┬────────────────────┘
                                         │
                                         ▼
                            🧹 SANITISATION & MEDIA CLEANING
                     ├─ Strip promotional HTML hyperlinks (<a href>)
                     ├─ Clean 100+ domain identifiers (case/bracket agnostic)
                     ├─ Convert underscores to spaces
                     ├─ Preserve [Hindi], [Dual Audio], [HEVC], [S01E01]
                     ├─ Detect real media extension vs split suffix (.001)
                     └─ Insert missing quality before true extension
                                         │
                                         ▼
                             📝 CAPTION & FOOTER ASSEMBLY
                     ├─ Format cleaned caption within 1024-char limit
                     ├─ Compute accurate file size: 💾 Size: 1015.20 MB
                     └─ Append sovereign join line: ⚜️ Powered By : [@luciferdatabase]
                                         │
                                         ▼
                             📊 PROGRESS & DISPATCH ENGINE
                     ├─ Real-time download/upload UI updates
                     ├─ Configurable safety delay (e.g. 3s)
                     └─ Multi-target routing (Channels / Groups / DMs / Topics)
                                         │
                                         ▼
                              🍃 MONGODB STATE PERSISTENCE
                     (Update sync_progress with last_msg_id for auto-resume)
```

### Deep Stage Breakdown
1. **Link Intake:** The engine receives links formatted as public usernames (`t.me/channel/100`), private hashes (`t.me/c/1234567890/100`), numeric ranges (`t.me/c/xxxx/101 - 200`), total channel sweeps (`t.me/c/xxxx/1 - all`), or bot dialogues (`t.me/b/botusername/4321`).
2. **Channel Resolution:** The bot resolves the source peer. If private, it accesses the message stream via the logged-in Userbot session (`USER_CLIENTS`).
3. **Direct vs. Fallback Strategy:** If `auto_download` is enabled (controllable via `/toggledl`), the bot first attempts direct server-side copying. If Telegram raises `ChatForwardsRestricted` or access limits, the bot switches to MTProto file streaming.
4. **Sanitisation Execution:** Media filenames and caption HTML strings pass through `clean_promotional_hyperlinks()` and `clean_promotional_names()`. The parser decouples `.001` split indicators from `.mkv` extensions, inserts missing quality standards, attaches the exact byte size, and stamps the sovereign footer.
5. **Dispatch & Rate-Limit Management:** Outgoing media is dispatched via the Bot or Userbot client. If Telegram responds with a `FloodWait(x)` exception, the task worker pauses execution for the exact duration requested, preventing peer deactivation, and automatically resumes upon timer expiry.
6. **State Recording:** After confirmation, the destination message is stored, the active task progress bar advances, and the latest message ID is committed to MongoDB.

---

<br>

## 🏛️ 04. ARCHITECTURE & CONCURRENCY MODEL

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                       LUCIFER MORNINGSTAR PROCESS                       │
├───────────────────────────────────┬─────────────────────────────────────┤
│      TELEGRAM CLIENT LAYER        │         ASYNC CORE & STORAGE        │
│  ┌─────────────────────────────┐  │  ┌───────────────────────────────┐  │
│  │     Pyrogram Bot Client     │  │  │    asyncio Event Loop Core    │  │
│  │   (50 Workers, MTProto)     │  │  │  (uvloop accelerated engine)  │  │
│  └──────────────┬──────────────┘  │  └───────────────┬───────────────┘  │
│                 │                 │                  │                  │
│  ┌──────────────┴──────────────┐  │  ┌───────────────┴───────────────┐  │
│  │   Multi-User Userbot Pool   │  │  │      ThreadPoolExecutor       │  │
│  │ (Dynamic session activation)│  │  │ (4 Workers for blocking I/O)  │  │
│  └──────────────┬──────────────┘  │  └───────────────┬───────────────┘  │
│                 │                 │                  │                  │
│  ┌──────────────┴──────────────┐  │  ┌───────────────┴───────────────┐  │
│  │     Live Watcher Engine     │  │  │     MongoDB Motor Driver      │  │
│  │ (Per-user listener filters) │  │  │  (Async non-blocking queries) │  │
│  └─────────────────────────────┘  │  └───────────────────────────────┘  │
├───────────────────────────────────┴─────────────────────────────────────┤
│                           AUXILIARY SERVICES                            │
│  ┌─────────────────────────────┐     ┌───────────────────────────────┐  │
│  │   aiohttp Health Server     │     │     7zip / Native Splitter    │  │
│  │   (Port 8080: / and /health)│     │   (2GB+ chunk size handler)   │  │
│  └─────────────────────────────┘     └───────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

* **Non-Blocking I/O Architecture:** Leverages `uvloop` (on UNIX environments) and Python's native `asyncio` loop, ensuring thousands of event messages are handled without locking execution threads.
* **Thread Pool Delegation:** Disk writes, 7zip extraction, native file splitting, and heavy regex scanning are offloaded to an internal `ThreadPoolExecutor(max_workers=4)`.
* **Stateful Userbot Pool:** User sessions generated through `/login` are maintained in-memory in `USER_CLIENTS`. Multiple users can process tasks simultaneously with distinct Telegram authorization contexts.
* **Task Queuing System:** Concurrent tasks per user are governed by `TASK_QUEUE` and restricted to `MAX_TASKS_PER_USER` (default: 3), preventing accidental API flood triggers.

---

<br>

## 🧩 05. IMPLEMENTED FEATURE MATRIX

| Capability | Status | Source Verification | Operational Details |
| :--- | :---: | :--- | :--- |
| **Single Post Forwarding** | ✅ | `restrict_bot.py:1754` | Direct link resolution for public and private posts. |
| **Batch Range Extraction** | ✅ | `restrict_bot.py:2315` | Accepts `From - To` numerical ranges (e.g. `101 - 200`). |
| **Complete Channel Scraping** | ✅ | `restrict_bot.py:2375` | Accepts `1 - all` syntax to harvest an entire channel archive. |
| **Restricted Content Unlock** | ✅ | `restrict_bot.py:2669` | Streams protected media via Pyrogram Userbot sessions. |
| **Server-Side Direct Copy** | ✅ | `restrict_bot.py:2708` | Instant forwarding without local downloading when permitted. |
| **Automatic Download Fallback**| ✅ | `restrict_bot.py:2795` | Download/Upload fallback when direct copying is prohibited. |
| **Promotional Link Stripping** | ✅ | `restrict_bot.py:530` | Removes hidden `<a href>` promotional hyperlinks safely. |
| **100+ Promo Domain Cleaning** | ✅ | `restrict_bot.py:557` | Sanitises domain/channel names with bracket & case awareness. |
| **Metadata Protection** | ✅ | `restrict_bot.py:640` | Preserves `[Hindi]`, `[Dual Audio]`, `[HEVC]`, `[S01E01]`, `[4K]`. |
| **Split-Suffix Preservation** | ✅ | `restrict_bot.py:512` | Separates true extension (`.mkv`) from split suffix (`.001`). |
| **Pre-Extension Quality Fix** | ✅ | `restrict_bot.py:648` | Inserts quality (`720p`) before real extension, never after. |
| **Accurate File Size Footer** | ✅ | `restrict_bot.py:586` | Computes decimal byte size: `💾 Size: 1015.20 MB`. |
| **Sovereign Channel Footer** | ✅ | `restrict_bot.py:596` | Appends `⚜️ Powered By : [@luciferdatabase]` with zero duplicates. |
| **2GB+ Telegram Splitting** | ✅ | `restrict_bot.py:795` | Splits oversized files into 1900MB chunks via `split`/`7z`. |
| **Live Multi-Target Watchers** | ✅ | `restrict_bot.py:210` | 24/7 monitoring of source channels with multi-destination dispatch. |
| **Content Type Filtering** | ✅ | `restrict_bot.py:1959` | Selectable filters: Video, Document, Photo, Audio, Voice, etc. |
| **Forum Topic / Thread Support**| ✅ | `restrict_bot.py:218` | Supports topic threads in both source and destination chats. |
| **Interactive Phone Login** | ✅ | `restrict_bot.py:1375` | `/login` wizard with phone number, spaced OTP, and 2FA password. |
| **Session Revocation** | ✅ | `restrict_bot.py:1314` | `/logout` calls Telegram `log_out()` and purges database session. |
| **Interactive Task Cancel** | ✅ | `restrict_bot.py:1067` | `/cancel` UI with individual task or bulk cancellation buttons. |
| **Live Task Refresh** | ✅ | `restrict_bot.py:1055` | `/tasks` or `/progress` re-renders active progress cards. |
| **Pixeldrain CDN Bypass** | ✅ | `restrict_bot.py:1181` | `/pixel` transforms Pixeldrain links into direct high-speed CDN URLs. |
| **System Health Dashboard** | ✅ | `restrict_bot.py:1218` | `/status` displays real-time CPU, RAM, Disk, Uptime, and Queue. |
| **Administrative Broadcast** | ✅ | `restrict_bot.py:1516` | `/broadcast` sends messages to all registered users with metrics. |
| **MongoDB State Resume** | ✅ | `restrict_bot.py:198` | Persists `last_msg_id` in `sync_progress` collection. |
| **Cloud HTTP Health Server** | ✅ | `restrict_bot.py:2961` | Built-in `aiohttp` web server on port `PORT` (default: 8080). |

---

<br>

## ⚙️ 06. PREREQUISITES & SYSTEM REQUIREMENTS

### Hardware Specifications
* **CPU:** Minimum 1 vCPU (2+ vCPUs recommended for multi-part 7zip splitting).
* **RAM:** Minimum 512 MB (1 GB to 2 GB recommended when handling 2GB+ downloads).
* **Disk Storage:** At least 5 GB of free SSD storage (high-volume multi-GB transfers require scratch disk capacity equal to `2 × largest file size`).

### Software Specifications
* **Python:** Version `3.10.x` or `3.11.x` (Python 3.10 recommended).
* **Operating System:** Linux (Ubuntu 20.04+, Debian 11+, Arch), Windows 10/11, macOS.
* **System Utilities:** `coreutils` (for native `split`) and `7zip` (or `p7zip-full`).
* **Compilers:** `build-essential` and `python3-dev` (required to compile C-accelerators `tgcrypto` and `uvloop`).

---

<br>

## 🗝️ 07. TELEGRAM API CREDENTIAL ACQUISITION

To allow the MTProto engine to interact with Telegram's binary data clusters, you must obtain an `API_ID` and `API_HASH`:

1. Direct your browser to the official Telegram application portal: [👉 my.telegram.org](https://my.telegram.org/).
2. Enter your telephone number in international format (e.g., `+447911123456`) and enter the confirmation code sent to your Telegram account.
3. Select **API development tools**.
4. Complete the **App title** and **Short name** fields (e.g., `LuciferEngine`).
5. Choose **Desktop** or **Other** under Platform.
6. Submit the form.
7. Safely record:
   * **`api_id`**: A numerical identifier (e.g., `12345678`).
   * **`api_hash`**: A 32-character hexadecimal string (e.g., `<YOUR_API_HASH>`).

> [!CAUTION]
> Treat your `API_ID` and `API_HASH` as root credentials. Never commit them to public repositories.

---

<br>

## 🤖 08. BOTFATHER TELEGRAM BOT CREATION

1. Open Telegram and initiate a conversation with [@BotFather](https://t.me/BotFather).
2. Execute the `/newbot` command.
3. Provide a friendly display name (e.g., `Lucifer Morningstar Engine`).
4. Provide a unique username ending in `bot` (e.g., `LuciferMorningstar_SyncBot`).
5. BotFather will issue your authentication token formatted as:
   ```text
   123456789:YOUR_BOT_TOKEN_HERE
   ```
6. **Configure Channel Permissions:**
   * Add your bot as an **Administrator** to all source and destination channels.
   * Required permissions: **Post Messages**, **Edit Messages**, **Delete Messages**, and **Invite Users via Link**.

---

<br>

## 🍃 09. MONGODB ATLAS CONFIGURATION & SETUP

The engine requires MongoDB to persist active tasks, user sessions, system settings, and watcher configurations.

1. Register for an account at [👉 MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register).
2. Deploy a database cluster (the free `M0 Sandbox` tier is fully supported).
3. Under **Security ➔ Database Access**, create a database user:
   * Select **Password Authentication**.
   * Assign the role **Read and write to any database**.
4. Under **Security ➔ Network Access**, configure IP whitelisting:
   * Click **Add IP Address**.
   * Select **Allow Access from Anywhere (`0.0.0.0/0`)** to ensure dynamic cloud platforms (Render, Koyeb, VPS) maintain uninterrupted connectivity.
5. Under **Database ➔ Clusters**, select **Connect ➔ Drivers**:
   * Select Driver: `Python`, Version: `3.6 or later`.
   * Copy the connection string:
     ```text
     mongodb+srv://<username>:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
     ```
   * Replace `<password>` with your database user password. This is your **`DB_URI`**.

---

<br>

## 🔐 10. MASTER ENVIRONMENT VARIABLES REFERENCE

Every configuration parameter is derived directly from the application source code:

| Variable | Required | Default | Type | Description & Purpose | Example Value |
| :--- | :---: | :---: | :---: | :--- | :--- |
| `API_ID` | **Yes** | `None` | Integer | Telegram API ID obtained from my.telegram.org. | `2847192` |
| `API_HASH` | **Yes** | `""` | String | Telegram API Hash obtained from my.telegram.org. | `<YOUR_API_HASH>` |
| `BOT_TOKEN` | **Yes** | `""` | String | Telegram Bot Token obtained from @BotFather. | `123456789:YOUR_BOT_TOKEN_HERE` |
| `DB_URI` | **Yes** | `""` | String | MongoDB connection URI with read/write privileges. | `mongodb+srv://<username>:<password>@cluster0...` |
| `DB_NAME` | **Yes** | `""` | String | MongoDB database name. Must be unique per bot instance. | `Lucifer_Cluster_01` |
| `STRING_SESSION`| No | `None` | String | Pyrogram v2 string session for default userbot operations. | `BQAF...very_long_session_string` |
| `SESSION_ENC_KEY`| No | `BOT_TOKEN` fallback | String | Passphrase used to encrypt stored MTProto session strings and API hashes. If unset, a key is derived from `BOT_TOKEN`; set it explicitly to decouple the two. Changing it makes existing sessions unreadable. | `a-very-long-random-passphrase` |
| `LOG_CHANNEL` | No | `""` | String/Int | Channel ID (or `ID/Topic_ID`) for audit logs & crash alerts. | `-1001234567890` or `-1001234567890/42` |
| `STATUS_UPDATE_INTERVAL` | No | `15` | Integer | Minimum interval (in seconds) between progress bar edits. | `15` |
| `LOGIN_SYSTEM` | No | `True` | Boolean | Enables or disables the interactive phone `/login` wizard. | `True` |
| `ERROR_MESSAGE`| No | `True` | Boolean | Whether to notify users via chat when file transfer fails. | `True` |
| `WAITING_TIME` | No | `3` | Integer | Default inter-message delay (in seconds) during batch jobs. | `3` |
| `ADMINS` | No | `[]` | Int List | Comma-separated user IDs granted full administrative control. | `123456789,987654321` |
| `SUDOS` | No | `[]` | Int List | Comma-separated user IDs granted elevated helper privileges. | `1122334455,5544332211` |
| `MAX_TASKS_PER_USER` | No | `3` | Integer | Maximum number of concurrent tasks allowed per user. | `3` |
| `PORT` | No | `8080` | Integer | Port for the built-in HTTP health check probe server. | `8080` |

---

<br>

## 📜 11. COMPLETE COMMAND CODEX (DETAILED REFERENCE)

### Master Command Summary Table

| Command | Aliases | Access Level | Syntax | Functional Description |
| :--- | :--- | :---: | :--- | :--- |
| `/start` | — | All Users | `/start` | Initializes conversation, registers user in database, displays primary menu. |
| `/help` | — | All Users | `/help` | Displays complete operator manual, syntax guidelines, and examples. |
| `/dl` | — | All Users | `/dl [Link]` *(or reply)* | Initiates single or batch file extraction and destination forwarding. |
| `/watch` | — | Private Chat | `/watch <Link>` | Interactive wizard to configure a 24/7 autonomous channel watcher. |
| `/watchers` | `/list` | Private Chat | `/watchers` | Lists all active watchers with source, filters, formats, and targets. |
| `/removetarget`| `/remove_target` | Private Chat | `/removetarget <src> <dst>` | Removes a specific destination channel from an active watcher. |
| `/removesource`| `/unwatch` | Private Chat | `/unwatch <source_id>` | Terminates an entire watcher pipeline for a given source channel. |
| `/addsourcechannel` | `/addsource` | Private Chat | `/addsourcechannel [ID/Link]` | Registers and auto-names a source channel in persistent memory. |
| `/adddestinationchannel` | `/adddest` | Private Chat | `/adddestinationchannel [ID/Link]` | Validates admin write permissions and saves a destination channel. |
| `/viewsourcechannels` | `/viewsources` | Private Chat | `/viewsourcechannels` | Interactive 10-per-page explorer for saved source channels with quick-watch. |
| `/viewdestinationchannels` | `/viewdest` | Private Chat | `/viewdestinationchannels` | Interactive 10-per-page explorer for saved destination channels with deletion. |
| `/tasks` | `/progress`| Private Chat | `/tasks` | Refreshes and re-displays active progress cards for ongoing tasks. |
| `/cancel` | — | All Users | `/cancel` | Opens interactive menu to terminate specific tasks or all user tasks. |
| `/login` | — | Private Chat | `/login` | Interactive phone login wizard generating a secure Pyrogram Userbot session. |
| `/logout` | — | Private Chat | `/logout` | Terminates active user session on Telegram and clears database storage. |
| `/status` | — | Admins & Sudos | `/status` | Displays system hardware metrics (CPU, RAM, Disk, Uptime, Queue). |
| `/botstats` | — | Admins Only | `/botstats` | Detailed analytics breakdown of registered users, sessions, and tasks. |
| `/log` | — | Admins & Sudos | `/log` | Transmits the active application log file (`bot.log`) as a Telegram document. |
| `/broadcast` | — | Admins Only | `/broadcast` *(reply)* | Broadcasts the replied message to all registered bot users with metrics. |
| `/channelstats` | `/watchstats`, `/stats`, `/analytics` | All Users | `/channelstats` | Performance & Channel Intelligence Dashboard (Daily, Weekly, Monthly, Lifetime deliveries). |
| `/channelhistory` | — | All Users | `/channelhistory` | Interactive separate channel history dossier with 1-page-per-channel navigation. |
| `/replace` | `/rebrand`, `/replacements` | All Users | `/replace <old> -> <new>` | Re-branding engine to replace watermarks, links, and text patterns. |
| `/setthumb` | `/setthumbnail` | All Users | `/setthumb` *(reply to photo)* | Sets custom thumbnail for all uploaded documents and video files. |
| `/viewthumb` | `/mythumb` | All Users | `/viewthumb` | Views currently saved custom thumbnail. |
| `/delthumb` | `/clearthumb` | All Users | `/delthumb` | Deletes saved custom thumbnail. |
| `/toggledl` | — | Admins & Sudos | `/toggledl` | Toggles global auto-download fallback mode (ON: Download/Upload, OFF: Direct Only). |
| `/pixel` | — | Admins & Sudos | `/pixel <URL>` | Bypasses Pixeldrain rate limits by generating direct high-speed CDN URLs. |

---

### Detailed Command Specifications

◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
### 🚀 `/dl` — DIRECT EXTRACTION & FORWARDING ENGINE
◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
* **Purpose:** The primary engine for transferring files from public or restricted channels directly to your destination.
* **Syntax:**
  * Direct Link: `/dl https://t.me/c/1234567890/100`
  * Reply Mode: Reply directly to a message containing a link with `/dl`
  * Plain Link: Sending the raw link directly into the private chat also triggers this engine.
* **Batch Range Syntax:**
  * Specific Range: `https://t.me/c/1234567890/101 - 200`
  * Complete Scraping: `https://t.me/c/1234567890/1 - all`
  * Bot Message Bypass: `https://t.me/b/botusername/4321`
* **Access:** Available to all registered users (governed by `MAX_TASKS_PER_USER`).
* **Workflow:**
  1. Inspects link format and verifies source channel accessibility.
  2. Queries destination selection (Direct Message or Custom Channel/Group).
  3. Prompts for inter-message delay (default: 3 seconds).
  4. Attempts direct server-side fast-copy. If restricted, streams chunked download, sanitises filename, checks 2GB split limits, uploads, appends size and footer, and updates MongoDB.

---

◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
### 🛰️ `/watch` — LIVE SURVEILLANCE & AUTO-FORWARDER
◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
* **Purpose:** Installs a permanent 24/7 background watcher on a source channel or forum topic.
* **Syntax:** `/watch` *(select from saved source channels)* or `/watch <Link>`
* **Access:** Private chat only.
* **Interactive Setup Flow:**
  1. **Source Analysis:** Verifies peer accessibility and detects forum thread IDs.
  2. **Target Destination:** Choose DM or specify custom channel ID/username.
  3. **Topic Selection:** Specify destination forum topic ID or send `None`.
  4. **Delay Setting:** Input transmission delay in seconds (recommended: 3s).
  5. **Content Filtering:** Inline multi-select keyboard to filter media types (Video, Document, Photo, Audio, Voice, Sticker, Animation, Text).
  6. **Text Formatting:** Select caption transformation mode (`Original`, `Title Only`, or `Cleaned`).

---

◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
### 📋 `/watchers` (Alias: `/list`) — ACTIVE SURVEILLANCE CODEX
◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
* **Purpose:** Inspects all active channel watchers configured by the executing user.
* **Syntax:** `/watchers` or `/list`
* **Access:** Private chat only.
* **Output Structure:**
  ```text
  📊 Your Multi-Source Channel Mappings:

  1. 📥 Cinema Vault (Topic: 12)
     -1001987654321
     🎛 Filters: Video, Document
     📝 Format: Cleaned
     ⏱ Delay: 3s
     ⤵️ Targets (2):
     • Backup Archive (-1001122334455)
     • VIP Streamers Topic: 4 (-1009988776655)
  ```

---

◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
### 🎯 `/removetarget` & `/removesource` — WATCHER TERMINATION
◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
* **Purpose:** Prunes destination targets or dismantles an entire source monitoring pipeline.
* **Syntax:**
  * Prune Single Destination: `/removetarget <source_id> <destination_id>`
  * Dismantle Entire Source: `/removesource <source_id>` or `/unwatch <source_id>`
* **Access:** Private chat only.

---

◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
### 🛑 `/cancel` — TASK ABORT CONTROLLER
◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
* **Purpose:** Safely halts ongoing transfers and clears pending queues.
* **Syntax:** `/cancel`
* **Workflow:** Displays interactive inline keyboard listing all running tasks with shortened labels. Offers individual task termination or `🛑 Cancel ALL My Tasks` with double-confirmation dialogue.

---

◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
### 📊 `/tasks` (Alias: `/progress`) — PROGRESS REFRESH
◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
* **Purpose:** Resets stale progress interface cards and triggers immediate re-rendering of live transfer statistics in chat.
* **Syntax:** `/tasks` or `/progress`
* **Access:** Private chat only.

---

◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
### 🔑 `/login` & `/logout` — USERBOT SESSION CONTROLLER
◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
* **Purpose:** Authenticates a personal Telegram account to unlock restricted channels without exposing raw session strings in environment files.
* **Login Flow:**
  1. Issue `/login`.
  2. Sends phone number in international format (`+447911123456`).
  3. **Critical OTP Formatting:** The 5-digit Telegram code **must** be sent with spaces (e.g. `1 2 3 4 5`) to circumvent automated Telegram security blocking.
  4. Submits Two-Step Verification (2FA) password if enabled on the account.
  5. Stores encrypted session string in MongoDB `users` collection and initializes `user_client`.
* **Logout Flow:**
  1. Issue `/logout`.
  2. Disconnects userbot instance and calls MTProto `log_out()` to unregister device authorization.
  3. Purges session keys from database.

---

◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
### 🔰 `/status` — SYSTEM HARDWARE DASHBOARD
◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
* **Purpose:** Provides comprehensive diagnostics regarding host server resource utilization.
* **Syntax:** `/status`
* **Access:** Strictly restricted to `ADMINS` and `SUDOS`.
* **Output Structure:**
  ```text
  🔰 SYSTEM DASHBOARD

  ⏱ Uptime: 4d 12h 30m
  🧠 RAM: 42.1%  │  ⚙️ CPU: 14.5%
  💿 Disk Free: 48.3 GB
  🔄 Auto-Download: ON ✅

  👀 Live Watchers: 8 running
  📉 Active Downloads (2)
  • Cinema Vault → Backup Archive
  • Series Hub → Direct Message
  ```

---

◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
### 📈 `/botstats` — ADMINISTRATIVE USER ANALYTICS
◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
* **Purpose:** Generates a real-time audit report detailing all registered users, active session authorizations, and current tasks.
* **Syntax:** `/botstats`
* **Access:** Strictly restricted to `ADMINS`.

---

◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
### 📜 `/log` — SYSTEM LOG RETRIEVAL
◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
* **Purpose:** Extracts the active `bot.log` file from the host filesystem and delivers it directly to Telegram for immediate debugging.
* **Syntax:** `/log`
* **Access:** Strictly restricted to `ADMINS` and `SUDOS`.

---

◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
### 📢 `/broadcast` — GLOBAL USER BROADCAST
◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
* **Purpose:** Dispatches an announcement to every user registered in the database.
* **Syntax:** Reply to any target message with `/broadcast`.
* **Access:** Strictly restricted to `ADMINS`.
* **Features:** Live progress updates every 20 deliveries; automatically purges deleted or blocked accounts from the database.

---

◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
### 🔄 `/toggledl` — AUTO-DOWNLOAD MODE TOGGLE
◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
* **Purpose:** Switches between aggressive download/upload fallback mode and strict bandwidth-saving direct-copy mode.
* **Syntax:** `/toggledl`
* **Access:** Strictly restricted to `ADMINS` and `SUDOS`.
* **States:**
  * **ON ✅:** If direct server-side forwarding fails, the file is downloaded and re-uploaded.
  * **OFF ❌:** If direct forwarding fails, the file is skipped to conserve server bandwidth.

---

◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
### ⚡ `/pixel` — PIXELDRAIN CDN ACCELERATOR
◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
* **Purpose:** Transforms rate-limited Pixeldrain URLs into direct, high-speed CDN stream links.
* **Syntax:** `/pixel https://pixeldrain.com/u/xxxx` (supports comma-separated URLs).
* **Access:** Strictly restricted to `ADMINS` and `SUDOS`.

---

<br>


◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
### 💾 SAVED CHANNEL MEMORY SUBSYSTEM (SOURCE & DESTINATION)
◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
* **Purpose:** Permanent database-backed storage for frequently used source and destination channels, eliminating manual channel ID lookups and enabling instant 1-click selection during forwarding tasks and watcher setup.
* **Commands:**
  * `/addsourcechannel` (Alias: `/addsource`) — Interactive or direct link/ID prompt to register and auto-name a source channel.
  * `/adddestinationchannel` (Alias: `/adddest`) — Validates bot/userbot posting rights and registers destination channel/topic into database.
  * `/viewsourcechannels` (Alias: `/viewsources`) — Paginated interactive browser (10 channels per page) with delete confirmation and 1-click `/watch` deployment.
  * `/viewdestinationchannels` (Alias: `/viewdest`) — Paginated interactive browser for saved destination channels with delete confirmation.
* **Watcher Integration:** Running `/watch` without arguments queries your saved source channels, presenting an interactive grid where tapping any channel immediately starts surveillance configuration!
* **WATCHERS 1-Click Migration:**
  * Access `/watchers` and click **`📥 Save All WATCHERS Source Channels`** to automatically extract, resolve real Telegram names, and import all active source channels into persistent memory.
  * Click **`📤 Save All WATCHERS Destination Channels`** to extract all destination peers across single-target and multi-target surveillance routes and import each destination channel once.
  * **Guaranteed Deduplication:** Canonical channel IDs are normalised and deduplicated (`user_id + channel_type + normalised channel_id`) so that multiple watcher routes targeting the same channel produce a single clean entry without modifying active routes.

---

## 🛰️ 12. LIVE WATCHER SURVEILLANCE & AUTO-ROUTING ENGINE

The Watcher system acts as an autonomous MTProto sentinel. Once configured, it continuously listens for incoming events on source channels or forum topics and immediately cascades them to assigned target destinations.

```text
       Source Channel Event ➔ Message Detected ➔ Media Filter Check
                                                        │
                         ┌──────────────────────────────┴──────────────────────────────┐
                         ▼                                                             ▼
                Matches Allowed Types                                        Disallowed (Discarded)
                         │
                         ▼
             Text Formatting & Cleaning Pass
                         │
                         ▼
        Multi-Target Iteration Loop (Target 1, 2, 3...)
                         │
                         ▼
        Inter-Message Delay Sleep (Prevents Telegram FloodWait)
                         │
                         ▼
             Dispatch to Destination Peers
```

### Multi-Target Routing
A single source channel can fan out to an arbitrary number of destination channels, groups, or topics. Each target configuration is tracked independently in the `watchers` MongoDB collection.

### Media Type Filtering Matrix
Operators can toggle filtering for specific MIME types via an inline keyboard:
* 🎬 **Video:** MP4, MKV, AVI, MOV, WEBM.
* 📁 **Document:** PDF, ZIP, RAR, ISO, APK, generic files.
* 🖼️ **Photo:** JPEG, PNG, WEBP images.
* 🎵 **Audio:** MP3, FLAC, WAV, AAC music tracks.
* 🎙️ **Voice:** OGG voice notes.
* 🎭 **Animation:** GIFs.
* 💬 **Text:** Plain text announcements without media.

---

<br>

## 🧹 13. MEDIA CLEANING & STREMIO PROCESSING PIPELINE

To satisfy strict cataloguing requirements for media servers (Stremio, Plex, Kodi), media filenames and captions are processed through a specialised sanitisation engine:

### 1. Promotional Hyperlink Removal
Original captions often contain hidden promotional links:
```html
Watch now on <a href="https://t.me/SpamPiracyChannel">Movie Vault</a> in Ultra HD!
```
The sanitiser detects promotional anchors, discards the predatory URLs, and preserves the visible text:
```html
Watch now on Movie Vault in Ultra HD!
```

### 2. Intelligent Domain Sanitisation (100+ Domains)
The cleaner maintains a deduplicated internal regex table matching over 100 promotional websites and release tags:
> *VegaMovies, 4kHdHub, Bollyflix, 1XBET, Melbet, Olamovies, MoviesMod, Khatrimaza, 9xmovies, Desiremovies, HubFlix, Bolly4u, Filmyzilla, Tamilrockers, JioRockers, KatMovieHD, MoviesFlix, MoviesVerse, MoviesRulz, TamilBlasters, SSRMovies, Ibomma, World4uFree, HDMoviesHub, Cinevood...*

The matcher accounts for mixed casing, dots, underscores, hyphens, and bracket wrapping:
* `Movie.Title.1080p.VegaMovies.mkv` ➔ `Movie.Title.1080p.mkv`
* `Movie.Title.[VegaMovies].1080p.mkv` ➔ `Movie.Title.1080p.mkv`
* `Movie_Title_4k-hd-hub_720p.mkv` ➔ `Movie Title 720p.mkv`

### 3. Absolute Protection of Media Metadata
Genuine release brackets are **never** removed:
* Audio Channels & Languages: `[Hindi]`, `[English]`, `[Dual Audio]`, `[Multi]`, `[DDP5.1]`
* Video Codecs & Standards: `[HEVC]`, `[H.265]`, `[x264]`, `[10Bit]`, `[HDR]`
* Season & Episode Identifiers: `[S01E01]`, `[Season 1]`, `[Episode 05]`
* Quality Markers: `[1080p]`, `[720p]`, `[2160p]`, `[4K]`

### 4. Split-Suffix Recognition & Pre-Extension Quality Fix
Telegram split archives possess double extensions (`.mkv.001`, `.mp4.002`). Naive parsers mistakenly treat `.001` as the extension, creating malformed names like `Movie.mkv 720p.001`.

The Lucifer engine utilizes a specialised regex:
```python
EXT_SPLIT_REGEX = re.compile(
    r'^(?P<stem>.*?)(?P<ext>\.[a-zA-Z][a-zA-Z0-9]{1,4})(?P<split>\.\d{2,4})?(\s*(?:</[^>]+>)*\s*)$',
    re.IGNORECASE
)
```
* Input: `The.Matrix.mkv.001`
* Correct Output: `The.Matrix 720p.mkv.001`
* If a valid quality marker already exists, no duplicate quality is inserted.

### 5. Standardised Decimal Caption Footer
Every media file receives an idempotent footer structure:
```text
Cleaned Caption Text

💾 Size: 1015.20 MB

⚜️ Powered By : [@luciferdatabase]
```
* File size is calculated directly from actual Telegram binary bytes or local filesystem statistics.
* Deduplication guards guarantee that retries or fallbacks never duplicate the footer block.
* Captions exceeding Telegram's 1024-character threshold are safely truncated while preserving title and footers.

---

<br>

## 📊 14. PROGRESS UI, TASK QUEUE & CANCELLATION SUBSYSTEM

During active file transfers, the engine generates an aesthetic command-centre progress display:

```text
╭━━━━━━━━━━━━━━━━━━━━━━╮
   📥 DOWNLOADING FILE
╰━━━━━━━━━━━━━━━━━━━━━━╯

📦 File: The.Matrix.1999.1080p.mkv
🔄 Status: Downloading [Chunk 1/1]
📊 Progress: [██████████░░░░░░░░░░] 52.4%

⚡ Speed: 8.42 MB/s
💾 Processed: 532.10 MB / 1015.20 MB
⏱️ ETA: 00:57
🛑 Active Task ID: `8f3b2a1c`

[ 🛑 Cancel Task ]   [ 🔄 Refresh ]
```

* **Throttled Interface Updates:** Status edits are throttled according to `STATUS_UPDATE_INTERVAL` (default: 15s) to guarantee the bot never encounters Telegram message edit rate limits.
* **Atomic Task Cancellation:** When `/cancel` is issued, `CANCEL_FLAGS[task_uuid]` is flagged. Active streams abort gracefully, temporary chunk files are purged from scratch storage, and database locks release cleanly.

---

<br>

## 🍃 15. MONGODB DATABASE ARCHITECTURE & COLLECTIONS

The MongoDB database maintains four core operational collections:

```text
                     ┌───────────────────────────────┐
                     │          DB_NAME              │
                     └───────────────┬───────────────┘
                                     │
         ┌───────────────────┬───────┴───────────┬───────────────────┐
         ▼                   ▼                   ▼                   ▼
    ┌─────────┐        ┌──────────┐        ┌───────────┐       ┌───────────┐
    │  users  │        │ settings │        │ watchers  │       │sync_prog..│
    └─────────┘        └──────────┘        └───────────┘       └───────────┘
```

### 1. `users` Collection
Stores registered users, active session strings, and personal API credentials.
```json
{
  "_id": {"$oid": "64fa12..."},
  "id": 123456789,
  "name": "Lucifer Operator",
  "session": "BQAF...",
  "api_id": 12345678,
  "api_hash": "YOUR_API_HASH"
}
```

### 2. `settings` Collection
Maintains global engine operational parameters.
```json
{
  "_id": {"$oid": "64fa13..."},
  "id": "system",
  "auto_download": true
}
```

### 3. `watchers` Collection
Persists background surveillance rules, media filters, and target channel lists.
```json
{
  "_id": {"$oid": "64fa14..."},
  "user_id": 123456789,
  "source_id": -1001987654321,
  "source_thread": null,
  "delay": 3,
  "is_restricted": true,
  "source_title": "Cinema Vault",
  "allowed_types": ["Video", "Document"],
  "text_format": ["Cleaned"],
  "targets": [
    {
      "dest_id": -1001122334455,
      "dest_thread": null,
      "dest_title": "Backup Archive"
    }
  ],
  "created_at": {"$date": "2026-09-22T04:00:00.000Z"}
}
```

### 4. `sync_progress` Collection
Maintains message ID pointers ensuring tasks resume seamlessly across server restarts.
```json
{
  "_id": {"$oid": "64fa15..."},
  "user_id": 123456789,
  "source_id": "-1001987654321",
  "dest_id": "-1001122334455",
  "last_msg_id": 1420,
  "updated_at": {"$date": "2026-09-22T04:15:30.000Z"}
}
```

---

<br>

## 💻 16. LOCAL DEPLOYMENT (WINDOWS, MACOS, LINUX)

### Step 1: Clone Repository
```bash
git clone https://github.com/ailuciferbaba-pixel/Auto-Filter-Bot-Lucifer.git
cd Auto-Filter-Bot-Lucifer
```

### Step 2: Configure Virtual Environment
* **Linux / macOS:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
* **Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```

### Step 3: Install Required Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a local `.env` file in the root directory:
```ini
API_ID=12345678
API_HASH=your_api_hash_here
BOT_TOKEN=123456789:YOUR_BOT_TOKEN_HERE
DB_URI=mongodb+srv://<username>:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
DB_NAME=Lucifer_Local_Dev
ADMINS=123456789
LOG_CHANNEL=-1001234567890
STATUS_UPDATE_INTERVAL=15
WAITING_TIME=3
PORT=8080
```

### Step 5: Execute Application
```bash
python restrict_bot.py
```

---

<br>

## 🐧 17. PRODUCTION VPS DEPLOYMENT (UBUNTU/DEBIAN + SYSTEMD)

Follow this enterprise deployment guide to run the engine continuously as a sovereign Linux system service.

### Step 1: System Package Preparation
```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3 python3-pip python3-venv git 7zip coreutils build-essential python3-dev
```

### Step 2: Deploy Project Code
```bash
sudo mkdir -p /opt/lucifer-engine
sudo chown -R $USER:$USER /opt/lucifer-engine
cd /opt/lucifer-engine
git clone https://github.com/ailuciferbaba-pixel/Auto-Filter-Bot-Lucifer.git .
python3 -m venv venv
source venv/bin/activate
pip install --no-cache-dir -r requirements.txt
```

### Step 3: Configure System Environment
Create the configuration file at `/opt/lucifer-engine/.env`:
```bash
nano /opt/lucifer-engine/.env
```
Populate with your verified credentials:
```ini
API_ID=12345678
API_HASH=your_api_hash_here
BOT_TOKEN=123456789:YOUR_BOT_TOKEN_HERE
DB_URI=mongodb+srv://<username>:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
DB_NAME=Lucifer_VPS_Prod
ADMINS=123456789
LOG_CHANNEL=-1001234567890
STATUS_UPDATE_INTERVAL=15
WAITING_TIME=3
PORT=8080
```

### Step 4: Create Systemd Service Unit
Create `/etc/systemd/system/lucifer.service`:
```bash
sudo nano /etc/systemd/system/lucifer.service
```
Insert the service definition:
```ini
[Unit]
Description=Lucifer Morningstar Telegram Automation Engine
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/lucifer-engine
EnvironmentFile=/opt/lucifer-engine/.env
ExecStart=/opt/lucifer-engine/venv/bin/python3 restrict_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

### Step 5: Enable & Launch Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable lucifer.service
sudo systemctl start lucifer.service
```

### Step 6: Monitor Live Telemetry
```bash
# View real-time systemd service journal
sudo journalctl -u lucifer.service -f

# View internal application audit log
tail -f /opt/lucifer-engine/bot.log
```

---

<br>

## 🐳 18. CONTAINERISED DOCKER DEPLOYMENT

The repository includes a production-optimised `Dockerfile` utilizing `python:3.10-slim` with compiled C-libraries and 7zip support.

### Step 1: Build the Docker Image
```bash
docker build -t lucifer-morningstar:latest .
```

### Step 2: Execute Container with Environment Injection
```bash
docker run -d \
  --name lucifer-engine \
  --restart always \
  -p 8080:8080 \
  -v lucifer_data:/app/downloads \
  --env-file .env \
  lucifer-morningstar:latest
```

### Step 3: Inspect Logs & Lifecycle
```bash
# Stream live container logs
docker logs -f lucifer-engine

# Inspect container operational status
docker ps -f name=lucifer-engine

# Stop and restart container
docker stop lucifer-engine
docker start lucifer-engine
```

---

<br>

## ☁️ 19. RENDER CLOUD PLATFORM DEPLOYMENT

1. Sign in to [Render](https://render.com/).
2. Click **New ➔ Web Service** (or Background Worker).
3. Connect your GitHub repository: `ailuciferbaba-pixel/Auto-Filter-Bot-Lucifer`.
4. Configure Build and Runtime settings:
   * **Environment:** `Docker` (Render automatically uses your repository `Dockerfile`).
   * **Region:** Choose the region closest to your MongoDB cluster.
   * **Plan:** Standard / Starter.
5. In the **Environment Variables** panel, add:
   * `API_ID`
   * `API_HASH`
   * `BOT_TOKEN`
   * `DB_URI`
   * `DB_NAME`
   * `ADMINS`
   * `LOG_CHANNEL`
   * `PORT`: Set to `8080`
6. Click **Create Web Service**.
7. Render will build the Docker container and launch the application. The internal web server will satisfy Render's HTTP port check on port `8080`.

---

<br>

## ☁️ 20. KOYEB CLOUD PLATFORM DEPLOYMENT

1. Authenticate at [Koyeb](https://www.koyeb.com/).
2. Select **Create App ➔ GitHub**.
3. Choose the repository and set deployment method to **Dockerfile**.
4. Configure the Health Check probe:
   * **Protocol:** `HTTP`
   * **Port:** `8080`
   * **Path:** `/health`
5. Under **Environment Variables**, define your configuration:
   * `API_ID`, `API_HASH`, `BOT_TOKEN`, `DB_URI`, `DB_NAME`, `ADMINS`, `PORT=8080`.
6. Select **Deploy**. Koyeb will monitor `/health` and maintain high availability.

---

<br>

## ☁️ 21. SEVALLA CLOUD PLATFORM DEPLOYMENT

1. Log into your [Sevalla Console](https://sevalla.com/).
2. Click **Create Application ➔ Git Repository**.
3. Select your GitHub repository branch `main`.
4. Select **Docker Deployment** to leverage the native `Dockerfile`.
5. Under Networking, configure the exposed port to `8080` for health probes.
6. Populate all required Environment Variables (`API_ID`, `API_HASH`, `BOT_TOKEN`, `DB_URI`, `DB_NAME`).
7. Click **Deploy Now**. Monitor build progress via the deployment log viewer.

---

<br>

## 🤗 22. HUGGING FACE SPACES DEPLOYMENT

1. Navigate to [Hugging Face Spaces](https://huggingface.co/spaces).
2. Click **Create new Space**.
3. Set **Space SDK** to **Docker** (Blank Docker template).
4. Clone your Space repository locally or push your existing repository code to the Hugging Face Space git remote.
5. In **Space Settings ➔ Repository Secrets**, configure your keys:
   * `API_ID`, `API_HASH`, `BOT_TOKEN`, `DB_URI`, `DB_NAME`, `ADMINS`, `PORT=7860`.
   *(Note: Hugging Face default container port is 7860; set `PORT=7860` in Space secrets).*
6. The Space will build and maintain container execution.

---

<br>

## 🧬 23. MULTI-INSTANCE DISTRIBUTED SCALING ARCHITECTURE

When processing hundreds of thousands of files across large channel networks, a single Telegram account or bot token faces strict MTProto limits.

You can construct a **Distributed Multi-Clone Cluster**:

```text
                           MONGODB ATLAS CLOUD BRAIN
                          (Unified Shared DB_URI)
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
  [ BOT INSTANCE 1 ]          [ BOT INSTANCE 2 ]          [ BOT INSTANCE 3 ]
  Host: VPS Alpha             Host: Render                Host: Koyeb
  DB_NAME: Cluster_Alpha      DB_NAME: Cluster_Beta       DB_NAME: Cluster_Gamma
  Telegram Account A          Telegram Account B          Telegram Account C
  Processing: 1 - 25,000      Processing: 25,001 - 50,000 Processing: 50,001 - 75,000
```

### Rules for Distributed Scaling:
1. **Identical `DB_URI`:** Connect all bots to the same MongoDB cluster to share user profiles and watcher telemetry.
2. **Distinct `DB_NAME`:** Each bot instance **must** have a unique `DB_NAME` (e.g. `Cluster_Alpha`, `Cluster_Beta`). If instances share a `DB_NAME`, their task managers will collide.
3. **Partitioned Ranges:** Divide batch tasks evenly across instances to process massive archives in parallel.

---

<br>

## 📁 24. OFFICIAL PROJECT STRUCTURE

```text
Auto-Filter-Bot-Lucifer/
│
├── 🐍 restrict_bot.py      # Core MTProto engine, handlers, cleaner, watchers & web server
├── 📦 requirements.txt     # Python runtime library dependencies (Pyrogram, Motor, etc.)
├── 🐳 Dockerfile           # Multi-stage production container definition (Python 3.10-slim)
├── 📜 README.md            # Sovereign technical architectural manual & documentation
├── 🛑 .gitignore           # Ignores __pycache__, logs, sessions, and environment secrets
│
└── 📂 downloads/           # Ephemeral scratch storage for chunked processing & 7z splits
```

---

<br>

## 🛠️ 25. COMPREHENSIVE TROUBLESHOOTING MANUAL

| Symptom / Error | Root Cause | Verified Remediation |
| :--- | :--- | :--- |
| `FloodWait(x seconds)` | Telegram rate-limiting consecutive API requests. | Do not terminate the process. The bot enters an automated sleep state for the exact required duration and resumes automatically. |
| `AuthKeyUnregistered` | Userbot session revoked or terminated in Telegram Devices. | Issue `/logout` to purge corrupted local records, then run `/login` to generate a fresh authenticated session. |
| `FileReferenceExpired` | Telegram file cache expired during an extended batch job. | The bot contains automatic file reference refresh logic. If it persists, re-issue the `/dl` command to fetch updated references. |
| `ChatForwardsRestricted` | Channel prohibits direct forwarding. | Ensure `auto_download` is ON (check via `/status` or enable via `/toggledl`). The bot will download and re-upload the file. |
| `PeerIdInvalid` / `ChannelPrivate` | Bot or Userbot has not joined the target peer. | Ensure your bot (and logged-in user account) is added as an **Administrator** in both source and destination channels. |
| `CaptionTooLong` | Caption exceeds Telegram's 1024-character limit. | Built-in `prepare_caption_fallback()` truncates excess body text while strictly preserving file size and join signatures. |
| `ServerSelectionTimeoutError` | MongoDB connection refused or timed out. | Verify `DB_URI` password credentials and ensure MongoDB Atlas Network Access whitelist is set to `0.0.0.0/0`. |
| Port Binding / Crash on Cloud | Cloud host cannot detect active HTTP server on `PORT`. | The bot includes an integrated `aiohttp` server. Ensure environment variable `PORT` matches the platform's expected port (e.g., 8080). |
| Out of Disk Space during Split | Host scratch disk filled by multi-GB video files. | The built-in watchdog purges stalled files. For heavy multi-GB processing, ensure VPS has SSD storage equal to `2 × largest file`. |

---

<br>

## ❓ 26. FREQUENTLY ASKED QUESTIONS (FAQ)

#### Q1: Does the bot download every file to my server?
**No.** The engine prioritizes direct server-side forwarding (`client.copy_message`). Files are only downloaded to local storage if the source channel restricts forwarding or direct copying fails.

#### Q2: What happens if the server crashes during a 10,000-file batch?
The bot maintains message tracking in MongoDB (`sync_progress` collection). When restarted, the task manager identifies the exact last processed message ID and resumes from that point without duplicate transfers.

#### Q3: How does the bot handle files larger than 2GB?
Standard Telegram bot tokens are restricted to 2000MB uploads. When a file exceeds this threshold, the engine invokes `split_file_python()`, which divides the file into 1900MB parts using native `split` or `7zip` before uploading.

#### Q4: Why must the login OTP code be sent with spaces?
Telegram employs automated heuristics that intercept and invalidate login codes sent inside Telegram chats. Typing the code with spaces (e.g., `1 2 3 4 5`) bypasses this detection filter.

#### Q5: Can I run multiple bots connected to the same database?
**Yes.** Use the same `DB_URI` but assign a distinct `DB_NAME` to each instance to prevent task pointer collisions.

---

<br>

## 🔒 27. SECURITY BEST PRACTICES & CREDENTIAL HYGIENE

```text
⚠️ CRITICAL SECURITY WARNING ⚠️
Never commit, share, or upload any of the following credentials:
• BOT_TOKEN
• API_HASH
• DB_URI (containing user passwords)
• STRING_SESSION
• SESSION_ENC_KEY
• Telegram Login OTPs or 2FA Passwords
```

* **Git Secret Prevention:** The repository `.gitignore` is preconfigured to ignore `.env`, `bot.log`, and `*.session` files. Always verify staged changes with `git status` prior to committing.
* **Database Access Control:** Restrict MongoDB users to specific database boundaries. Do not use Atlas administrative root users for runtime bot connections.
* **Session Protection:** Pyrogram session strings grant full access to your Telegram account. Never paste session strings into public groups or logs.
* **Encryption at Rest:** Set `SESSION_ENC_KEY` to encrypt session strings and API hashes in MongoDB; `/log` now sends a redacted copy with tokens and long session strings removed.

---

<br>

## 🔄 28. MAINTENANCE, BACKUPS & UPDATE PROCEDURES

### Updating an Existing Deployment
```bash
# 1. Access project directory
cd /opt/lucifer-engine

# 2. Halt running service
sudo systemctl stop lucifer.service

# 3. Pull latest updates from Git
git pull origin main

# 4. Activate virtual environment and update packages
source venv/bin/activate
pip install --upgrade -r requirements.txt

# 5. Restart service and verify telemetry
sudo systemctl start lucifer.service
sudo journalctl -u lucifer.service -f
```

### Docker Container Redeployment
```bash
# Pull and rebuild container image
docker build -t lucifer-morningstar:latest .

# Stop and recreate container
docker stop lucifer-engine && docker rm lucifer-engine
docker run -d --name lucifer-engine --restart always -p 8080:8080 --env-file .env lucifer-morningstar:latest
```

---

<br>

## 📜 29. LICENCE INFORMATION

This project is distributed under the terms of the **MIT Licence**.

```text
MIT License

Copyright (c) 2026 Lucifer Morningstar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<br>

<div align="center">

◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
## 👑 30. THE LUCIFER MORNINGSTAR CITADEL
◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈

<br>

### ⚜️ **Lucifer Morningstar** ⚜️
*Lead Architect, Core Systems Engineer & Project Maintainer*

<br>

> *“True engineering perfection is not attained when there is nothing left to add, but when every superfluous element has been stripped away, leaving only unyielding resilience and sovereign precision.”*

<br>

[![Official Channel](https://img.shields.io/badge/Telegram-Official_Channel-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/LuciferOpenSource)
[![Support Group](https://img.shields.io/badge/Telegram-Support_Group-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/LuciferOpenSourceDiscussionGroup)
[![Request Group](https://img.shields.io/badge/Telegram-Movie_Request_Group-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/RequestLuciferDatabase)
[![GitHub](https://img.shields.io/badge/GitHub-ailuciferbaba--pixel-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/ailuciferbaba-pixel)

<br>

**Crafted with unwavering discipline, sovereign precision, and cryptographic fidelity.**  
*© 2026 Lucifer Morningstar. All Rights Reserved.*

</div>
