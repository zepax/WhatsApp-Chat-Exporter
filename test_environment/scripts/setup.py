#!/usr/bin/env python3
"""
Setup and installation script for WhatsApp Chat Analyzer Professional
Handles dependency installation, configuration, and system setup
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import json
import argparse

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_dependencies(install_type="full"):
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    
    # Base requirements
    base_requirements = [
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "pandas>=1.5.0"
    ]
    
    # Full installation requirements
    full_requirements = [
        "openpyxl>=3.1.0",
        "textblob>=0.17.0", 
        "matplotlib>=3.6.0",
        "seaborn>=0.12.0",
        "plotly>=5.15.0",
        "reportlab>=4.0.0",
        "flask>=2.3.0",
        "schedule>=1.2.0",
        "cryptography>=41.0.0",
        "pyyaml>=6.0",
        "toml>=0.10.0",
        "requests>=2.31.0"
    ]
    
    # Choose requirements based on install type
    if install_type == "minimal":
        requirements = base_requirements
    else:
        requirements = base_requirements + full_requirements
    
    try:
        # Install requirements
        for requirement in requirements:
            print(f"  Installing {requirement}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", requirement
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Failed to install {requirement}")
                print(f"Error: {result.stderr}")
                return False
        
        print("✅ All dependencies installed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def download_nltk_data():
    """Download required NLTK data for sentiment analysis."""
    try:
        import nltk
        print("📥 Downloading NLTK data for sentiment analysis...")
        nltk.download('punkt', quiet=True)
        nltk.download('vader_lexicon', quiet=True)
        nltk.download('stopwords', quiet=True)
        print("✅ NLTK data downloaded")
        return True
    except ImportError:
        print("ℹ️  NLTK not installed, skipping NLTK data download")
        return True
    except Exception as e:
        print(f"⚠️  Failed to download NLTK data: {e}")
        return True  # Non-critical error

def setup_textblob():
    """Setup TextBlob corpora."""
    try:
        import textblob
        print("📥 Downloading TextBlob corpora...")
        
        # Download corpora
        subprocess.run([
            sys.executable, "-m", "textblob.download_corpora"
        ], capture_output=True)
        
        print("✅ TextBlob corpora downloaded")
        return True
    except ImportError:
        print("ℹ️  TextBlob not installed, skipping corpora download")
        return True
    except Exception as e:
        print(f"⚠️  Failed to download TextBlob corpora: {e}")
        return True  # Non-critical error

def create_directory_structure():
    """Create necessary directory structure."""
    print("📁 Creating directory structure...")
    
    directories = [
        ".config",
        ".config/profiles", 
        ".cache",
        "logs",
        "templates",
        "analysis_results",
        "analysis_results/filtered_conversations",
        "analysis_results/split_conversations",
        "analysis_results/exports",
        "analysis_results/audit_logs",
        "analysis_results/privacy_reports",
        "analysis_results/compliance_records"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"  Created: {directory}")
    
    print("✅ Directory structure created")

def create_default_config():
    """Create default configuration files."""
    print("⚙️  Creating default configuration...")
    
    # Default analyzer configuration
    default_config = {
        "analysis": {
            "keywords": [
                "meeting", "call", "video", "photo", "document", "location",
                "happy", "sad", "urgent", "important", "work", "family"
            ],
            "use_regex": False,
            "case_sensitive": False,
            "sentiment_analysis": True,
            "language_detection": True,
            "topic_extraction": True
        },
        "processing": {
            "max_workers": 4,
            "use_cache": True,
            "cache_directory": ".cache"
        },
        "output": {
            "generate_excel": True,
            "generate_pdf": True,
            "generate_dashboard": True
        },
        "security": {
            "anonymize_data": False,
            "encrypt_output": False
        },
        "automation": {
            "auto_cleanup": True,
            "cleanup_after_days": 30,
            "performance_monitoring": True
        },
        "notifications": {
            "email_enabled": False,
            "slack_enabled": False,
            "discord_enabled": False
        },
        "scheduling": {
            "enabled": False,
            "frequency": "weekly",
            "time": "02:00"
        }
    }
    
    # Save default configuration
    config_file = Path(".config/default_config.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Default configuration created: {config_file}")

def create_launcher_script():
    """Create launcher script for easy execution."""
    print("🚀 Creating launcher script...")
    
    # Get current directory
    current_dir = Path.cwd()
    
    if platform.system() == "Windows":
        launcher_content = f"""@echo off
cd /d "{current_dir}"
python content_analyzer.py %*
pause
"""
        launcher_file = "run_analyzer.bat"
    else:
        launcher_content = f"""#!/bin/bash
