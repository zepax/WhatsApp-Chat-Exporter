#!/bin/bash

# Advanced WhatsApp Chat Content Analyzer - Quick Start Script
# This script demonstrates how to use the advanced analyzer with different configurations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANALYZER="$SCRIPT_DIR/advanced_content_analyzer.py"
CONFIG="$SCRIPT_DIR/advanced_analyzer_config.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}$1${NC}"
    echo "$(printf '=%.0s' {1..60})"
}

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_usage() {
    cat << EOF
🚀 Advanced WhatsApp Chat Content Analyzer - Quick Start

Usage: $0 [CHAT_DIRECTORY] [OPTIONS]

Examples:
  $0 /path/to/chat/exports                    # Basic analysis with defaults
  $0 /path/to/exports --config                # Use advanced configuration
  $0 /path/to/exports --large                 # Optimized for large datasets
  $0 /path/to/exports --regex                 # Enable custom regex patterns
  $0 /path/to/exports --performance           # Performance optimized
  $0 --demo                                   # Run with demo data
  $0 --help                                   # Show this help

Options:
  --config      Use advanced configuration file
  --large       Large dataset optimization (50k files, 1GB each)
  --regex       Enable extensive regex pattern matching
  --performance High-performance mode (8 workers, streaming)
  --demo        Create and analyze demo data
  --help        Show this help message

Advanced Features:
  📊 50+ predefined patterns (phones, emails, URLs, dates, etc.)
  🚀 Streaming analysis for files up to 1GB
  ⚡ Parallel processing with configurable workers
  📈 Advanced statistics and word frequency analysis
  🔍 Custom regex patterns with security validation
  💾 Memory monitoring and batch processing
  📁 Comprehensive JSON and text reporting

EOF
}

