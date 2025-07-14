# WhatsApp Chat Cleaner

Advanced tool for cleaning, filtering, and processing WhatsApp chat exports with privacy and analysis features.

## Quick Start

### Basic Usage
```bash
# Clean a chat file (removes duplicates by default)
python chat_cleaner.py input.html

# Clean with anonymization and system message removal
python chat_cleaner.py input.html --anonymize-names --anonymize-phones --remove-system

# Process entire directory
python chat_cleaner.py /path/to/chats --directory --output /path/to/cleaned
```

### Privacy Protection
```bash
# Full anonymization
python chat_cleaner.py chat.html --anonymize-names --anonymize-phones --anonymize-emails

# Clean for sharing (remove personal info + system messages)
python chat_cleaner.py chat.html --anonymize-names --anonymize-phones --remove-system --output-format json
```

### Data Analysis
```bash
# Filter by date range
python chat_cleaner.py chat.html --start-date 2024-01-01 --end-date 2024-03-31 --stats

# Aggressive duplicate removal for analysis
python chat_cleaner.py chat.html --duplicate-threshold 10 --remove-system --stats
```

## Key Features

- ✅ **Smart Duplicate Detection** - Configurable similarity matching
- ✅ **Privacy Protection** - Anonymize names, phones, emails
- ✅ **System Message Cleanup** - Remove WhatsApp notifications
- ✅ **Date Filtering** - Extract specific time periods
- ✅ **Multiple Formats** - HTML, JSON, TXT output
- ✅ **Batch Processing** - Handle multiple files
- ✅ **Safe Operation** - Automatic backups
- ✅ **Detailed Statistics** - Processing reports

## Requirements

```bash
pip install beautifulsoup4  # For HTML parsing
pip install psutil         # For memory monitoring (optional)
```

## Main Options

| Option | Description |
|--------|-------------|
| `--anonymize-names` | Replace person names with placeholders |
| `--anonymize-phones` | Replace phone numbers with fake ones |
| `--anonymize-emails` | Replace email addresses |
| `--remove-system` | Remove WhatsApp system messages |
| `--duplicate-threshold SEC` | Duplicate detection window (default: 60s) |
| `--start-date DATE` | Filter from date (YYYY-MM-DD) |
| `--end-date DATE` | Filter to date (YYYY-MM-DD) |
| `--output-format FORMAT` | Output: html, json, txt |
| `--directory` | Process entire directory |
| `--stats` | Show detailed statistics |
| `--verbose` | Enable detailed logging |

## Examples

### Privacy Cleaning
```bash
# Prepare chat for sharing
python chat_cleaner.py personal_chat.html \
  --anonymize-names \
  --anonymize-phones \
  --remove-system \
  --output-format json \
  --output sanitized_chat.json
```

### Research Data Preparation
```bash
# Clean dataset for analysis
python chat_cleaner.py research_data/ \
  --directory \
  --duplicate-threshold 30 \
  --remove-system \
  --start-date 2024-01-01 \
  --stats
```

### Format Conversion
```bash
# Convert HTML to clean JSON
python chat_cleaner.py export.html \
  --output-format json \
  --remove-system \
  --output clean_export.json
```

## Output

The cleaner creates:
- **Backup file**: `original_backup.html` (if enabled)
- **Cleaned file**: `cleaned_original.html` or specified output
- **Statistics**: Processing summary and metrics

## Integration

### From Main Exporter
```bash
# Basic cleaning during export
wtsexporter export data/ --output cleaned/
wtsexporter clean cleaned/export.html --anonymize-names

# Or use Typer interface
wtsexporter clean input.html --remove-system --anonymize-names
```

### Python API
```python
from chat_cleaner import ChatCleaner, CleaningConfig

config = CleaningConfig(
    anonymize_names=True,
    remove_system_messages=True,
    duplicate_threshold_seconds=30
)

cleaner = ChatCleaner(config)
success = cleaner.clean_file("input.html", "output.html")
stats = cleaner.get_stats()
```

## Performance

- **Small files** (< 1MB): Instant processing
- **Medium files** (10MB): 2-5 seconds
- **Large files** (100MB+): 30 seconds - 2 minutes
- **Memory usage**: Configurable, typically 100-500MB

## Troubleshooting

1. **Import errors**: Install `beautifulsoup4`
2. **Memory issues**: Reduce `--batch-size` or `--max-memory`
3. **No messages found**: Check file format with `--verbose`
4. **Permission errors**: Check file permissions and output directory

For detailed documentation see: `docs/CHAT_CLEANER.md`