cd "{current_dir}"
python3 content_analyzer.py "$@"
"""
        launcher_file = "run_analyzer.sh"
    
    with open(launcher_file, 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    
    # Make executable on Unix systems
    if platform.system() != "Windows":
        os.chmod(launcher_file, 0o755)
    
    print(f"✅ Launcher script created: {launcher_file}")

def run_system_checks():
    """Run system compatibility checks."""
    print("🔍 Running system checks...")
    
    checks_passed = 0
    total_checks = 5
    
    # Check 1: Python version
    if check_python_version():
        checks_passed += 1
    
    # Check 2: Pip availability
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      capture_output=True, check=True)
        print("✅ pip is available")
        checks_passed += 1
    except:
        print("❌ pip is not available")
    
    # Check 3: Internet connectivity for downloads
    try:
        import urllib.request
        urllib.request.urlopen('https://pypi.org', timeout=5)
        print("✅ Internet connectivity available")
        checks_passed += 1
    except:
        print("⚠️  Limited internet connectivity - some features may not work")
    
    # Check 4: Memory check
    try:
        import psutil
        memory = psutil.virtual_memory()
        if memory.total >= 2 * 1024 * 1024 * 1024:  # 2GB
            print(f"✅ Sufficient memory: {memory.total // (1024**3):.1f} GB")
            checks_passed += 1
        else:
            print(f"⚠️  Low memory: {memory.total // (1024**3):.1f} GB (2GB+ recommended)")
    except:
        print("ℹ️  Could not check memory requirements")
        checks_passed += 1  # Don't fail for this
    
    # Check 5: Disk space
    try:
        import shutil
        free_space = shutil.disk_usage('.').free
        if free_space >= 1024 * 1024 * 1024:  # 1GB
            print(f"✅ Sufficient disk space: {free_space // (1024**3):.1f} GB free")
            checks_passed += 1
        else:
            print(f"⚠️  Low disk space: {free_space // (1024**2):.1f} MB free")
    except:
        print("ℹ️  Could not check disk space")
        checks_passed += 1  # Don't fail for this
    
    print(f"📊 System checks: {checks_passed}/{total_checks} passed")
    return checks_passed >= 3  # Require at least 3/5 checks to pass

def install_optional_features():
    """Install optional advanced features."""
    print("🎯 Installing optional features...")
    
    optional_packages = {
        "spacy": "Advanced NLP processing",
        "nltk": "Additional language processing",
        "psutil": "System monitoring",
        "watchdog": "File system monitoring"
    }
    
    for package, description in optional_packages.items():
        try:
            print(f"  Installing {package} ({description})...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, check=True)
            print(f"  ✅ {package} installed")
        except:
            print(f"  ⚠️  {package} installation failed (optional)")

def create_example_config():
    """Create example configuration file."""
    print("📄 Creating example configuration file...")
    
    example_config = {
        "keywords": [
            "example_keyword_1",
            "example_keyword_2", 
            "regex_pattern.*",
            "case_sensitive_WORD"
        ],
        "description": "Example configuration file for WhatsApp Chat Analyzer",
        "use_regex": True,
        "case_sensitive": False,
        "sentiment_analysis": True,
        "language_detection": True,
        "topic_extraction": True,
        "categories": {
            "work": ["meeting", "project", "deadline", "client"],
            "personal": ["family", "friend", "party", "vacation"],
            "technology": ["app", "software", "computer", "phone"]
        }
    }
    
    with open("example_config.json", 'w', encoding='utf-8') as f:
        json.dump(example_config, f, indent=2, ensure_ascii=False)
    
    print("✅ Example configuration created: example_config.json")

def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="WhatsApp Chat Analyzer Setup")
    parser.add_argument("--install-type", choices=["minimal", "full"], 
                       default="full", help="Installation type")
    parser.add_argument("--skip-checks", action="store_true", 
                       help="Skip system compatibility checks")
    parser.add_argument("--no-optional", action="store_true",
                       help="Skip optional feature installation")
    
    args = parser.parse_args()
    
    print("🔧 WhatsApp Chat Analyzer Professional - Setup Script")
    print("=" * 60)
    
    # Run system checks
    if not args.skip_checks:
        if not run_system_checks():
            print("\n❌ System checks failed. Use --skip-checks to bypass.")
            return False
    
    # Install dependencies
    if not install_dependencies(args.install_type):
        print("\n❌ Dependency installation failed")
        return False
    
    # Setup NLP libraries
    if args.install_type == "full":
        download_nltk_data()
        setup_textblob()
    
    # Install optional features
    if not args.no_optional and args.install_type == "full":
        install_optional_features()
    
    # Create directory structure
    create_directory_structure()
    
    # Create configuration files
    create_default_config()
    create_example_config()
    
    # Create launcher script
    create_launcher_script()
    
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit the configuration file: .config/default_config.json")
    print("2. Run the analyzer: python content_analyzer.py --help")
    print("3. For web dashboard: python content_analyzer.py /path/to/chats --generate-dashboard")
    print("4. See example_config.json for configuration examples")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)