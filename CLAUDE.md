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

# Run pre-commit hooks
pre-commit run --all-files

# Install pre-commit hooks
pre-commit install
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

### Chat Cleaning and Processing
```bash
# Basic chat cleaning (remove duplicates, system messages)
wtsexporter clean input.html --remove-system --anonymize-names

# Advanced cleaning with date filtering
wtsexporter clean input.html --start-date 2024-01-01 --end-date 2024-12-31 --anonymize-phones

# Standalone chat cleaner with full features
python -m Whatsapp_Chat_Exporter.chat_cleaner input.html --stats --verbose

# Process entire directory of chat exports
python -m Whatsapp_Chat_Exporter.chat_cleaner /path/to/chats --directory --anonymize-names

# Convert formats with cleaning
python -m Whatsapp_Chat_Exporter.chat_cleaner input.html --output-format json --remove-system
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

**Performance & Optimization:**
- `optimized_handlers.py`: Performance-enhanced platform handlers with database optimizations
- `database_optimizer.py`: Database connection pooling and schema optimization
- `query_optimizer.py`: N+1 query elimination and caching strategies

**Security & Utilities:**
- `security_utils.py`: Path traversal protection and secure file operations
- `utility.py`: Common functions for file handling, templating, and data processing
- `normalizer.py`: Message text normalization
- `vcards_contacts.py`: vCard contact enrichment
- `chat_cleaner.py`: Advanced chat cleaning and processing with privacy features

**Logging & Monitoring:**
- `logging_config.py`: Structured logging with JSON formatting and security event tracking

### Data Flow

1. **Input Processing**: Platform detection and file validation
2. **Decryption**: Handle encrypted Android backups (Crypt12/14/15)
3. **Database Reading**: SQLite database parsing for messages and contacts
4. **Media Extraction**: Copy/move media files, especially for iOS backups
5. **Data Transformation**: Convert to internal data model (`ChatCollection`)
6. **Chat Cleaning** (Optional): Apply advanced cleaning, filtering, and anonymization
7. **Output Generation**: Create HTML, JSON, or text outputs

### Key Architecture Patterns

- **MutableMapping Pattern**: `ChatCollection` implements dict-like interface for seamless chat management
- **Handler Pattern**: Separate handlers for Android/iOS/exported chats with common interface
- **Dual CLI Design**: Modern Typer CLI (`cli.py`) forwards to comprehensive argparse system (`__main__.py`)
- **Template System**: Jinja2 templates for HTML generation with offline support
- **Streaming Support**: Memory-efficient JSON streaming for large datasets
- **Plugin Architecture**: Optional dependencies for different encryption/contact formats
- **Performance Optimization**: Layered optimization with connection pooling, query optimization, and caching
- **Security by Design**: Comprehensive input validation and secure file operations throughout

### Development Patterns & Conventions

**File Structure:**
- All main processing modules are in `Whatsapp_Chat_Exporter/`
- Test files are prefixed with `test_` and co-located with source
- HTML templates: `whatsapp.html` (classic), `whatsapp_new.html` (modern theme)
- Media handling preserves original directory structure
- Output uses sanitized filenames for cross-platform compatibility

**Error Handling:**
- Comprehensive exception handling with user-friendly messages
- Security-focused validation for all user inputs and file paths
- Graceful degradation when optional features are unavailable

**Testing Strategy:**
- Co-located test files alongside source code for maintainability
- Comprehensive coverage including CLI, handlers, utilities, and security components
- Performance testing for optimization modules

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

## Chat Cleaning Features

The integrated chat cleaner (`chat_cleaner.py`) provides advanced post-processing capabilities:

### Core Features
- **Duplicate Detection**: Smart removal of duplicate messages with configurable similarity thresholds
- **Date Filtering**: Filter messages by date ranges for temporal analysis
- **System Message Removal**: Clean removal of WhatsApp system notifications and group events
- **Privacy Protection**: Comprehensive anonymization of names, phone numbers, and email addresses
- **Media Validation**: Clean and validate media file references
- **Format Conversion**: Convert between HTML, JSON, and TXT formats
- **Batch Processing**: Process multiple chat files efficiently
- **Statistics & Reporting**: Detailed analysis and processing metrics

### Usage Patterns
- **Post-Export Cleaning**: Apply after main export for refined analysis
- **Privacy Preparation**: Anonymize sensitive data before sharing or analysis
- **Data Analysis**: Clean datasets for research or statistical analysis
- **Format Conversion**: Convert exports between different formats
- **Archive Maintenance**: Clean up chat archives for long-term storage

### Integration Points
- **CLI Integration**: Available through `wtsexporter clean` command
- **Standalone Usage**: Direct module execution with full feature set
- **Python API**: Programmatic access for custom workflows
- **Batch Operations**: Directory-level processing for bulk operations

See `docs/CHAT_CLEANER.md` for comprehensive documentation and examples.
