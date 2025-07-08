<<<<<<< HEAD
# Exportador de WhatsApp a HTML/JSON/PDF
**name:** Exportador de WhatsApp a HTML/JSON/PDF
## 🟢 Main Objective

Automate the conversion of WhatsApp backups (.zip, .tar, .sqlite, or .json files) into a navigable HTML site, normalized JSON artifacts, and optional per-chat PDF export. The user should be able to run the process via CLI with simple parameters and receive a well-structured, easily explorable folder with included media files.

---

## ⚙️ Environment & Stack

- Python ≥ 3.11 (CPython)
- Typer (CLI), Jinja2 (HTML templates), TailwindCSS 3 (self-hosted)
- Data validation with Pydantic v2
- Incremental parsing using ijson/sqlite3
- PDF export with weasyprint or pdfkit (optional)
- Asyncio and aiofiles/aiohttp for I/O and concurrent tasks
- Testing with pytest, pytest-asyncio, minimum 85% coverage
- Dependency management with Poetry
- Linting with Ruff and Black, strict typing with mypy
- Documentation generated with MkDocs

---
## 📁 Expected Input

- Compressed file (.zip, .tar.gz) exported from WhatsApp, iOS chatstorage.sqlite, or Android chat.json export
- Output folder for export (default: `./export`)
- Option to export PDF (`--export-pdf`)
- Option to anonymize data (`--redact`)
- Option for Telegram notification (variables: NOTIFY_TELEGRAM_TOKEN, NOTIFY_CHAT_ID)
- Configurable timezone (`TZ_DEFAULT`)

---

## 📂 Output Structure

export/
├── index.html                  # Navigable homepage
├── chats/
│   ├── chat\_0001.html
│   ├── chat\_0002.html
│   └── ...
├── chats.json                  # All messages (normalized JSON)
├── media/
│   ├── img\_0001.jpg
│   └── ...
├── pdf/
│   ├── chat\_0001.pdf           # Only if --export-pdf
│   └── ...
└── static/                     # CSS, fonts, resources

---

## 🧪 Testing

- All changes must include automated tests.
- Tests are run with `pytest`, with no external dependencies.
- Use mocks for network and large files.
- Fixtures: `mini_chat.json` (small case), `huge_chat.json.gz` (realistic case)

---

## 🧰 Best Practices & Rules

- Never block the event loop (use async I/O).
- Code must be PEP8, mypy strict, and max 99 characters per line.
- HTML templates must be autoescaped (Jinja2).
- Never upload, export, or collect user files outside the designated export folder.
- If the user requests anonymization, anonymize names, phone numbers, and media.
- Prioritize environment variables for sensitive paths and tokens.
- Document all public functions (Google style).
- Show process progress in CLI using Rich.
- Use only approved open-source dependencies.

---

## 🔒 Security & Privacy

- Never send data to external services without explicit consent.
- Automatically redact sensitive data in export if requested.
- Protect copied media and clean up temporary files upon completion.

---

## 📝 Example Tasks for the Agent

- "Fix the parser to support iOS 2024 chatstorage.sqlite."
- "Add --export-pdf option to the CLI."
- "Improve the HTML template to display stickers and emojis correctly."
- "Refactor the Message model to normalize dates as ISO 8601."
- "Implement Telegram notifications upon process completion."
- "Speed up media export using asyncio."

---

## ⚠️ Limits

- Never modify files outside the working directory.
- Do not install proprietary libraries or use commercial services.
- Do not send dangerous or destructive shell commands.
- Do not alter network settings or expose user data.

---

## 📖 Available Resources

- Project structure, AGENTS.md template, test fixtures, and sample environment variables.

---

## 🟢 Success Criteria

The agent must deliver clean, safe, and well-tested code that fulfills the goal of exporting and navigating WhatsApp information in a simple and private way, strictly following all the rules above.
```
=======
# Exportador de WhatsApp a HTML/JSON/PDF
**name:** Exportador de WhatsApp a HTML/JSON/PDF
## 🟢 Main Objective

Automate the conversion of WhatsApp backups (.zip, .tar, .sqlite, or .json files) into a navigable HTML site, normalized JSON artifacts, and optional per-chat PDF export. The user should be able to run the process via CLI with simple parameters and receive a well-structured, easily explorable folder with included media files.

---

## ⚙️ Environment & Stack

- Python ≥ 3.11 (CPython)
- Typer (CLI), Jinja2 (HTML templates), TailwindCSS 3 (self-hosted)
- Data validation with Pydantic v2
- Incremental parsing using ijson/sqlite3
- PDF export with weasyprint or pdfkit (optional)
- Asyncio and aiofiles/aiohttp for I/O and concurrent tasks
- Testing with pytest, pytest-asyncio, minimum 85% coverage
- Dependency management with Poetry
- Linting with Ruff and Black, strict typing with mypy
- Documentation generated with MkDocs

---
## 📁 Expected Input

- Compressed file (.zip, .tar.gz) exported from WhatsApp, iOS chatstorage.sqlite, or Android chat.json export
- Output folder for export (default: `./export`)
- Option to export PDF (`--export-pdf`)
- Option to anonymize data (`--redact`)
- Option for Telegram notification (variables: NOTIFY_TELEGRAM_TOKEN, NOTIFY_CHAT_ID)
- Configurable timezone (`TZ_DEFAULT`)

---

## 📂 Output Structure

export/
├── index.html                  # Navigable homepage
├── chats/
│   ├── chat\_0001.html
│   ├── chat\_0002.html
│   └── ...
├── chats.json                  # All messages (normalized JSON)
├── media/
│   ├── img\_0001.jpg
│   └── ...
├── pdf/
│   ├── chat\_0001.pdf           # Only if --export-pdf
│   └── ...
└── static/                     # CSS, fonts, resources

---

## 🧪 Testing

- All changes must include automated tests.
- Tests are run with `pytest`, with no external dependencies.
- Use mocks for network and large files.
- Fixtures: `mini_chat.json` (small case), `huge_chat.json.gz` (realistic case)

---

## 🧰 Best Practices & Rules

- Never block the event loop (use async I/O).
- Code must be PEP8, mypy strict, and max 99 characters per line.
- HTML templates must be autoescaped (Jinja2).
- Never upload, export, or collect user files outside the designated export folder.
- If the user requests anonymization, anonymize names, phone numbers, and media.
- Prioritize environment variables for sensitive paths and tokens.
- Document all public functions (Google style).
- Show process progress in CLI using Rich.
- Use only approved open-source dependencies.

---

## 🔒 Security & Privacy

- Never send data to external services without explicit consent.
- Automatically redact sensitive data in export if requested.
- Protect copied media and clean up temporary files upon completion.

---

## 📝 Example Tasks for the Agent

- "Fix the parser to support iOS 2024 chatstorage.sqlite."
- "Add --export-pdf option to the CLI."
- "Improve the HTML template to display stickers and emojis correctly."
- "Refactor the Message model to normalize dates as ISO 8601."
- "Implement Telegram notifications upon process completion."
- "Speed up media export using asyncio."

---

## ⚠️ Limits

- Never modify files outside the working directory.
- Do not install proprietary libraries or use commercial services.
- Do not send dangerous or destructive shell commands.
- Do not alter network settings or expose user data.

---

## 📖 Available Resources

- Project structure, AGENTS.md template, test fixtures, and sample environment variables.

---

## 🟢 Success Criteria

The agent must deliver clean, safe, and well-tested code that fulfills the goal of exporting and navigating WhatsApp information in a simple and private way, strictly following all the rules above.
```
>>>>>>> 0b087d242fb332e1e94c87caa74b2b5dc3ef79a0
