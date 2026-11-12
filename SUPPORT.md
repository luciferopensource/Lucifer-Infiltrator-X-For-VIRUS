# Support & Community Help

Welcome to the **Lucifer Infiltrator X** support center. If you encounter issues while configuring, deploying, or running the bot, use the resources outlined below to obtain assistance.

---

## Support Philosophy

We are committed to maintaining a robust, stable, and accessible automation engine. To ensure community support remains efficient:
1. **Self-Service First:** Always consult [README.md](README.md) and [SECURITY.md](SECURITY.md) before submitting a support inquiry.
2. **Provide Actionable Context:** Vague reports ("bot not working") cannot be diagnosed without logs and environment details.
3. **Respect Privacy:** Redact all API keys, bot tokens, session strings, and private channel IDs before posting logs.

---

## Where to Ask for Help

| Channel | Purpose | Link |
| :------ | :------ | :--- |
| 📢 **Official Citadel** | Project updates, announcements, release notes | [@LuciferOpenSource](https://t.me/LuciferOpenSource) |
| 💬 **Support Group** | Interactive community assistance, setup troubleshooting | [@LuciferOpenSourceDiscussionGroup](https://t.me/LuciferOpenSourceDiscussionGroup) |
| 🍿 **Database Index** | Sovereign media archive and indexation requests | [@RequestLuciferDatabase](https://t.me/RequestLuciferDatabase) |
| 🐙 **GitHub Issues** | Verified reproducible bug reports and feature requests | [GitHub Issues](https://github.com/luciferopensource/Lucifer-Infiltrator-X-/issues) |
| 🦊 **GitLab Issues** | Alternative issue tracking and merge requests | [GitLab Issues](https://gitlab.com/luciferopensource/lucifer-infiltrator-x/-/issues) |

---

## Common Troubleshooting Scenarios

### 1. `CHANNEL_INVALID` or `CHANNEL_PRIVATE` Errors
- **Cause:** The bot or userbot account is not a member or administrator of the specified source or destination channel.
- **Solution:** Verify that the userbot account has joined the private channel, and the bot account is added as an administrator with posting permissions in the destination channel.

### 2. High Delay in Batch Forwarding (15-Minute Stalls)
- **Cause:** Telegram MTProto flood-wait protections or connection timeout during continuous downloads.
- **Solution:** Verify you are running version `v2.4.0` or higher, which includes optimized rate-limiting backoffs and persistent connection keep-alives.

### 3. Koyeb / Render Health Check Fails
- **Cause:** Port mismatch or web server failed to bind.
- **Solution:** Ensure `PORT=10000` (or `8080`) is exposed. The integrated `aiohttp` server responds with HTTP 200 on `/health` and root `/`.

### 4. OTP Login Code Formatting
- **Cause:** Telegram deletes messages containing raw numeric OTP login codes to prevent interception.
- **Solution:** Send the OTP code with spaces between each digit (e.g., `1 2 3 4 5`).

---

## How to Provide Logs Safely

When asking for help in the support group or opening an issue, provide relevant output from `bot.log` or your terminal:

```bash
# Redact sensitive lines before posting!
# Replace your BOT_TOKEN with [REDACTED_BOT_TOKEN]
# Replace your MONGO_URI with [REDACTED_MONGO_URI]
# Replace your SESSION_STRING with [REDACTED_SESSION]
```

---

## Support Boundaries

The community maintainers provide support for:
- Core Lucifer Infiltrator X bugs and runtime errors.
- Configuration and deployment troubleshooting on supported platforms (Linux, Docker, Koyeb, Render).
- Feature guidance and documentation clarification.

We do **NOT** provide support for:
- Bypassing Telegram account bans resulting from aggressive abuse or spamming.
- Modifying the bot for commercial resale or proprietary unauthorized redistribution.
