# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest Whatsapp_Chat_Exporter/test_cli.py

# Run tests with verbose output
pytest -v

# Run tests with coverage
pytest --cov=Whatsapp_Chat_Exporter
```

### Code Quality
```bash
# Format code with black
black .

# Lint code with ruff
ruff check .

# Fix linting issues automatically
ruff check --fix .

# Type checking with mypy
mypy Whatsapp_Chat_Exporter/
```

### Installation and Setup
```bash
# Install in development mode
pip install -e .

# Install with all optional dependencies
pip install -e .[all]

# Install with Poetry (preferred)
poetry install

# Install with specific extras
pip install -e .[android_backup,vcards,crypt15]
```

### Running the Exporter
```bash
# Basic Android export
wtsexporter -a

# Android with encryption key
wtsexporter -a -k key -b msgstore.db.crypt15

# iOS export
wtsexporter -i -b "/path/to/backup"

# Export with custom output directory
wtsexporter -a -o custom_output/

# Export as JSON only
wtsexporter -a -j result.json --no-html
```

## Architecture Overview

### Core Components

**Entry Points:**
- `cli.py`: Typer wrapper that forwards to argparse-based main
- `__main__.py`: Main entry point with comprehensive argument parsing and orchestration

**Data Models:**
- `data_model.py`: Core data structures
  - `ChatCollection`: Dictionary-like container for all chats
  - `ChatStore`: Individual chat with messages and metadata
  - `Message`: Individual message with timestamps, media, and formatting
  - `Timing`: Handles timezone-aware timestamp formatting

**Platform Handlers:**
- `android_handler.py`: Android database processing and HTML generation
- `ios_handler.py`: iOS database processing 
- `ios_media_handler.py`: iOS media extraction from backups
- `exported_handler.py`: Plain text exported chat processing

**Encryption Support:**
- `android_crypt.py`: Handles Crypt12/14/15 backup decryption
- `bplist.py`: Binary plist parsing for iOS

**Utilities:**
- `utility.py`: Common functions for file handling, templating, and data processing
- `normalizer.py`: Message text normalization
- `vcards_contacts.py`: vCard contact enrichment

### Data Flow

1. **Input Processing**: Platform detection and file validation
2. **Decryption**: Handle encrypted Android backups (Crypt12/14/15)
3. **Database Reading**: SQLite database parsing for messages and contacts
4. **Media Extraction**: Copy/move media files, especially for iOS backups
5. **Data Transformation**: Convert to internal data model (`ChatCollection`)
6. **Output Generation**: Create HTML, JSON, or text outputs

### Key Architecture Patterns

- **MutableMapping Pattern**: `ChatCollection` implements dict-like interface
- **Handler Pattern**: Separate handlers for Android/iOS with common interface
- **Template System**: Jinja2 templates for HTML generation with offline support
- **Streaming Support**: Memory-efficient JSON streaming for large datasets
- **Plugin Architecture**: Optional dependencies for different encryption/contact formats

### File Structure Conventions

- All main processing modules are in `Whatsapp_Chat_Exporter/`
- Test files are prefixed with `test_` and co-located with source
- HTML templates: `whatsapp.html` (classic), `whatsapp_new.html` (modern theme)
- Media handling preserves original directory structure
- Output uses sanitized filenames for cross-platform compatibility

### Platform-Specific Notes

**Android:**
- Uses `msgstore.db` for messages, `wa.db` for contacts
- Supports encrypted backups (Crypt12/14/15) with key files or hex keys
- Media folder structure: `WhatsApp/Media/`
- Profile photos: `WhatsApp/Media/WhatsApp Profile Photos/me.jpg`

**iOS:**
- Uses iTunes/Finder backup directory structure
- Message DB: `7c7fba66680ef796b916b067077cc246adacf01d`
- Contact DB: `ContactsV2.sqlite`
- Supports encrypted backups with `iphone_backup_decrypt`
- Media extraction from backup manifest

**Exported Chats:**
- Plain text format parsing with automatic participant detection
- Media file path resolution relative to chat file location
- Interactive prompts for participant identification