# Changelog

All notable changes to the **Lucifer Infiltrator X** engine are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.4.0] — 2026-10-11

### Added
- **Intelligent Title & Footer Hyperlinking:** Integrated automated markdown hyperlinking connecting sanitized media titles and official database footers directly to sovereign repository endpoints (`https://t.me/luciferdatabase`).
- **Resilient Channel Identifier Resolution:** Implemented robust multi-strategy channel peer resolution resolving both numeric IDs (`-100...`) and public usernames to prevent `CHANNEL_INVALID` errors during administrative log dispatches.

### Changed
- **Unicode Promotional Banner Sanitisation:** Upgraded caption cleaning filters to aggressively identify and strip multi-line Unicode promotional banners, join invitations, and trailing marketing snippets while preserving core release identifiers.
- **Batch Processing Rate Stabilisation:** Tuned adaptive forwarding delay loops to eliminate Pyrogram client disconnection stalls during extended mass-synchronization queues.

### Fixed
- **Pyrogram MTProto Disconnection Resilience:** Resolved an issue where high-frequency flood wait cycles could trigger unhandled client detachment during continuous 15-minute sync intervals.
- **Clean Caption Format Alignment:** Ensured file size footers (`💾 Size: X.XX GB`) consistently format using standardized two-decimal precision.

---

## [2.3.0] — 2026-09-26

### Added
- **Multi-Target Watcher Routing:** Implemented `/watch` engine supporting real-time surveillance of source channels with simultaneous dispatch to multiple destination channels.
- **Asynchronous 7-Zip Multi-Part Extraction:** Built background extraction routines capable of uncompressing `.7z`, `.zip`, and `.rar` multi-volume archives before channel upload.
- **Media Type Filtering Matrix:** Added granular media classification supporting document, video, audio, and photo selective auto-forwarding.
- **Koyeb & Render Health Check Daemon:** Embedded an asynchronous `aiohttp` HTTP server on port 10000 / 8080 to satisfy cloud hosting platform liveness probes.

### Changed
- **Database Schema Optimisation:** Migrated surveillance watchers and user settings into segregated MongoDB Motor collections with compound indexation.

### Fixed
- **Memory Pressure in Large Batch Queues:** Optimized memory footprint during multi-gigabyte media stream transfers.

---

## [2.0.0] — 2026-09-21

### Added
- **Initial Release of Lucifer Infiltrator X:** Modern asynchronous Telegram restricted content automation engine.
- **Dual-Client MTProto Synchronization:** Simultaneous orchestration of Telegram Bot API and MTProto Userbot session for bypassing restricted channel download flags.
- **Domain Sanitisation Pipeline:** Automated regex filtering removing over 100 promotional piracy and advertising domain patterns from incoming media captions.
- **Interactive Session Controller:** In-chat OTP authentication mechanism via `/login` and `/logout` for dynamic userbot setup without redeployment.
- **Containerised Deployment:** Official multi-architecture Dockerfile built upon Python 3.10-slim with compiled C-accelerators (`tgcrypto`, `uvloop`).
