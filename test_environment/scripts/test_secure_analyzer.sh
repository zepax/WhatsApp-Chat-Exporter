#!/bin/bash

# Test script for the Secure WhatsApp Chat Content Analyzer
# This script demonstrates basic usage scenarios

echo "🔒 Secure WhatsApp Chat Content Analyzer - Test Script"
echo "====================================================="

# Check if we're in the right directory
if [ ! -f "secure_content_analyzer.py" ]; then
    echo "❌ Error: secure_content_analyzer.py not found in current directory"
    echo "   Please run this script from the scripts directory"
    exit 1
fi

# Test 1: Check if analyzer runs
echo
echo "🧪 Test 1: Check analyzer help"
echo "------------------------------"
python3 secure_content_analyzer.py --help | head -5

# Test 2: Create sample configuration
echo
echo "🧪 Test 2: Create sample configuration"
echo "-------------------------------------"
python3 secure_content_analyzer.py --create-config

# Test 3: Create test HTML file
echo
echo "🧪 Test 3: Create test HTML file"
echo "-------------------------------"
mkdir -p test_html_data
cat > test_html_data/test_chat.html << EOF
<!DOCTYPE html>
<html>
<head><title>Test Chat</title></head>
<body>
<div class="message">Hello world! I love my family</div>
<div class="message">Let's have a meeting tomorrow</div>
<div class="message">Can you call me later?</div>
<div class="message">I'm happy about the work progress</div>
</body>
</html>
EOF
echo "✅ Created test HTML file with sample messages"

# Test 4: Run basic analysis
echo
echo "🧪 Test 4: Run basic keyword analysis"
echo "------------------------------------"
python3 secure_content_analyzer.py test_html_data --keywords "love,family,meeting,call,happy,work" --verbose

# Test 5: Run with config file
echo
echo "🧪 Test 5: Run with configuration file"
echo "-------------------------------------"
python3 secure_content_analyzer.py test_html_data --config secure_analyzer_config.json --verbose

# Cleanup
echo
echo "🧹 Cleaning up test files..."
rm -rf test_html_data secure_analysis_results

echo
echo "✅ All tests completed successfully!"
echo "📋 The secure analyzer is working properly."
echo
echo "💡 Usage examples:"
echo "   ./run_analyzer.sh /path/to/chats --keywords 'family,work,meeting'"
echo "   python3 secure_content_analyzer.py /path/to/chats --config my_config.json"
echo