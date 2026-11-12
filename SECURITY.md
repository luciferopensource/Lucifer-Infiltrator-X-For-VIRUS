# Security Policy

The security and privacy of our users and contributors are paramount to the **Lucifer Infiltrator X** project. This document outlines our vulnerability reporting process, supported software versions, and best practices for credential handling.

---

## Supported Versions

Only the latest release branch of Lucifer Infiltrator X receives official security fixes and updates.

| Version | Supported          | Security Support Level |
| :------ | :----------------- | :--------------------- |
| 2.4.x   | :white_check_mark: | Full active security support and bug fixes |
| 2.3.x   | :x:                | Deprecated — please upgrade to 2.4.x |
| < 2.3.0 | :x:                | Unsupported |

---

## Reporting a Vulnerability

If you discover a security vulnerability within Lucifer Infiltrator X, please report it responsibly:

- **Primary Contact:** Send an email directly to `ailuciferbaba@gmail.com`.
- **Subject Line:** `[SECURITY] Lucifer Infiltrator X Vulnerability Report`
- **Alternative Contact:** Message the project lead via the official support group: [@LuciferOpenSourceDiscussionGroup](https://t.me/LuciferOpenSourceDiscussionGroup)

**Please do NOT file public GitHub or GitLab issues for sensitive security vulnerabilities.**

### What to Include in Your Report
To assist us in verifying and addressing the issue quickly, please include:
1. Description of the vulnerability and its potential impact.
2. Step-by-step reproduction instructions or proof-of-concept (PoC).
3. Affected components (e.g., MTProto session handler, caption parser, MongoDB connection pool).
4. Environment details (Python version, OS, Docker environment).

### Response Timeline
- **Initial Acknowledgment:** Within 48 hours of receipt.
- **Triage & Assessment:** Within 5 business days.
- **Remediation & Patch Release:** Coordinated disclosure and security release deployed as soon as a fix is validated.

---

## Credential & Secret Hygiene

Lucifer Infiltrator X requires sensitive credentials to communicate with Telegram and MongoDB. Never expose these secrets:

- `BOT_TOKEN`: Telegram Bot API token issued by [@BotFather](https://t.me/BotFather).
- `API_ID` & `API_HASH`: Telegram application credentials issued by [my.telegram.org](https://my.telegram.org).
- `SESSION_STRING` / `*.session`: Authenticated MTProto user session providing full access to your Telegram account.
- `MONGO_URI`: Database connection string containing administrative user credentials.

### Protection Guidelines
1. Always inject credentials through environment variables or secure vault managers.
2. Never hardcode tokens or credentials in source code.
3. Ensure `.env` and `*.session` files remain in `.gitignore` at all times.
4. When sharing diagnostic logs for troubleshooting, ensure all session strings, phone numbers, and tokens are completely redacted.

---

## Deployment & Infrastructure Security

- **Container Isolation:** In containerized deployments (Docker/Kubernetes), isolate the container network and run with minimal required privileges.
- **Database Access:** Configure IP access lists in MongoDB Atlas and enable TLS encryption for all database connections.
- **Cloud Platform Environment:** Never commit production `.env` files to cloud hosting repositories. Use platform-native environment variable injection (Render, Koyeb, Sevalla).
