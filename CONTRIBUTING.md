# Contributing to Lucifer Infiltrator X

Thank you for your interest in contributing to **Lucifer Infiltrator X**! We welcome bug reports, feature enhancements, documentation improvements, and architectural optimizations.

---

## Welcome / Contribution Philosophy

We value clean code, high concurrency, strict error handling, and robust MTProto interaction. All contributions should adhere to the following principles:
- **Zero Fabrication:** Test all logic against actual MTProto behaviors and edge cases.
- **Asynchronous Integrity:** Never block the main asyncio event loop; use native async calls and threadpools where necessary for CPU-bound tasks.
- **Privacy First:** Ensure credentials, tokens, session strings, and personal identifying data are strictly isolated and never committed.

---

## Before You Begin

1. Review the [Code of Conduct](CODE_OF_CONDUCT.md).
2. Check existing [Issues](https://github.com/luciferopensource/Lucifer-Infiltrator-X-/issues) and [Merge Requests](https://gitlab.com/luciferopensource/lucifer-infiltrator-x/-/merge_requests) to avoid duplicate work.
3. For major architectural changes or new bot commands, discuss your proposal in the [Support Group](https://t.me/LuciferOpenSourceDiscussionGroup) first.

---

## Development Environment & Prerequisites

- **Python:** Version 3.10 or higher.
- **Database:** MongoDB instance (MongoDB 5.0+ or MongoDB Atlas free M0 sandbox).
- **Archive Tool:** 7-Zip command-line utility (`7z` / `p7zip-full`).
- **Telegram Credentials:** Valid `API_ID`, `API_HASH`, and `BOT_TOKEN` from [my.telegram.org](https://my.telegram.org) and [@BotFather](https://t.me/BotFather).
- **C-Compilers (Optional but recommended):** `gcc` / `build-essential` and `python3-dev` for compiling `tgcrypto` and `uvloop`.

---

## Local Setup

### 1. Clone the Repository
```bash
git clone https://github.com/luciferopensource/Lucifer-Infiltrator-X-.git
cd Lucifer-Infiltrator-X-
```

### 2. Configure Virtual Environment
```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment
Copy the example environment configuration (or create `.env` based on repository documentation):
```bash
cp .env.example .env  # If template exists, or populate .env manually
```
Required environment variables:
```env
API_ID=12345678
API_HASH=your_api_hash_here
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority
OWNER_ID=123456789
LOG_CHANNEL=-1001234567890
```

---

## Development Workflow & Coding Standards

- **Style Guide:** Follow [PEP 8](https://peps.python.org/pep-0008/) conventions.
- **Formatting:** Use 4 spaces for Python indentation as declared in [.editorconfig](.editorconfig).
- **Line Endings:** LF line endings are mandatory across all platforms.
- **Caption Regex Quality:** Any modifications to caption sanitisation, domain stripping, or title formatting must be thoroughly validated against multi-line Unicode strings and edge-case promotional text.
- **Commit Messages:** Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:
  - `feat: add multi-account rotation support`
  - `fix(caption): prevent regex stripping on filenames containing hyphens`
  - `perf: optimize streaming buffer size for 2GB+ media files`
  - `docs: update deployment instructions for Koyeb`
  - `chore: update requirements and Dockerfile dependencies`

---

## Pull Request & Merge Request Checklist

Before submitting a PR / MR:
1. Ensure the code compiles and runs cleanly without syntax or runtime errors.
2. Verify that no secrets, `.env` files, or Telegram `.session` files are staged.
3. Verify that `README.md` and project governance files remain uncorrupted.
4. Test the changes with live Telegram channels or sandbox test suites.
5. Provide a concise description of what was changed and why in your PR/MR description.

---

## Contributor Recognition

Contributors who provide valuable enhancements or bug fixes will be acknowledged in [AUTHORS.md](AUTHORS.md) and within our community update announcements.
