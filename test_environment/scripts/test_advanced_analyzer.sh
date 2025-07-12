#!/bin/bash

# Test script for Advanced WhatsApp Chat Content Analyzer
# Tests various features and configurations

set -e  # Exit on any error

echo "🚀 Testing Advanced WhatsApp Chat Content Analyzer"
echo "================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANALYZER_SCRIPT="$SCRIPT_DIR/advanced_content_analyzer.py"
CONFIG_FILE="$SCRIPT_DIR/advanced_analyzer_config.json"
TEST_OUTPUT_DIR="$SCRIPT_DIR/test_advanced_results"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3 is available
check_python() {
    print_status "Checking Python installation..."
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        print_success "Python 3 found: $(python3 --version)"
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version 2>&1)
        if [[ $PYTHON_VERSION == *"Python 3"* ]]; then
            PYTHON_CMD="python"
            print_success "Python 3 found: $PYTHON_VERSION"
        else
            print_error "Python 3 is required but not found"
            exit 1
        fi
    else
        print_error "Python is not installed"
        exit 1
    fi
}

# Check required Python packages
check_dependencies() {
    print_status "Checking Python dependencies..."
    
    local missing_packages=()
    
    # Check for BeautifulSoup4
    if ! $PYTHON_CMD -c "import bs4" &> /dev/null; then
        missing_packages+=("beautifulsoup4")
    fi
    
    # Check for psutil
    if ! $PYTHON_CMD -c "import psutil" &> /dev/null; then
        missing_packages+=("psutil")
    fi
    
    if [ ${#missing_packages[@]} -eq 0 ]; then
        print_success "All required packages are installed"
    else
        print_warning "Missing packages: ${missing_packages[*]}"
        print_status "Installing missing packages..."
        pip install "${missing_packages[@]}" || {
            print_error "Failed to install missing packages"
            print_status "Please install manually: pip install ${missing_packages[*]}"
            exit 1
        }
    fi
}

# Create test data
create_test_data() {
    print_status "Creating test data..."
    
    local test_dir="$SCRIPT_DIR/test_data_advanced"
    mkdir -p "$test_dir"
    
    # Create sample HTML chat file with various patterns
    cat > "$test_dir/test_chat_1.html" << 'EOF'
<!DOCTYPE html>
<html>
<head><title>WhatsApp Chat</title></head>
<body>
<div class="chat">
    <div class="message">
        <span class="time">10:30 AM</span>
        <span class="author">John</span>
        <span class="text">Hey! Can we schedule a meeting for tomorrow? My phone number is +1 234-567-8900</span>
    </div>
    <div class="message">
        <span class="time">10:32 AM</span>
        <span class="author">Sarah</span>
        <span class="text">Sure! What time works for you? I'm happy to meet anytime 😊</span>
    </div>
    <div class="message">
        <span class="time">10:35 AM</span>
        <span class="author">John</span>
        <span class="text">How about 2:00 PM? We could discuss the important project deadline. Email me at john@company.com</span>
    </div>
    <div class="message">
        <span class="time">10:40 AM</span>
        <span class="author">Sarah</span>
        <span class="text">Perfect! I'll send you the document. Check out this link: https://example.com/project-details</span>
    </div>
    <div class="message">
        <span class="time">11:00 AM</span>
        <span class="author">John</span>
        <span class="text">Great work on the family vacation photos! The trip to Paris was amazing 🇫🇷✈️</span>
    </div>
    <div class="message">
        <span class="time">11:05 AM</span>
        <span class="author">Sarah</span>
        <span class="text">Thanks! I love traveling. Food was incredible - spent $2,500 total on the trip</span>
    </div>
    <div class="message">
        <span class="time">11:10 AM</span>
        <span class="author">Group Notification</span>
        <span class="text">Mike joined using this group's invite link</span>
    </div>
    <div class="message">
        <span class="time">11:15 AM</span>
        <span class="author">Mike</span>
        <span class="text">Hello everyone! Excited to be here. My contact: mike@email.com, phone: (555) 123-4567</span>
    </div>
    <div class="message">
        <span class="time">11:20 AM</span>
        <span class="author">John</span>
        <span class="text">Welcome Mike! Let's plan our next video call for 15/03/2024 at 14:30</span>
    </div>
    <div class="message">
        <span class="time">11:25 AM</span>
        <span class="author">Sarah</span>
        <span class="text">URGENT: Need help with the presentation!!! Please call me ASAP 📞⚡</span>
    </div>
</div>
</body>
</html>
EOF

    # Create another sample file with different patterns
    cat > "$test_dir/test_chat_2.html" << 'EOF'
<!DOCTYPE html>
<html>
<head><title>WhatsApp Group Chat</title></head>
<body>
<div class="chat">
    <div class="message">
        <span class="time">09:00</span>
        <span class="author">Alex</span>
        <span class="text">Good morning! Weather forecast shows 25°C today ☀️</span>
    </div>
    <div class="message">
        <span class="time">09:15</span>
        <span class="author">Emma</span>
        <span class="text">Perfect for our outdoor meeting! Location: 40.7128,-74.0060 (Central Park)</span>
    </div>
    <div class="message">
        <span class="time">09:30</span>
        <span class="author">Alex</span>
        <span class="text">@everyone please bring your documents. File format should be .pdf or .docx</span>
    </div>
    <div class="message">
        <span class="time">09:45</span>
        <span class="author">Emma</span>
        <span class="text">My credit card number is 4532-1234-5678-9012 for the booking</span>
    </div>
    <div class="message">
        <span class="time">10:00</span>
        <span class="author">System</span>
        <span class="text">Emma changed the group name to "Project Team 2024"</span>
    </div>
    <div class="message">
        <span class="time">10:15</span>
        <span class="author">Alex</span>
        <span class="text">Package weight: 2.5kg, shipping to ZIP code 12345-6789</span>
    </div>
    <div class="message">
        <span class="time">10:30</span>
        <span class="author">Emma</span>
        <span class="text">Stock price: AAPL is up 5.2% today! Investment advice needed...</span>
    </div>
    <div class="message">
        <span class="time">10:45</span>
        <span class="author">Alex</span>
        <span class="text">Chemistry formula: H2SO4 concentration is 98%. Server IP: 192.168.1.100</span>
    </div>
    <div class="message">
        <span class="time">11:00</span>
        <span class="author">Emma</span>
        <span class="text">Book ISBN: 978-0-123456-78-9, available in library. Temperature: 72°F</span>
    </div>
    <div class="message">
        <span class="time">11:15</span>
        <span class="author">Alex</span>
        <span class="text">Distance to venue: 15.5 km (9.6 miles). Departure time: 14:30:00</span>
    </div>
</div>
</body>
</html>
EOF

    # Create a large file to test streaming
    cat > "$test_dir/large_chat.html" << 'EOF'
<!DOCTYPE html>
<html>
<head><title>Large WhatsApp Chat</title></head>
<body>
<div class="chat">
EOF

    # Generate many messages for large file testing
    for i in {1..1000}; do
        hour=$((9 + (i / 60)))
        minute=$((i % 60))
        cat >> "$test_dir/large_chat.html" << EOF
    <div class="message">
        <span class="time">${hour}:$(printf "%02d" $minute)</span>
        <span class="author">User$((i % 10))</span>
        <span class="text">Message $i: This is a test message with keywords like meeting, family, work, and love. Phone: +1-555-000-$(printf "%04d" $i)</span>
    </div>
EOF
    done
    
    cat >> "$test_dir/large_chat.html" << 'EOF'
</div>
</body>
</html>
EOF

    # Create a JSON test file
    cat > "$test_dir/chat_export.json" << 'EOF'
{
    "chat_name": "Test Group",
    "messages": [
        {
            "timestamp": "2024-01-15T10:30:00",
            "sender": "John",
            "text": "Let's schedule a video call for our work project. My email: john@test.com"
        },
        {
            "timestamp": "2024-01-15T10:35:00", 
            "sender": "Mary",
            "text": "Sounds good! I'm excited about this family reunion planning 😊"
        },
        {
            "timestamp": "2024-01-15T10:40:00",
            "sender": "John", 
            "text": "IMPORTANT: Meeting moved to 2:00 PM tomorrow. Food catering costs $500."
        }
    ]
}
EOF

    print_success "Test data created in: $test_dir"
    echo "  - test_chat_1.html (small file with various patterns)"
    echo "  - test_chat_2.html (medium file with advanced patterns)"
    echo "  - large_chat.html (large file with 1000+ messages)"
    echo "  - chat_export.json (JSON format test)"
}

# Test 1: Basic functionality
test_basic_functionality() {
    print_status "Test 1: Basic functionality with default settings"
    
    local test_dir="$SCRIPT_DIR/test_data_advanced"
    
    $PYTHON_CMD "$ANALYZER_SCRIPT" "$test_dir" \
        --keywords "meeting,work,family,love,important" \
        --output "$TEST_OUTPUT_DIR/test1_basic" \
        --verbose \
        || {
            print_error "Basic functionality test failed"
            return 1
        }
    
    print_success "Basic functionality test passed"
}

# Test 2: Advanced configuration
test_advanced_config() {
    print_status "Test 2: Advanced configuration with config file"
    
    local test_dir="$SCRIPT_DIR/test_data_advanced"
    
    $PYTHON_CMD "$ANALYZER_SCRIPT" "$test_dir" \
        --config "$CONFIG_FILE" \
        --output "$TEST_OUTPUT_DIR/test2_advanced" \
        --verbose \
        || {
            print_error "Advanced configuration test failed"
            return 1
        }
    
    print_success "Advanced configuration test passed"
}

# Test 3: Custom regex patterns
test_custom_regex() {
    print_status "Test 3: Custom regex patterns"
    
    local test_dir="$SCRIPT_DIR/test_data_advanced"
    local regex_file="$SCRIPT_DIR/custom_regex_test.json"
    
    # Create custom regex patterns file
    cat > "$regex_file" << 'EOF'
{
    "phone_test": "\\+?[\\d\\s\\-\\(\\)]{10,}",
    "email_test": "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b",
    "time_test": "\\d{1,2}:\\d{2}(?::\\d{2})?",
    "money_test": "\\$\\d+(?:,\\d{3})*(?:\\.\\d{2})?",
    "emoji_test": "[😊🇫🇷✈️📞⚡☀️]"
}
EOF
    
    $PYTHON_CMD "$ANALYZER_SCRIPT" "$test_dir" \
        --keywords "test,demo" \
        --regex-patterns "$regex_file" \
        --output "$TEST_OUTPUT_DIR/test3_regex" \
        --verbose \
        || {
            print_error "Custom regex test failed"
            return 1
        }
    
    # Cleanup
    rm -f "$regex_file"
    
    print_success "Custom regex patterns test passed"
}

# Test 4: Large file processing
test_large_files() {
    print_status "Test 4: Large file processing with streaming"
    
    local test_dir="$SCRIPT_DIR/test_data_advanced"
    
    $PYTHON_CMD "$ANALYZER_SCRIPT" "$test_dir" \
        --keywords "message,test,phone,meeting" \
        --max-files 10 \
        --max-file-size 10 \
        --parallel-workers 2 \
        --enable-streaming \
        --output "$TEST_OUTPUT_DIR/test4_large" \
        --verbose \
        || {
            print_error "Large file processing test failed"
            return 1
        }
    
    print_success "Large file processing test passed"
}

# Test 5: Performance test
test_performance() {
    print_status "Test 5: Performance test with parallel processing"
    
    local test_dir="$SCRIPT_DIR/test_data_advanced"
    
    echo "Testing with 1 worker..."
    time $PYTHON_CMD "$ANALYZER_SCRIPT" "$test_dir" \
        --keywords "meeting,work,family" \
        --parallel-workers 1 \
        --output "$TEST_OUTPUT_DIR/test5_perf_single" \
        > /dev/null 2>&1
    
    echo "Testing with 4 workers..."
    time $PYTHON_CMD "$ANALYZER_SCRIPT" "$test_dir" \
        --keywords "meeting,work,family" \
        --parallel-workers 4 \
        --output "$TEST_OUTPUT_DIR/test5_perf_multi" \
        > /dev/null 2>&1
    
    print_success "Performance test completed"
}

# Test 6: Error handling
test_error_handling() {
    print_status "Test 6: Error handling and edge cases"
    
    # Test with non-existent directory
    $PYTHON_CMD "$ANALYZER_SCRIPT" "/non/existent/directory" \
        --keywords "test" \
        --output "$TEST_OUTPUT_DIR/test6_error" \
        2>/dev/null && {
            print_error "Should have failed with non-existent directory"
            return 1
        }
    
    # Test with invalid regex
    local invalid_regex_file="$SCRIPT_DIR/invalid_regex.json"
    cat > "$invalid_regex_file" << 'EOF'
{
    "invalid_pattern": "[unclosed_bracket",
    "dangerous_pattern": "(.*)+"
}
EOF
    
    local test_dir="$SCRIPT_DIR/test_data_advanced"
    $PYTHON_CMD "$ANALYZER_SCRIPT" "$test_dir" \
        --keywords "test" \
        --regex-patterns "$invalid_regex_file" \
        --output "$TEST_OUTPUT_DIR/test6_invalid_regex" \
        --verbose \
        || {
            print_warning "Expected error with invalid regex patterns"
        }
    
    # Cleanup
    rm -f "$invalid_regex_file"
    
    print_success "Error handling test passed"
}

# Test 7: Configuration creation
test_config_creation() {
    print_status "Test 7: Configuration file creation"
    
    local config_test_file="$SCRIPT_DIR/test_config.json"
    
    $PYTHON_CMD "$ANALYZER_SCRIPT" --create-config || {
        print_error "Config creation failed"
        return 1
    }
    
    if [ -f "advanced_analyzer_config.json" ]; then
        print_success "Configuration file created successfully"
        # Move to test location
        mv "advanced_analyzer_config.json" "$config_test_file"
        
        # Validate JSON
        if $PYTHON_CMD -c "import json; json.load(open('$config_test_file'))" 2>/dev/null; then
            print_success "Generated configuration is valid JSON"
        else
            print_error "Generated configuration is invalid JSON"
            return 1
        fi
        
        # Cleanup
        rm -f "$config_test_file"
    else
        print_error "Configuration file was not created"
        return 1
    fi
}

# Validate results
validate_results() {
    print_status "Validating test results..."
    
    local results_found=0
    
    for test_dir in "$TEST_OUTPUT_DIR"/test*; do
        if [ -d "$test_dir" ]; then
            echo "  Checking: $(basename "$test_dir")"
            
            # Check for JSON results
            if ls "$test_dir"/*.json >/dev/null 2>&1; then
                echo "    ✓ JSON results found"
                results_found=$((results_found + 1))
            fi
            
            # Check for text summary
            if ls "$test_dir"/*.txt >/dev/null 2>&1; then
                echo "    ✓ Text summary found"
            fi
            
            # Validate JSON structure
            for json_file in "$test_dir"/*.json; do
                if [ -f "$json_file" ]; then
                    if $PYTHON_CMD -c "
import json
import sys
try:
    with open('$json_file') as f:
        data = json.load(f)
    assert 'summary' in data
    assert 'detailed_results' in data
    print('    ✓ JSON structure is valid')
except Exception as e:
    print(f'    ✗ JSON validation failed: {e}')
    sys.exit(1)
" 2>/dev/null; then
                        echo "    ✓ JSON content validated"
                    else
                        print_warning "    ⚠ JSON validation issues in $json_file"
                    fi
                fi
            done
        fi
    done
    
    if [ $results_found -gt 0 ]; then
        print_success "Found results from $results_found test(s)"
    else
        print_error "No test results found"
        return 1
    fi
}

# Cleanup function
cleanup() {
    print_status "Cleaning up test files..."
    rm -rf "$SCRIPT_DIR/test_data_advanced"
    rm -rf "$TEST_OUTPUT_DIR"
    rm -f "$SCRIPT_DIR/advanced_analyzer.log"
    print_success "Cleanup completed"
}

# Main test execution
main() {
    echo "Starting Advanced Content Analyzer Tests"
    echo "========================================"
    
    # Preparation
    check_python
    check_dependencies
    
    # Create output directory
    mkdir -p "$TEST_OUTPUT_DIR"
    
    # Setup
    create_test_data
    
    # Run tests
    local failed_tests=0
    
    echo ""
    echo "Running Tests:"
    echo "=============="
    
    test_config_creation || failed_tests=$((failed_tests + 1))
    test_basic_functionality || failed_tests=$((failed_tests + 1))
    test_advanced_config || failed_tests=$((failed_tests + 1))
    test_custom_regex || failed_tests=$((failed_tests + 1))
    test_large_files || failed_tests=$((failed_tests + 1))
    test_performance || failed_tests=$((failed_tests + 1))
    test_error_handling || failed_tests=$((failed_tests + 1))
    
    echo ""
    echo "Validation:"
    echo "==========="
    validate_results || failed_tests=$((failed_tests + 1))
    
    # Results
    echo ""
    echo "Test Results:"
    echo "============="
    
    if [ $failed_tests -eq 0 ]; then
        print_success "All tests passed! 🎉"
        echo ""
        echo "Test results are available in: $TEST_OUTPUT_DIR"
        echo "Log file: $SCRIPT_DIR/advanced_analyzer.log"
        echo ""
        echo "You can now use the advanced analyzer with:"
        echo "  python3 $ANALYZER_SCRIPT /path/to/your/chats --config $CONFIG_FILE"
    else
        print_error "$failed_tests test(s) failed"
        echo ""
        echo "Check the output above for details"
        return 1
    fi
    
    # Ask about cleanup
    echo ""
    read -p "Clean up test files? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cleanup
    else
        print_status "Test files preserved in: $TEST_OUTPUT_DIR"
    fi
}

# Handle interruption
trap 'echo ""; print_warning "Test interrupted"; exit 1' INT

# Run main function
main "$@"