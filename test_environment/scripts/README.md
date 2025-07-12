# Secure WhatsApp Chat Content Analyzer

A secure and simplified tool for analyzing WhatsApp chat exports for content patterns.

## 🔒 Security Features

- **Path validation**: Prevents directory traversal attacks
- **File size limits**: Maximum 50MB per file, 1000 files total
- **Extension filtering**: Only processes .html/.htm files
- **Input sanitization**: All inputs are validated and escaped
- **No external dependencies**: Only uses BeautifulSoup if available
- **Resource limits**: Memory and processing constraints
- **Safe output**: Controlled output directory creation

## 🚀 Usage

### Basic Usage
```bash
# Analyze with default keywords
python3 secure_content_analyzer.py /path/to/chat/exports

# Use custom keywords
python3 secure_content_analyzer.py /path/to/exports --keywords "love,family,work,meeting"

# Use configuration file
python3 secure_content_analyzer.py /path/to/exports --config my_config.json

# Create sample configuration
python3 secure_content_analyzer.py --create-config
```

### Configuration File
```json
{
  "keywords": [
    "meeting", "call", "video", "photo", "document",
    "happy", "sad", "excited", "love", "work",
    "family", "friend", "party", "travel", "food"
  ],
  "description": "Sample secure configuration for content analysis"
}
```

## 📊 Output

The analyzer creates:
- **JSON report**: Detailed analysis data
- **Text summary**: Human-readable summary
- **Secure output directory**: Results saved safely

### Example Output
```
==================================================
🔍 SECURE ANALYSIS COMPLETE
==================================================
📁 Files analyzed: 15
📊 Total messages: 12,450
📝 Total words: 89,230
💾 Total size: 2.3 MB
🎯 Files with matches: 8

🔍 Top keywords found:
  • family: 156
  • work: 89
  • meeting: 67
  • love: 45
  • photo: 34
```

## 🛡️ Security Improvements Over Original

| Feature | Original | Secure Version |
|---------|----------|----------------|
| Path validation | ❌ None | ✅ Comprehensive |
| File size limits | ❌ None | ✅ 50MB max |
| Extension filtering | ❌ None | ✅ HTML only |
| Resource limits | ❌ None | ✅ Multiple limits |
| Dependencies | ❌ 10+ optional | ✅ 1 optional |
| Code complexity | ❌ 1,615 lines | ✅ 400 lines |
| Parallel processing | ❌ Unsafe | ✅ Sequential only |
| File operations | ❌ Dangerous | ✅ Validated |

## 🔧 Technical Details

### Security Constraints
- Maximum file size: 50MB
- Maximum files processed: 1,000
- Maximum keywords: 100
- Maximum path length: 260 characters
- Allowed extensions: .html, .htm only
- Blocked path patterns: `..`, `~`, `$`, `|`, `;`, `&`, `` ` ``

### Dependencies
- **Required**: Python 3.6+
- **Optional**: BeautifulSoup4 (for better HTML parsing)
- **Fallback**: Regex-based text extraction if BeautifulSoup unavailable

### Error Handling
- Comprehensive input validation
- Graceful degradation on errors
- Detailed error logging
- Safe failure modes

## 📝 License

Same license as the main WhatsApp Chat Exporter project.

## 🤝 Contributing

This analyzer prioritizes security and simplicity. When contributing:
1. Maintain security-first approach
2. Keep code simple and readable
3. Add comprehensive input validation
4. Test with malicious inputs
5. Document security considerations