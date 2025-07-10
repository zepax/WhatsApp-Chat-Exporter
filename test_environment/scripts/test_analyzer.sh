#!/bin/bash

# Test script for the WhatsApp Chat Content Analyzer
# This script demonstrates various usage scenarios

echo "🚀 WhatsApp Chat Content Analyzer - Test Script"
echo "================================================"

# Check if we're in the right directory
if [ ! -f "content_analyzer.py" ]; then
    echo "❌ Error: content_analyzer.py not found in current directory"
    echo "   Please run this script from the scripts directory"
    exit 1
fi

# Create sample configuration if it doesn't exist
if [ ! -f "analyzer_config_sample.json" ]; then
    echo "📝 Creating sample configuration..."
    python content_analyzer.py --create-config
fi

# Check if we have any HTML files to analyze
HTML_DIR="../output/ios_quick_test"
if [ ! -d "$HTML_DIR" ]; then
    echo "📁 Test directory not found: $HTML_DIR"
    echo "   Creating a sample test with the iOS data..."
    
    # Try to run a quick iOS test first
    cd ..
    echo "   Running: python -m Whatsapp_Chat_Exporter -i -d ios/backup/ChatStorage.sqlite -o output/ios_quick_test/ -v"
    python -m Whatsapp_Chat_Exporter -i -d ios/backup/ChatStorage.sqlite -o output/ios_quick_test/ -v
    cd scripts
fi

# Test 1: Basic analysis
echo "📊 Test 1: Basic content analysis"
echo "================================="
python content_analyzer.py "$HTML_DIR" --output test_results_basic

# Test 2: Analysis with custom config
echo ""
echo "📊 Test 2: Analysis with custom configuration"
echo "============================================="
python content_analyzer.py "$HTML_DIR" --config analyzer_config_sample.json --output test_results_custom

# Test 3: Verbose analysis
echo ""
echo "📊 Test 3: Verbose analysis with detailed logging"
echo "================================================="
python content_analyzer.py "$HTML_DIR" --verbose --output test_results_verbose

# Test 4: Create and test with minimal config
echo ""
echo "📊 Test 4: Creating and testing minimal configuration"
echo "===================================================="

# Create a minimal test config
cat > test_minimal_config.json << EOF
{
  "keywords": [
    "test",
    "message",
    "chat",
    "hello",
    "thanks"
  ],
  "description": "Minimal test configuration"
}
EOF

python content_analyzer.py "$HTML_DIR" --config test_minimal_config.json --output test_results_minimal

# Show results summary
echo ""
echo "✅ Analysis Tests Complete!"
echo "=========================="
echo ""
echo "📂 Generated output directories:"
ls -la test_results_* 2>/dev/null | grep "^d" || echo "   (No test result directories found)"

echo ""
echo "📄 Generated files in test_results_basic:"
ls -la test_results_basic/ 2>/dev/null || echo "   (Directory not found)"

echo ""
echo "📊 Quick summary from latest analysis:"
if [ -f "test_results_basic/analysis_summary_"*.txt ]; then
    LATEST_SUMMARY=$(ls -t test_results_basic/analysis_summary_*.txt 2>/dev/null | head -1)
    if [ -n "$LATEST_SUMMARY" ]; then
        echo "   From: $(basename "$LATEST_SUMMARY")"
        head -15 "$LATEST_SUMMARY" | grep -E "(Total Files|Total Messages|Total Words|Files With)"
    fi
fi

echo ""
echo "🎯 Usage Examples:"
echo "=================="
echo "# Analyze specific directory:"
echo "python content_analyzer.py /path/to/html/files"
echo ""
echo "# Use custom keywords:"
echo "python content_analyzer.py /path/to/html/files --config my_keywords.json"
echo ""
echo "# Create new configuration:"
echo "python content_analyzer.py --create-config"
echo ""
echo "# Detailed help:"
echo "python content_analyzer.py --help"

# Cleanup test config
rm -f test_minimal_config.json

echo ""
echo "✨ Test completed successfully!"