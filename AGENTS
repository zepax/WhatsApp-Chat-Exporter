**name:** WhatsApp Exporter to HTML/JSON/PDF

## 🟢 Main Objective

Automate the conversion of WhatsApp backups (.zip, .tar, .sqlite, or .json files) into a navigable HTML site, normalized JSON artifacts, and optional per-chat PDF export. The user should be able to run the process via CLI with simple parameters and receive a well-structured, easily explorable folder with included media files.

---

## ⚙️ Environment & Stack

- Python ≥ 3.11 (CPython implementation)
- Typer for CLI, Jinja2 for HTML templates, TailwindCSS 3 (self-hosted, no CDN) for styling
- Data validation with Pydantic v2
- Incremental parsing using ijson and sqlite3
- Optional PDF export with WeasyPrint or pdfkit (both fully open source)
- Asyncio, aiofiles, and aiohttp for I/O and concurrency
- Testing with pytest and pytest-asyncio, minimum 85% coverage
- Dependency management with Poetry
- Linting with Ruff and Black, strict typing with mypy
- Documentation generated with MkDocs

---

## 📁 Expected Input

- Compressed file (.zip, .tar.gz) exported from WhatsApp, iOS chatstorage.sqlite, or Android chat.json export
- Output folder for export (default: `./export`)
- Option to export PDF (`--export-pdf`)
- Option to anonymize sensitive data (`--redact`)
- Option for Telegram notification (environment variables: `NOTIFY_TELEGRAM_TOKEN`, `NOTIFY_CHAT_ID`)
- Configurable timezone (`TZ_DEFAULT`)

---

## 📂 Output Structure

export/
├── index.html # Navigable homepage
├── chats/
│ ├── chat_0001.html
│ ├── chat_0002.html
│ └── ...
├── chats.json # All messages (normalized JSON)
├── media/
│ ├── img_0001.jpg
│ └── ...
├── pdf/ # Present only if --export-pdf is used
│ ├── chat_0001.pdf
│ └── ...
└── static/ # CSS, fonts, and static resources

---

## 🧪 Automated Testing

- All changes must include automated tests.
- Tests are run with `pytest` without external dependencies.
- Use mocks for network and large files.
- Included fixtures: `mini_chat.json` (small case), `huge_chat.json.gz` (realistic case).

---

## 🧰 Best Practices & Rules

- Never block the event loop; use async I/O exclusively.
- Code must comply with PEP8, use strict mypy typing, and limit lines to 99 characters.
- HTML templates must have autoescaping enabled (Jinja2).
- Never upload, export, or collect user files outside the designated export folder.
- When anonymization is requested, redact names, phone numbers, and media files accordingly.
- Prioritize environment variables for sensitive paths and tokens.
- Document all public functions following Google style.
- Display process progress in CLI using Rich.
- Use only approved open-source dependencies, including but not limited to:
  - Typer (CLI)
  - Jinja2 (templates)
  - TailwindCSS (self-hosted)
  - Pydantic (validation)
  - aiohttp, aiofiles (async I/O)
  - pytest, pytest-asyncio (testing)
  - Ruff, Black (linting and formatting)
  - mypy (typing)
  - WeasyPrint, pdfkit (PDF export)

---

## 🔒 Security, Privacy & Licensing

- All dependencies and tools must be open source and compatible with project licensing.
- Handle user data with extreme care to prevent any leakage or unauthorized exposure.
- Never send data to external services without explicit user consent.
- Automatically redact sensitive data from exports if requested.
- Secure copied media and clean temporary files upon completion.
- Respect all licenses of included software and properly document third-party usage.

---

## 📝 Sample Tasks for the Agent

- "Fix parser to support iOS 2024 chatstorage.sqlite."
- "Add `--export-pdf` option to CLI."
- "Improve HTML templates to correctly display stickers and emojis."
- "Refactor Message model to normalize dates in ISO 8601 format."
- "Implement Telegram notifications on process completion."
- "Optimize media export with asyncio concurrency."

---

## ⚠️ Limits & Restrictions

- Never modify files outside the working directory.
- Do not install proprietary libraries or use commercial services.
- Do not execute dangerous or destructive shell commands.
- Do not alter network configurations or expose user data.

---

## 📖 Available Resources

- Project structure, AGENTS.md template, test fixtures, and example environment variables.

---

## 🟢 Success Criteria

The agent must deliver clean, secure, and well-tested code that achieves the goal of exporting and navigating WhatsApp data simply and privately, strictly following all rules and restrictions stated above.