create_demo_data() {
    local demo_dir="$SCRIPT_DIR/demo_chat_data"
    print_info "Creating demo chat data in: $demo_dir"
    
    mkdir -p "$demo_dir"
    
    # Create comprehensive demo chat
    cat > "$demo_dir/comprehensive_chat.html" << 'EOF'
<!DOCTYPE html>
<html>
<head><title>WhatsApp Group Chat - Project Team</title></head>
<body>
<div class="chat">
    <div class="message">
        <span class="time">09:00 AM</span>
        <span class="author">Alice</span>
        <span class="text">Good morning team! Ready for our important meeting today? 📅</span>
    </div>
    <div class="message">
        <span class="time">09:05 AM</span>
        <span class="author">Bob</span>
        <span class="text">Yes! I'll call you at +1-555-123-4567. My email is bob@company.com</span>
    </div>
    <div class="message">
        <span class="time">09:10 AM</span>
        <span class="author">Carol</span>
        <span class="text">Perfect! The work deadline is 15/03/2024. Budget: $25,000 for this project</span>
    </div>
    <div class="message">
        <span class="time">09:15 AM</span>
        <span class="author">David</span>
        <span class="text">I love working with this team! Check the document at https://docs.company.com/project</span>
    </div>
    <div class="message">
        <span class="time">09:20 AM</span>
        <span class="author">Alice</span>
        <span class="text">URGENT: Family emergency! Need help with presentation. Contact: alice@email.com</span>
    </div>
    <div class="message">
        <span class="time">09:25 AM</span>
        <span class="author">Bob</span>
        <span class="text">No problem! I'm happy to help. Will video call you in 30 minutes 📞</span>
    </div>
    <div class="message">
        <span class="time">09:30 AM</span>
        <span class="author">Carol</span>
        <span class="text">Team work makes the dream work! Let's schedule another meeting for next week</span>
    </div>
    <div class="message">
        <span class="time">09:35 AM</span>
        <span class="author">David</span>
        <span class="text">Agreed! My phone: (555) 987-6543. Travel expenses: €1,500 for client visit</span>
    </div>
    <div class="message">
        <span class="time">09:40 AM</span>
        <span class="author">System</span>
        <span class="text">Emma joined using this group's invite link</span>
    </div>
    <div class="message">
        <span class="time">09:45 AM</span>
        <span class="author">Emma</span>
        <span class="text">Hello everyone! Excited to work with you. My contact: emma@newcompany.org</span>
    </div>
    <div class="message">
        <span class="time">09:50 AM</span>
        <span class="author">Alice</span>
        <span class="text">Welcome Emma! This family of colleagues is amazing. Temperature today: 22°C ☀️</span>
    </div>
    <div class="message">
        <span class="time">09:55 AM</span>
        <span class="author">Bob</span>
        <span class="text">Great! IP address for server: 192.168.1.100. Meeting room: Building A, coordinates: 40.7128,-74.0060</span>
    </div>
</div>
</body>
</html>
EOF

    # Create personal chat
    cat > "$demo_dir/personal_chat.html" << 'EOF'
<!DOCTYPE html>
<html>
<head><title>WhatsApp Chat - Personal</title></head>
<body>
<div class="chat">
    <div class="message">
        <span class="time">14:00</span>
        <span class="author">John</span>
        <span class="text">Hey! How's your family doing? I love spending time with them 👨‍👩‍👧‍👦</span>
    </div>
    <div class="message">
        <span class="time">14:05</span>
        <span class="author">Mary</span>
        <span class="text">They're great! Work has been busy though. Important deadline on 20/12/2024</span>
    </div>
    <div class="message">
        <span class="time">14:10</span>
        <span class="author">John</span>
        <span class="text">I understand! Want to video call later? My number: +44-20-1234-5678</span>
    </div>
    <div class="message">
        <span class="time">14:15</span>
        <span class="author">Mary</span>
        <span class="text">Sure! Meeting you is always a pleasure. Travel plans: Paris next month! ✈️🇫🇷</span>
    </div>
    <div class="message">
        <span class="time">14:20</span>
        <span class="author">John</span>
        <span class="text">Wonderful! I love travel too. Cost around $3,000? Email me details: john.smith@email.com</span>
    </div>
    <div class="message">
        <span class="time">14:25</span>
        <span class="author">Mary</span>
        <span class="text">Will do! Happy to share the itinerary. Work stress is finally over! 😊</span>
    </div>
</div>
</body>
</html>
EOF

    # Create large chat file for streaming test
    cat > "$demo_dir/large_chat.html" << 'EOF'
<!DOCTYPE html>
<html>
<head><title>WhatsApp Group - Large Chat</title></head>
<body>
<div class="chat">
EOF

    # Generate many messages
    for i in {1..500}; do
        hour=$((9 + (i / 60)))
        minute=$((i % 60))
        user=$((i % 5 + 1))
        
        # Vary message content
        case $((i % 6)) in
            0) content="Meeting scheduled for important work project. Contact: user${user}@company.com" ;;
            1) content="Family dinner tonight! Love spending time together. Phone: +1-555-000-${i}" ;;
            2) content="Work deadline approaching. Need help with video call preparation!" ;;
            3) content="Happy to announce project success! Travel budget: \$${i}00 approved" ;;
            4) content="URGENT: Meeting moved to ${hour}:${minute}. Important update for team" ;;
            5) content="Love working with this team! Family-friendly company culture is amazing" ;;
        esac
        
        cat >> "$demo_dir/large_chat.html" << EOF
    <div class="message">
        <span class="time">${hour}:$(printf "%02d" $minute)</span>
        <span class="author">User${user}</span>
        <span class="text">Message ${i}: ${content}</span>
    </div>
EOF
    done
    
    cat >> "$demo_dir/large_chat.html" << 'EOF'
</div>
</body>
</html>
EOF

    print_info "Demo data created with:"
    echo "  - comprehensive_chat.html (group chat with patterns)"
    echo "  - personal_chat.html (personal conversation)"
    echo "  - large_chat.html (500+ messages for streaming test)"
}

run_basic_analysis() {
    local chat_dir="$1"
    print_header "🔍 Basic Analysis with Default Settings"
    
    python3 "$ANALYZER" "$chat_dir" \
        --keywords "meeting,work,family,love,important,help,travel" \
        --output "basic_analysis_results" \
        --verbose
}

run_advanced_config() {
    local chat_dir="$1"
    print_header "⚙️ Advanced Configuration Analysis"
    
    if [ ! -f "$CONFIG" ]; then
        print_warning "Configuration file not found. Creating one..."
        python3 "$ANALYZER" --create-config
    fi
    
    python3 "$ANALYZER" "$chat_dir" \
        --config "$CONFIG" \
        --output "advanced_config_results" \
        --verbose
}

