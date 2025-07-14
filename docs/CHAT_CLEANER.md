# WhatsApp Chat Cleaner Documentation

The WhatsApp Chat Cleaner is a comprehensive tool for cleaning, filtering, and preprocessing WhatsApp chat exports with advanced features for privacy, security, and data analysis.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI Usage](#cli-usage)
- [Python API](#python-api)
- [Configuration](#configuration)
- [Output Formats](#output-formats)
- [Examples](#examples)
- [Advanced Features](#advanced-features)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)

## Overview

The Chat Cleaner provides sophisticated processing capabilities for WhatsApp chat exports, including:

- **Duplicate removal** with configurable similarity detection
- **Date filtering** for time-range analysis
- **System message cleanup** to remove notifications
- **Privacy protection** through anonymization
- **Media reference validation** and cleanup
- **Multiple output formats** (HTML, JSON, TXT)
- **Batch processing** for multiple files
- **Comprehensive statistics** and reporting

## Features

### 🔄 **Duplicate Detection & Removal**
- Smart duplicate detection based on content similarity and timing
- Configurable time threshold (default: 60 seconds)
- Handles exact duplicates and near-duplicates
- Preserves message order and context

### 📅 **Date Filtering**
- Filter messages by date ranges
- Support for multiple date formats
- Inclusive date filtering (start and end dates included)
- Timezone-aware processing

### 🤖 **System Message Removal**
- Remove WhatsApp system notifications
- Configurable patterns for different message types
- Includes: join/leave notifications, group changes, security messages
- Preserves important conversation flow

### 🎭 **Anonymization & Privacy**
- **Name anonymization**: Replace person names with consistent placeholders
- **Phone number anonymization**: Replace with formatted placeholders
- **Email anonymization**: Replace while preserving domain structure
- **Structure preservation**: Maintain message format and readability
- **Consistent mapping**: Same person always gets same anonymous name

### 📱 **Media Reference Cleanup**
- Validate media file references
- Clean broken or missing media links
- Optional media path validation
- Replace missing media with clean placeholders

### 📊 **Processing & Analysis**
- **Comprehensive statistics**: Messages processed, removed, anonymized
- **Performance metrics**: Processing time, memory usage
- **Error reporting**: Detailed error logs and warnings
- **Progress tracking**: Real-time processing updates

### 🛡️ **Safety & Backup**
- **Automatic backups**: Create backups before processing
- **Non-destructive processing**: Original files preserved
- **Error recovery**: Graceful handling of parsing errors
- **Validation**: Input validation and sanitization

## Installation

### Prerequisites

```bash
# Required dependencies
pip install beautifulsoup4  # For HTML parsing
pip install psutil         # For memory monitoring (optional)
```

### From Main Codebase

The chat cleaner is included in the main WhatsApp Chat Exporter package:

```bash
# Using the main CLI
wtsexporter clean input.html --anonymize-names --remove-system

# Direct Python usage
python -m Whatsapp_Chat_Exporter.chat_cleaner input.html --stats
```

## Quick Start

### Basic Cleaning
```bash
# Clean a single file with default settings
python chat_cleaner.py input.html

# Clean with anonymization
python chat_cleaner.py input.html --anonymize-names --anonymize-phones

# Clean entire directory
python chat_cleaner.py /path/to/chats --directory
```

### Common Use Cases
```bash
# Remove system messages and duplicates
python chat_cleaner.py chat.html --remove-system --duplicate-threshold 30

# Privacy-focused cleaning
python chat_cleaner.py chat.html --anonymize-names --anonymize-phones --anonymize-emails

# Date-filtered analysis
python chat_cleaner.py chat.html --start-date 2024-01-01 --end-date 2024-12-31

# Convert to JSON with statistics
python chat_cleaner.py chat.html --output-format json --stats
```

## CLI Usage

### Basic Syntax
```bash
python chat_cleaner.py INPUT [OPTIONS]
```

### Input/Output Options
```bash
-o, --output OUTPUT          # Output file/directory (auto-generated if not specified)
-d, --directory             # Process entire directory
--output-format FORMAT     # Output format: html, json, txt
```

### Cleaning Options
```bash
--no-duplicates             # Disable duplicate removal
--duplicate-threshold SEC   # Duplicate detection threshold (default: 60)
--remove-system            # Remove system messages
--start-date DATE          # Start date filter (YYYY-MM-DD or MM/DD/YYYY)
--end-date DATE            # End date filter (YYYY-MM-DD or MM/DD/YYYY)
```

### Privacy Options
```bash
--anonymize-names          # Anonymize person names
--anonymize-phones         # Anonymize phone numbers
--anonymize-emails         # Anonymize email addresses
--preserve-structure       # Preserve name structure when anonymizing
```

### Media Options
```bash
--clean-media              # Clean broken media references
--media-path PATH          # Base path for media file validation
```

### Safety Options
```bash
--no-backup                # Don't create backup files
```

### Performance Options
```bash
--batch-size SIZE          # Processing batch size (default: 1000)
--max-memory MB            # Maximum memory usage (default: 512)
```

### Output Options
```bash
-v, --verbose              # Enable verbose output
-q, --quiet               # Suppress output except errors
--stats                   # Show detailed statistics
```

## Python API

### Basic Usage

```python
from Whatsapp_Chat_Exporter.chat_cleaner import ChatCleaner, CleaningConfig

# Create configuration
config = CleaningConfig(
    remove_duplicates=True,
    duplicate_threshold_seconds=60,
    remove_system_messages=True,
    anonymize_names=True,
    create_backup=True
)

# Initialize cleaner
cleaner = ChatCleaner(config)

# Clean a single file
success = cleaner.clean_file("input.html", "output.html")

# Clean a directory
success = cleaner.clean_directory("input_dir/", "output_dir/")

# Get statistics
stats = cleaner.get_stats()
print(f"Processed {stats.total_messages_before} messages")
print(f"Removed {stats.duplicates_removed} duplicates")
```

### Advanced Configuration

```python
from datetime import datetime

config = CleaningConfig(
    # Duplicate removal
    remove_duplicates=True,
    duplicate_threshold_seconds=30,

    # Date filtering
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),

    # System messages
    remove_system_messages=True,
    system_message_patterns=[
        r"joined using this group's invite link",
        r"left",
        r"changed the group name",
        # Add custom patterns
    ],

    # Anonymization
    anonymize_names=True,
    anonymize_phones=True,
    anonymize_emails=True,
    preserve_structure=True,

    # Media cleaning
    clean_broken_media=True,
    media_base_path="/path/to/media",

    # Output
    output_format="json",
    create_backup=True,

    # Performance
    batch_size=2000,
    max_memory_mb=1024
)
```

### Custom Processing

```python
# Process with custom logic
cleaner = ChatCleaner(config)

# Access raw messages after parsing
messages = cleaner._parse_html_chat("input.html")

# Apply specific cleaning operations
cleaned = cleaner._remove_duplicates(messages)
cleaned = cleaner._anonymize_content(cleaned)

# Save with custom format
success = cleaner._save_as_json(cleaned, "output.json")
```

## Configuration

### CleaningConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `remove_duplicates` | bool | True | Enable duplicate message removal |
| `duplicate_threshold_seconds` | int | 60 | Time window for duplicate detection |
| `start_date` | datetime | None | Filter start date (inclusive) |
| `end_date` | datetime | None | Filter end date (inclusive) |
| `remove_system_messages` | bool | False | Remove system notifications |
| `system_message_patterns` | List[str] | Default patterns | Regex patterns for system messages |
| `anonymize_names` | bool | False | Anonymize person names |
| `anonymize_phones` | bool | False | Anonymize phone numbers |
| `anonymize_emails` | bool | False | Anonymize email addresses |
| `preserve_structure` | bool | True | Preserve name structure when anonymizing |
| `clean_broken_media` | bool | False | Clean broken media references |
| `validate_media_paths` | bool | False | Validate media file existence |
| `media_base_path` | str | None | Base path for media file validation |
| `create_backup` | bool | True | Create backup before processing |
| `output_format` | str | "html" | Output format (html/json/txt) |
| `preserve_timestamps` | bool | True | Preserve original timestamps |
| `batch_size` | int | 1000 | Processing batch size |
| `max_memory_mb` | int | 512 | Maximum memory usage |

### System Message Patterns

Default patterns for system message detection:

```python
default_patterns = [
    r"joined using this group's invite link",
    r"left",
    r"changed the group name",
    r"changed this group's icon",
    r"added",
    r"removed",
    r"You created group",
    r"Messages and calls are end-to-end encrypted",
    r"changed their phone number",
    r"security code changed"
]
```

### Date Format Support

Supported input date formats:
- `YYYY-MM-DD` (ISO format)
- `MM/DD/YYYY` (US format)
- `DD/MM/YYYY` (European format)
- `YYYY-MM-DD HH:MM:SS` (with time)
- `MM/DD/YYYY HH:MM:SS` (US with time)
- `DD/MM/YYYY HH:MM:SS` (European with time)

## Output Formats

### HTML Output
- Clean, readable format with CSS styling
- Embedded statistics summary
- Message categorization (text/media/system)
- Timestamp preservation
- Responsive design

### JSON Output
```json
{
  "metadata": {
    "total_messages": 1500,
    "export_time": "2024-01-15T10:30:00",
    "cleaning_stats": {
      "duplicates_removed": 45,
      "system_messages_removed": 12,
      "anonymized_items": 67
    }
  },
  "messages": [
    {
      "timestamp": "2024-01-01T09:00:00",
      "sender": "Person1",
      "content": "Hello everyone!",
      "type": "text",
      "media_path": null
    }
  ]
}
```

### Text Output
- Clean plain text format
- Standard WhatsApp timestamp format
- Compatible with re-import
- Lightweight and portable

## Examples

### 1. Basic Chat Cleaning

```bash
# Clean a WhatsApp HTML export
python chat_cleaner.py whatsapp_chat.html

# Result: whatsapp_chat_backup.html (backup) + cleaned_whatsapp_chat.html
```

### 2. Privacy-Focused Processing

```bash
# Full anonymization with system message removal
python chat_cleaner.py personal_chat.html \
  --anonymize-names \
  --anonymize-phones \
  --anonymize-emails \
  --remove-system \
  --output-format json
```

### 3. Date-Range Analysis

```bash
# Analyze messages from specific period
python chat_cleaner.py group_chat.html \
  --start-date 2024-01-01 \
  --end-date 2024-03-31 \
  --remove-system \
  --stats
```

### 4. Bulk Processing

```bash
# Process entire directory of chat exports
python chat_cleaner.py /exports/whatsapp_chats/ \
  --directory \
  --output /cleaned_exports/ \
  --anonymize-names \
  --duplicate-threshold 30 \
  --verbose
```

### 5. Advanced Configuration

```bash
# Custom processing with multiple options
python chat_cleaner.py large_group.html \
  --duplicate-threshold 10 \
  --remove-system \
  --anonymize-names \
  --clean-media \
  --media-path /media/whatsapp/ \
  --output-format json \
  --batch-size 2000 \
  --max-memory 1024 \
  --stats
```

## Advanced Features

### Custom System Message Patterns

```python
# Add custom patterns for specific use cases
config = CleaningConfig(
    remove_system_messages=True,
    system_message_patterns=[
        r"joined using this group's invite link",
        r"Missed voice call",
        r"Missed video call",
        r"This message was deleted",
        # Add your custom patterns
        r"Custom notification pattern",
    ]
)
```

### Batch Processing with Error Handling

```python
import logging
from pathlib import Path

# Setup detailed logging
logging.basicConfig(level=logging.DEBUG)

config = CleaningConfig(anonymize_names=True)
cleaner = ChatCleaner(config)

# Process multiple files with error tracking
chat_files = Path("exports/").glob("*.html")
results = {}

for chat_file in chat_files:
    try:
        success = cleaner.clean_file(str(chat_file))
        results[chat_file.name] = "success" if success else "failed"
    except Exception as e:
        results[chat_file.name] = f"error: {e}"

# Review results
stats = cleaner.get_stats()
print(f"Processed {stats.files_processed} files")
print("Results:", results)
```

### Memory-Efficient Large File Processing

```python
# Configure for large files
config = CleaningConfig(
    batch_size=5000,      # Larger batches
    max_memory_mb=2048,   # Allow more memory
    create_backup=False   # Skip backup for very large files
)

cleaner = ChatCleaner(config)

# Monitor memory usage
import psutil
process = psutil.Process()

print(f"Memory before: {process.memory_info().rss / 1024 / 1024:.1f} MB")
success = cleaner.clean_file("very_large_chat.html")
print(f"Memory after: {process.memory_info().rss / 1024 / 1024:.1f} MB")
```

## Performance

### Benchmarks

Typical performance on a modern system:

| File Size | Messages | Processing Time | Memory Usage |
|-----------|----------|----------------|--------------|
| 1 MB | 1,000 | < 1 second | 50 MB |
| 10 MB | 10,000 | 2-5 seconds | 100 MB |
| 100 MB | 100,000 | 15-30 seconds | 300 MB |
| 1 GB | 1,000,000 | 2-5 minutes | 1 GB |

### Optimization Tips

1. **Disable unnecessary features** for better performance:
   ```python
   config = CleaningConfig(
       remove_duplicates=True,    # Keep this for most value
       remove_system_messages=False,  # Disable if not needed
       anonymize_names=False,     # Skip if privacy not required
       create_backup=False        # Skip for temporary processing
   )
   ```

2. **Adjust batch size** for your system:
   ```python
   config = CleaningConfig(
       batch_size=10000,  # Larger for more RAM
       max_memory_mb=2048  # Set based on available RAM
   )
   ```

3. **Use appropriate output format**:
   - **JSON**: Fastest processing and smallest output
   - **TXT**: Good performance, very small files
   - **HTML**: Slower but best readability

### Memory Management

The cleaner includes automatic memory management:

- **Streaming processing**: Large files processed in chunks
- **Garbage collection**: Automatic cleanup of processed data
- **Memory monitoring**: Warnings when approaching limits
- **Batch processing**: Configurable batch sizes for efficiency

## Troubleshooting

### Common Issues

#### 1. **ImportError: BeautifulSoup4 required**
```bash
# Solution: Install required dependency
pip install beautifulsoup4
```

#### 2. **Memory errors with large files**
```bash
# Solution: Reduce batch size and enable streaming
python chat_cleaner.py large_file.html --batch-size 500 --max-memory 512
```

#### 3. **No messages found in file**
```bash
# Possible causes:
# - Unsupported HTML format
# - Corrupted file
# - Non-WhatsApp export format

# Solution: Check file format and try verbose mode
python chat_cleaner.py file.html --verbose
```

#### 4. **Date parsing errors**
```bash
# Solution: Use supported date formats
python chat_cleaner.py file.html --start-date "2024-01-01" --end-date "2024-12-31"
```

#### 5. **Permission denied errors**
```bash
# Solution: Check file permissions and output directory
chmod +r input_file.html
mkdir -p output_directory/
```

### Debug Mode

Enable detailed debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

config = CleaningConfig()
cleaner = ChatCleaner(config)
cleaner.clean_file("problematic_file.html")
```

### Error Logs

Check error logs in the statistics:

```python
stats = cleaner.get_stats()
if stats.errors:
    print("Errors encountered:")
    for error in stats.errors:
        print(f"  - {error}")

if stats.warnings:
    print("Warnings:")
    for warning in stats.warnings:
        print(f"  - {warning}")
```

### Validation

Validate your configuration before processing:

```python
def validate_config(config: CleaningConfig) -> bool:
    """Validate cleaning configuration."""
    if config.start_date and config.end_date:
        if config.start_date > config.end_date:
            print("Error: Start date must be before end date")
            return False

    if config.duplicate_threshold_seconds < 0:
        print("Error: Duplicate threshold must be positive")
        return False

    if config.max_memory_mb < 100:
        print("Warning: Very low memory limit may cause issues")

    return True

# Use before processing
if validate_config(config):
    cleaner = ChatCleaner(config)
```

## Support

For issues, questions, or contributions:

1. **Check this documentation** for common solutions
2. **Enable verbose mode** to get detailed error information
3. **Report issues** with sample files and error logs
4. **Contribute improvements** to the codebase

The chat cleaner is designed to be robust and handle various input formats, but WhatsApp export formats can vary. When reporting issues, please include:

- Input file format and size
- Command used or configuration
- Error messages and logs
- Expected vs actual behavior

---

*Last updated: December 2024*
