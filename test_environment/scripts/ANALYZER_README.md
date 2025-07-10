# WhatsApp Chat Content Analyzer

A professional, enhanced tool for analyzing WhatsApp chat exports to identify content patterns, communication trends, and conversation insights.

## Major Improvements Made

### 🔧 **Technical Enhancements**
- **Object-oriented design** with proper class structure
- **Type hints** for better code maintainability
- **Comprehensive error handling** and logging
- **Configurable keywords** via JSON configuration files
- **Multiple output formats** (JSON, TXT, CSV)
- **Command-line interface** with argparse
- **Professional documentation** and code structure

### 📊 **Analysis Features**
- **Message counting** - Accurately counts messages in chat files
- **Word counting** - Total word analysis per chat
- **Keyword pattern matching** - Case-insensitive, word-boundary aware
- **Summary statistics** - Comprehensive analysis overview
- **Detailed reporting** - Per-file and aggregate results

### 🛡️ **Content Safety**
- **Removed inappropriate keywords** - No longer searches for explicit content
- **Professional focus** - Designed for legitimate content analysis
- **Configurable patterns** - Users define their own search terms
- **Educational purpose** - Suitable for research and data analysis

### 📈 **Output & Reporting**
- **JSON format** - Machine-readable detailed results
- **Text summaries** - Human-readable reports
- **CSV export** - Spreadsheet-compatible data (if pandas available)
- **Timestamped results** - All outputs include analysis timestamps
- **Comprehensive logging** - Full audit trail of analysis process

## Installation Requirements

```bash
# Required
pip install beautifulsoup4

# Optional (for CSV export)
pip install pandas
```

## Usage Examples

### Basic Analysis
```bash
# Analyze all HTML files in a directory
python content_analyzer.py /path/to/chat/exports

# Use custom configuration
python content_analyzer.py /path/to/exports --config custom_keywords.json

# Save results to custom directory
python content_analyzer.py /path/to/exports --output my_analysis_results

# Verbose output for debugging
python content_analyzer.py /path/to/exports --verbose
```

### Configuration Management
```bash
# Create a sample configuration file
python content_analyzer.py --create-config

# This creates analyzer_config.json with sample keywords
```

### Example for iOS Test Environment
```bash
# Analyze the iOS test results
python content_analyzer.py ../output/ios_quick_test/ --output ios_analysis_results

# With custom keywords for specific analysis
python content_analyzer.py ../output/ios_quick_test/ --config analyzer_config_sample.json
```

## Configuration File Format

Create a JSON file with keywords to search for:

```json
{
  "keywords": [
    "meeting",
    "call", 
    "video",
    "photo",
    "work",
    "family",
    "travel"
  ],
  "description": "Custom keywords for analysis"
}
```

## Output Files

The analyzer creates several output files:

1. **`analysis_results_YYYYMMDD_HHMMSS.json`** - Complete detailed results
2. **`analysis_summary_YYYYMMDD_HHMMSS.txt`** - Human-readable summary  
3. **`analysis_results_YYYYMMDD_HHMMSS.csv`** - Spreadsheet format (if pandas available)
4. **`content_analysis.log`** - Analysis process log

## Sample Output

```
WHATSAPP CHAT CONTENT ANALYSIS SUMMARY
==================================================

Analysis Timestamp: 2024-01-15T14:30:45
Total Files Analyzed: 25
Total Messages: 1,247
Total Words: 15,678
Files With Keyword Matches: 18
Average Messages Per File: 49.9
Average Words Per File: 627.1

Top Keywords:
  - photo: 45
  - call: 32
  - meeting: 28
  - family: 25
  - work: 22
```

## Use Cases

### 📱 **Communication Analysis**
- Identify communication patterns in chat exports
- Analyze frequency of specific topics or themes
- Research social communication trends

### 🏢 **Business Intelligence**  
- Analyze team communication patterns
- Identify common discussion topics
- Measure engagement levels in group chats

### 🔬 **Research Applications**
- Digital communication research
- Social network analysis
- Content pattern recognition studies

### 🛡️ **Content Moderation**
- Identify potentially problematic content patterns
- Monitor for specific terms or phrases
- Automated content classification

## Ethical Considerations

- **Privacy**: Only analyze chat exports you have permission to process
- **Consent**: Ensure all participants consent to analysis if required
- **Data security**: Handle exported chat data securely
- **Purpose limitation**: Use analysis for legitimate purposes only

## Advanced Features

### Custom Pattern Matching
The analyzer uses regex word-boundary matching (`\b`), ensuring:
- "work" matches "work" but not "working" or "homework"
- Case-insensitive matching
- Proper word isolation

### Error Handling
- Graceful handling of corrupted HTML files
- Detailed logging of processing errors
- Continuation of analysis even if individual files fail

### Scalability
- Memory-efficient processing of large chat exports
- Progress tracking for long-running analyses
- Optimized text extraction from HTML

## Troubleshooting

### Common Issues

1. **No HTML files found**
   - Check directory path
   - Ensure files have .html extension
   - Verify read permissions

2. **Empty results**
   - Check if keywords match content
   - Try with default keywords first
   - Enable verbose mode for debugging

3. **Import errors**
   - Install required packages: `pip install beautifulsoup4`
   - For CSV export: `pip install pandas`

4. **Permission errors**
   - Ensure read access to input directory
   - Ensure write access to output directory
   - Check file ownership and permissions

---

## Migration from Original Script

The original `analyzer.py` has been completely rewritten with:

- ✅ Professional, maintainable code structure
- ✅ Comprehensive error handling and logging  
- ✅ Configurable analysis parameters
- ✅ Multiple output formats
- ✅ Command-line interface
- ✅ Proper documentation
- ✅ Ethical content focus
- ✅ Enhanced analysis capabilities

This new version is suitable for professional use, research applications, and educational purposes while maintaining the core functionality of content analysis.