run_large_dataset() {
    local chat_dir="$1"
    print_header "📊 Large Dataset Optimization"
    
    python3 "$ANALYZER" "$chat_dir" \
        --keywords "meeting,work,family,important,urgent,project,deadline" \
        --max-files 50000 \
        --max-file-size 1000 \
        --parallel-workers 8 \
        --enable-streaming \
        --output "large_dataset_results" \
        --verbose
}

run_regex_analysis() {
    local chat_dir="$1"
    print_header "🔍 Custom Regex Pattern Analysis"
    
    # Create custom regex patterns
    local regex_file="$SCRIPT_DIR/custom_patterns.json"
    cat > "$regex_file" << 'EOF'
{
    "phone_international": "\\+\\d{1,3}[\\s\\-]?\\d{1,14}",
    "email_advanced": "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b",
    "money_multi": "(\\$|€|£)\\d+(?:,\\d{3})*(?:\\.\\d{2})?",
    "coordinates": "\\d{1,3}\\.\\d+,\\s*\\d{1,3}\\.\\d+",
    "ip_addresses": "\\b(?:\\d{1,3}\\.){3}\\d{1,3}\\b",
    "dates_multiple": "\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4}",
    "times_24h": "\\d{1,2}:\\d{2}",
    "urgent_words": "(?i)\\b(urgent|important|asap|emergency|critical)\\b",
    "emotions": "(?i)\\b(love|happy|sad|excited|worried|angry)\\b",
    "work_terms": "(?i)\\b(meeting|deadline|project|work|office|client|budget)\\b"
}
EOF
    
    python3 "$ANALYZER" "$chat_dir" \
        --keywords "analysis,test,demo" \
        --regex-patterns "$regex_file" \
        --parallel-workers 4 \
        --output "regex_analysis_results" \
        --verbose
    
    # Cleanup
    rm -f "$regex_file"
}

run_performance_test() {
    local chat_dir="$1"
    print_header "⚡ Performance Optimization Test"
    
    print_info "Testing with 1 worker (sequential)..."
    time python3 "$ANALYZER" "$chat_dir" \
        --keywords "test,performance" \
        --parallel-workers 1 \
        --output "performance_single" \
        > /dev/null 2>&1
    
    print_info "Testing with 8 workers (parallel)..."
    time python3 "$ANALYZER" "$chat_dir" \
        --keywords "test,performance" \
        --parallel-workers 8 \
        --output "performance_multi" \
        > /dev/null 2>&1
    
    print_info "Performance test completed. Check timing above."
}

cleanup_results() {
    print_info "Cleaning up result directories..."
    rm -rf basic_analysis_results advanced_config_results large_dataset_results 
    rm -rf regex_analysis_results performance_single performance_multi
    rm -rf "$SCRIPT_DIR/demo_chat_data"
    print_info "Cleanup completed"
}

main() {
    case "${1:-}" in
        --help|-h)
            show_usage
            exit 0
            ;;
        --demo)
            print_header "🎯 Demo Mode - Creating and Analyzing Sample Data"
            create_demo_data
            local demo_dir="$SCRIPT_DIR/demo_chat_data"
            
            run_basic_analysis "$demo_dir"
            run_advanced_config "$demo_dir"
            run_regex_analysis "$demo_dir"
            run_performance_test "$demo_dir"
            
            print_header "✅ Demo Complete"
            print_info "Results are available in various *_results directories"
            
            echo ""
            read -p "Clean up demo files and results? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                cleanup_results
            fi
            ;;
        "")
            print_error "Chat directory is required"
            echo ""
            show_usage
            exit 1
            ;;
        --*)
            print_error "Unknown option: $1"
            echo ""
            show_usage
            exit 1
            ;;
        *)
            local chat_dir="$1"
            shift
            
            if [ ! -d "$chat_dir" ]; then
                print_error "Directory not found: $chat_dir"
                exit 1
            fi
            
            case "${1:-basic}" in
                --config)
                    run_advanced_config "$chat_dir"
                    ;;
                --large)
                    run_large_dataset "$chat_dir"
                    ;;
                --regex)
                    run_regex_analysis "$chat_dir"
                    ;;
                --performance)
                    run_performance_test "$chat_dir"
                    ;;
                *)
                    run_basic_analysis "$chat_dir"
                    ;;
            esac
            ;;
    esac
}

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not found"
    exit 1
fi

# Check if analyzer exists
if [ ! -f "$ANALYZER" ]; then
    print_error "Advanced analyzer not found: $ANALYZER"
    exit 1
fi

# Run main function
main "$@"