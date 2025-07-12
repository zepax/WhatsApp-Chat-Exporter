# WhatsApp Chat Content Analyzers

Advanced tools for analyzing WhatsApp chat exports with different capabilities and security levels.

## 📋 Available Analyzers

### 🔒 Secure Content Analyzer (`secure_content_analyzer.py`)
**Focus**: Security and simplicity
- **File limits**: 50MB per file, 1,000 files max
- **Text analysis**: 1MB per file  
- **Security**: Comprehensive validation and constraints
- **Best for**: Small to medium datasets where security is priority

### 🚀 Advanced Content Analyzer (`advanced_content_analyzer.py`)
**Focus**: Performance and large datasets
- **File limits**: 1GB per file, 50,000 files max
- **Text analysis**: 100MB per file with streaming
- **Features**: Custom regex, parallel processing, advanced patterns
- **Best for**: Large datasets requiring extensive analysis

## 🔒 Security Features (Both Analyzers)

- **Path validation**: Prevents directory traversal attacks
- **File size limits**: Configurable per analyzer
- **Extension filtering**: Multiple formats supported
- **Input sanitization**: All inputs validated and escaped
- **Resource monitoring**: Memory and processing constraints
- **Safe output**: Controlled output directory creation

## 🚀 Usage

### Secure Analyzer (Basic Usage)
```bash
# Analyze with default keywords
python3 secure_content_analyzer.py /path/to/chat/exports

# Use custom keywords
python3 secure_content_analyzer.py /path/to/exports --keywords "love,family,work,meeting"

# Use configuration file
python3 secure_content_analyzer.py /path/to/exports --config secure_config.json

# Create sample configuration
python3 secure_content_analyzer.py --create-config
```

### Advanced Analyzer (Enhanced Usage)
```bash
# Basic analysis with advanced features
python3 advanced_content_analyzer.py /path/to/chat/exports

# Advanced configuration
python3 advanced_content_analyzer.py /path/to/exports --config advanced_analyzer_config.json

# Custom settings for large datasets (auto-detects optimal workers)
python3 advanced_content_analyzer.py /path/to/exports \
    --max-files 50000 \
    --max-file-size 1000 \
    --keywords "meeting,work,family,urgent"

# Manual worker override (disables auto-detection)
python3 advanced_content_analyzer.py /path/to/exports \
    --parallel-workers 8 \
    --disable-auto-workers

# With custom regex patterns
python3 advanced_content_analyzer.py /path/to/exports \
    --regex-patterns '{"phones": "\\+?[\\d\\s\\-\\(\\)]{10,}", "emails": "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b"}'

# Create advanced configuration
python3 advanced_content_analyzer.py --create-config

# Run with graceful interrupt handling (press Ctrl+C to stop safely)
python3 advanced_content_analyzer.py /path/to/exports --keywords "familia,trabajo,amor"
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

## 🆚 Analyzer Comparison

| Feature | Original (Vulnerable) | Secure Version | Advanced Version |
|---------|----------------------|----------------|------------------|
| **Security** |
| Path validation | ❌ None | ✅ Comprehensive | ✅ Enhanced |
| File size limits | ❌ None | ✅ 50MB max | ✅ 1GB max |
| Extension filtering | ❌ None | ✅ HTML only | ✅ Multiple formats |
| Resource limits | ❌ None | ✅ Basic limits | ✅ Advanced monitoring |
| **Performance** |
| Max files | ❌ Unlimited | ✅ 1,000 | ✅ 50,000 |
| Text analysis | ❌ Unlimited | ✅ 1MB per file | ✅ 100MB per file |
| Parallel processing | ❌ Unsafe | ❌ Sequential only | ✅ Safe parallel |
| Streaming | ❌ None | ❌ None | ✅ Large file streaming |
| **Features** |
| Basic keywords | ✅ Yes | ✅ Yes | ✅ Yes |
| Custom regex | ❌ Limited | ❌ None | ✅ Advanced patterns |
| Predefined patterns | ❌ None | ❌ None | ✅ 50+ patterns |
| Word frequency | ❌ Basic | ❌ None | ✅ Advanced |
| Statistics | ❌ Basic | ✅ Basic | ✅ Comprehensive |
| **Code Quality** |
| Lines of code | ❌ 1,615 | ✅ 400 | ✅ 1,200 |
| Dependencies | ❌ 10+ optional | ✅ 1 optional | ✅ 2 optional |
| Error handling | ❌ Poor | ✅ Good | ✅ Excellent |

## 🔍 Advanced Analyzer Features

### 📊 Enhanced Patterns
- **50+ Predefined Patterns**: Phone numbers, emails, URLs, dates, times, money amounts
- **Custom Regex Support**: Add your own patterns with validation
- **Pattern Categories**: Communication, WhatsApp-specific, content analysis
- **Pattern Validation**: Security checks for regex safety

### 🚀 Performance Optimizations
- **Auto Hardware Detection**: Automatically detects CPU cores, memory, and GPU
- **Smart Worker Scaling**: Optimizes parallel workers based on system specs
- **Streaming Analysis**: Process files larger than memory
- **Intelligent Batching**: Adjusts batch sizes based on workload
- **Memory Monitoring**: Automatic memory usage tracking
- **GPU Detection**: Identifies available NVIDIA/AMD/Intel GPUs for future acceleration

### 📈 Advanced Statistics
- **Word Frequency Analysis**: Top words across all chats
- **Pattern Distribution**: Where patterns appear most
- **Unique Match Tracking**: Deduplicated pattern matches
- **Processing Metrics**: Performance and resource usage
- **Comprehensive Reporting**: JSON and text outputs

### ⚙️ Configuration Options
```json
{
  "advanced_config": {
    "max_files": 50000,
    "max_file_size_mb": 1000,
    "max_text_analysis_mb": 100,
    "parallel_workers": 8,
    "enable_streaming": true,
    "enable_custom_regex": true,
    "save_match_examples": true,
    "generate_statistics": true
  }
}
```

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
- **Optional**: tqdm (for visual progress bars with ETA estimates)
- **Fallback**: Regex-based text extraction if BeautifulSoup unavailable
- **Fallback**: Simple console output if tqdm unavailable

#### Installing Optional Dependencies
```bash
# For enhanced HTML parsing
pip install beautifulsoup4

# For visual progress bars (recommended)
pip install tqdm

# Install all optional dependencies
pip install beautifulsoup4 tqdm
```

### Error Handling & Interruptions
- **Comprehensive input validation**: All inputs validated and escaped
- **Graceful degradation**: Continues analysis even with individual file errors
- **Detailed error logging**: Full error tracking and reporting
- **Safe failure modes**: No data corruption on errors
- **Graceful interruption**: Press Ctrl+C to safely stop and save partial results
- **Automatic cleanup**: Progress tracking closed and temporary files cleaned
- **Partial result saving**: Analysis results preserved on interruption

## 📝 License

Same license as the main WhatsApp Chat Exporter project.

## 🤝 Contributing

This analyzer prioritizes security and simplicity. When contributing:
1. Maintain security-first approach
2. Keep code simple and readable
3. Add comprehensive input validation
4. Test with malicious inputs
5. Document security considerations