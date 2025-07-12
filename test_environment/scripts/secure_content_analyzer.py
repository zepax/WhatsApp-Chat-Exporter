#!/usr/bin/env python3
"""
Secure WhatsApp Chat Content Analyzer - Refactored Version

A secure and simplified tool for analyzing WhatsApp chat exports.
Focuses on security, simplicity, and essential functionality only.
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from bs4 import BeautifulSoup

    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

# Security constants
MAX_FILE_SIZE_MB = 50  # Maximum file size to process
MAX_FILES = 1000  # Maximum number of files to process
MAX_KEYWORDS = 100  # Maximum number of keywords
MAX_PATH_LENGTH = 260  # Maximum path length
ALLOWED_EXTENSIONS = {".html", ".htm"}  # Only HTML files
BLOCKED_PATTERNS = ["..", "~", "$", "|", ";", "&", "`"]  # Path traversal patterns


@dataclass
class SecureAnalysisResult:
    """Simplified and secure analysis result."""

    file_name: str
    file_size_bytes: int
    total_messages: int
    total_words: int
    keyword_matches: Dict[str, int]
    processing_time: float
    timestamp: str
    errors: List[str]

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.errors is None:
            self.errors = []


class SecurePathValidator:
    """Secure path validation utilities."""

    @staticmethod
    def is_safe_path(path: str, base_dir: str) -> bool:
        """Validate that a path is safe and within allowed directory."""
        try:
            # Convert to Path objects
            path_obj = Path(path).resolve()
            base_obj = Path(base_dir).resolve()

            # Check path length
            if len(str(path_obj)) > MAX_PATH_LENGTH:
                return False

            # Check for blocked patterns
            path_str = str(path_obj).lower()
            if any(pattern in path_str for pattern in BLOCKED_PATTERNS):
                return False

            # Ensure path is within base directory
            try:
                path_obj.relative_to(base_obj)
                return True
            except ValueError:
                return False

        except (OSError, ValueError):
            return False

    @staticmethod
    def is_allowed_file(file_path: str) -> bool:
        """Check if file extension is allowed."""
        return Path(file_path).suffix.lower() in ALLOWED_EXTENSIONS

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size safely."""
        try:
            return os.path.getsize(file_path)
        except (OSError, ValueError):
            return 0


class SecureContentAnalyzer:
    """Secure and simplified content analyzer for WhatsApp chats."""

    def __init__(self, keywords: List[str], base_directory: str):
        """Initialize with security validations."""
        self.setup_logging()

        # Validate and store base directory
        self.base_directory = str(Path(base_directory).resolve())
        if not os.path.isdir(self.base_directory):
            raise ValueError(f"Invalid base directory: {base_directory}")

        # Validate and store keywords
        if not keywords or len(keywords) > MAX_KEYWORDS:
            raise ValueError(f"Keywords must be between 1 and {MAX_KEYWORDS}")

        self.keywords = [kw.strip() for kw in keywords if kw.strip()]
        if not self.keywords:
            raise ValueError("No valid keywords provided")

        # Compile patterns securely
        self.keyword_patterns = {}
        for keyword in self.keywords:
            try:
                # Escape keyword to prevent regex injection
                escaped_kw = re.escape(keyword)
                pattern = re.compile(rf"\b{escaped_kw}\b", re.IGNORECASE)
                self.keyword_patterns[keyword] = pattern
            except re.error as e:
                self.logger.warning(f"Invalid keyword '{keyword}': {e}")

        if not self.keyword_patterns:
            raise ValueError("No valid keyword patterns could be compiled")

        self.results: List[SecureAnalysisResult] = []
        self.logger.info(
            f"Analyzer initialized with {len(self.keyword_patterns)} keywords"
        )

    def setup_logging(self):
        """Configure secure logging."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        self.logger = logging.getLogger(__name__)

    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """Comprehensive file validation."""
        # Check if path is safe
        if not SecurePathValidator.is_safe_path(file_path, self.base_directory):
            return False, "Unsafe file path"

        # Check if file exists
        if not os.path.isfile(file_path):
            return False, "File does not exist"

        # Check file extension
        if not SecurePathValidator.is_allowed_file(file_path):
            return (
                False,
                f"File extension not allowed. Only {ALLOWED_EXTENSIONS} are permitted",
            )

        # Check file size
        file_size = SecurePathValidator.get_file_size(file_path)
        max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_size_bytes:
            return False, f"File too large: {file_size} bytes (max: {max_size_bytes})"

        return True, "Valid"

    def extract_text_from_html(self, file_path: str) -> Tuple[str, int, List[str]]:
        """Securely extract text from HTML file."""
        errors = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                # Read with size limit
                content = f.read(MAX_FILE_SIZE_MB * 1024 * 1024)

            if not BS4_AVAILABLE:
                # Fallback: simple text extraction with regex
                text = re.sub(r"<[^>]+>", " ", content)
                text = re.sub(r"\s+", " ", text).strip()

                # Estimate message count
                lines = text.split("\n")
                message_count = len(
                    [line for line in lines if ":" in line and len(line.strip()) > 10]
                )

                return text, message_count, errors

            # Use BeautifulSoup for better extraction
            soup = BeautifulSoup(content, "html.parser")

            # Remove scripts and styles
            for element in soup(["script", "style"]):
                element.decompose()

            # Extract clean text
            text = soup.get_text(separator=" ")
            text = re.sub(r"\s+", " ", text).strip()

            # Count message elements
            message_elements = soup.find_all(
                ["div", "p"], class_=re.compile(r"message|msg")
            )
            message_count = len(message_elements) if message_elements else 0

            # Fallback message counting
            if message_count == 0:
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                message_count = len(
                    [line for line in lines if ":" in line and len(line) > 10]
                )

            return text, message_count, errors

        except Exception as e:
            error_msg = f"Error extracting text: {str(e)}"
            errors.append(error_msg)
            self.logger.error(f"Failed to extract text from {file_path}: {e}")
            return "", 0, errors

    def analyze_keywords(self, text: str) -> Dict[str, int]:
        """Analyze text for keyword occurrences."""
        results = {}

        # Limit text size for analysis
        max_text_length = 1024 * 1024  # 1MB of text
        if len(text) > max_text_length:
            text = text[:max_text_length]
            self.logger.warning("Text truncated for analysis due to size limit")

        for keyword, pattern in self.keyword_patterns.items():
            try:
                matches = pattern.findall(text)
                if matches:
                    results[keyword] = len(matches)
            except Exception as e:
                self.logger.warning(f"Error analyzing keyword '{keyword}': {e}")

        return results

    def count_words(self, text: str) -> int:
        """Count words in text safely."""
        try:
            # Simple word counting with length limit
            words = text.split()
            return len(words)
        except Exception:
            return 0

    def analyze_file(self, file_path: str) -> Optional[SecureAnalysisResult]:
        """Analyze a single file securely."""
        start_time = time.time()
        errors = []

        # Validate file first
        is_valid, validation_msg = self.validate_file(file_path)
        if not is_valid:
            errors.append(f"Validation failed: {validation_msg}")
            self.logger.warning(f"Skipping {file_path}: {validation_msg}")
            return None

        file_size = SecurePathValidator.get_file_size(file_path)
        file_name = os.path.basename(file_path)

        self.logger.info(f"Analyzing: {file_name} ({file_size:,} bytes)")

        try:
            # Extract text
            text, message_count, extraction_errors = self.extract_text_from_html(
                file_path
            )
            errors.extend(extraction_errors)

            # Analyze content
            word_count = self.count_words(text)
            keyword_matches = self.analyze_keywords(text)

            processing_time = time.time() - start_time

            result = SecureAnalysisResult(
                file_name=file_name,
                file_size_bytes=file_size,
                total_messages=message_count,
                total_words=word_count,
                keyword_matches=keyword_matches,
                processing_time=processing_time,
                timestamp=datetime.now().isoformat(),
                errors=errors,
            )

            return result

        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            errors.append(error_msg)
            self.logger.error(f"Failed to analyze {file_path}: {e}")
            return None

    def analyze_directory(self, directory: str = None) -> bool:
        """Analyze all valid HTML files in directory."""
        if directory is None:
            directory = self.base_directory

        # Validate directory
        if not SecurePathValidator.is_safe_path(directory, self.base_directory):
            self.logger.error(f"Unsafe directory path: {directory}")
            return False

        if not os.path.isdir(directory):
            self.logger.error(f"Directory not found: {directory}")
            return False

        # Find HTML files
        html_files = []
        try:
            for file_path in Path(directory).rglob("*"):
                if file_path.is_file() and SecurePathValidator.is_allowed_file(
                    str(file_path)
                ):
                    if SecurePathValidator.is_safe_path(
                        str(file_path), self.base_directory
                    ):
                        html_files.append(str(file_path))
        except Exception as e:
            self.logger.error(f"Error scanning directory: {e}")
            return False

        if not html_files:
            self.logger.warning(f"No valid HTML files found in: {directory}")
            return False

        if len(html_files) > MAX_FILES:
            self.logger.warning(
                f"Too many files ({len(html_files)}). Limiting to {MAX_FILES}"
            )
            html_files = html_files[:MAX_FILES]

        self.logger.info(f"Found {len(html_files)} HTML files to analyze")

        # Analyze files sequentially (safer than parallel)
        successful_analyses = 0
        for file_path in html_files:
            result = self.analyze_file(file_path)
            if result:
                self.results.append(result)
                successful_analyses += 1

        self.logger.info(
            f"Successfully analyzed {successful_analyses}/{len(html_files)} files"
        )
        return successful_analyses > 0

    def generate_summary(self) -> Dict:
        """Generate secure summary report."""
        if not self.results:
            return {"error": "No results to summarize"}

        total_files = len(self.results)
        total_messages = sum(r.total_messages for r in self.results)
        total_words = sum(r.total_words for r in self.results)
        total_size_mb = sum(r.file_size_bytes for r in self.results) / (1024 * 1024)

        # Aggregate keyword counts
        all_keywords = {}
        for result in self.results:
            for keyword, count in result.keyword_matches.items():
                all_keywords[keyword] = all_keywords.get(keyword, 0) + count

        # Sort keywords by frequency
        top_keywords = dict(
            sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)[:10]
        )

        # Files with matches
        files_with_matches = [r for r in self.results if r.keyword_matches]

        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "total_files_analyzed": total_files,
            "total_messages": total_messages,
            "total_words": total_words,
            "total_size_mb": round(total_size_mb, 2),
            "files_with_keyword_matches": len(files_with_matches),
            "top_keywords": top_keywords,
            "keywords_searched": self.keywords,
            "average_messages_per_file": (
                round(total_messages / total_files, 1) if total_files > 0 else 0
            ),
            "average_processing_time": (
                round(sum(r.processing_time for r in self.results) / total_files, 2)
                if total_files > 0
                else 0
            ),
        }

    def save_results(self, output_dir: str = "secure_analysis_results") -> bool:
        """Save results to secure output directory."""
        try:
            # Create output directory safely
            output_path = Path(output_dir).resolve()

            # Ensure output directory is safe
            if not SecurePathValidator.is_safe_path(str(output_path), os.getcwd()):
                self.logger.error(f"Unsafe output directory: {output_dir}")
                return False

            output_path.mkdir(exist_ok=True)

            # Generate summary
            summary = self.generate_summary()

            # Save JSON report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = output_path / f"secure_analysis_{timestamp}.json"

            report_data = {
                "summary": summary,
                "detailed_results": [asdict(result) for result in self.results],
            }

            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            # Save text summary
            txt_file = output_path / f"summary_{timestamp}.txt"
            with open(txt_file, "w", encoding="utf-8") as f:
                f.write("SECURE WHATSAPP CHAT ANALYSIS SUMMARY\n")
                f.write("=" * 50 + "\n\n")

                for key, value in summary.items():
                    if key == "top_keywords" and isinstance(value, dict):
                        f.write(f"{key.replace('_', ' ').title()}:\n")
                        for kw, count in value.items():
                            f.write(f"  - {kw}: {count}\n")
                    else:
                        f.write(f"{key.replace('_', ' ').title()}: {value}\n")

                f.write("\nDETAILED RESULTS:\n")
                f.write("-" * 30 + "\n")
                for result in self.results:
                    f.write(f"\nFile: {result.file_name}\n")
                    f.write(f"  Size: {result.file_size_bytes:,} bytes\n")
                    f.write(f"  Messages: {result.total_messages:,}\n")
                    f.write(f"  Words: {result.total_words:,}\n")
                    f.write(f"  Processing time: {result.processing_time:.2f}s\n")
                    if result.keyword_matches:
                        f.write("  Keywords found:\n")
                        for kw, count in result.keyword_matches.items():
                            f.write(f"    - {kw}: {count}\n")
                    if result.errors:
                        f.write("  Errors:\n")
                        for error in result.errors:
                            f.write(f"    - {error}\n")

            self.logger.info(f"Results saved to: {output_path}")
            self.logger.info(f"JSON report: {json_file}")
            self.logger.info(f"Text summary: {txt_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
            return False


def create_sample_config():
    """Create a sample configuration file."""
    config = {
        "keywords": [
            "meeting",
            "call",
            "video",
            "photo",
            "document",
            "happy",
            "sad",
            "excited",
            "love",
            "work",
            "family",
            "friend",
            "party",
            "travel",
            "food",
        ],
        "description": "Sample secure configuration for content analysis",
    }

    config_file = "secure_analyzer_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print(f"Sample configuration created: {config_file}")


def main():
    """Main function with secure CLI interface."""
    parser = argparse.ArgumentParser(
        description="Secure WhatsApp Chat Content Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python secure_content_analyzer.py /path/to/chat/exports
  python secure_content_analyzer.py /path/to/exports --config config.json
  python secure_content_analyzer.py /path/to/exports --keywords love,family,work
  python secure_content_analyzer.py --create-config
        """,
    )

    parser.add_argument(
        "directory", nargs="?", help="Directory containing HTML chat export files"
    )

    parser.add_argument("--config", "-c", help="JSON configuration file with keywords")

    parser.add_argument(
        "--keywords", "-k", help="Comma-separated list of keywords to search for"
    )

    parser.add_argument(
        "--output",
        "-o",
        default="secure_analysis_results",
        help="Output directory for results (default: secure_analysis_results)",
    )

    parser.add_argument(
        "--create-config",
        action="store_true",
        help="Create a sample configuration file",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.create_config:
        create_sample_config()
        return

    if not args.directory:
        parser.error("Directory argument is required unless using --create-config")

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load keywords
    keywords = []
    if args.config:
        try:
            with open(args.config, "r", encoding="utf-8") as f:
                config = json.load(f)
                keywords = config.get("keywords", [])
        except Exception as e:
            print(f"Error loading config file: {e}")
            return
    elif args.keywords:
        keywords = [kw.strip() for kw in args.keywords.split(",")]
    else:
        # Default keywords
        keywords = ["meeting", "call", "video", "photo", "happy", "work", "family"]

    if not keywords:
        print("No keywords specified. Use --keywords or --config")
        return

    try:
        # Create secure analyzer
        analyzer = SecureContentAnalyzer(keywords, args.directory)

        # Run analysis
        success = analyzer.analyze_directory()

        if success and analyzer.results:
            # Save results
            analyzer.save_results(args.output)

            # Display summary
            summary = analyzer.generate_summary()
            print("\n" + "=" * 50)
            print("🔍 SECURE ANALYSIS COMPLETE")
            print("=" * 50)
            print(f"📁 Files analyzed: {summary['total_files_analyzed']}")
            print(f"📊 Total messages: {summary['total_messages']:,}")
            print(f"📝 Total words: {summary['total_words']:,}")
            print(f"💾 Total size: {summary['total_size_mb']} MB")
            print(f"🎯 Files with matches: {summary['files_with_keyword_matches']}")

            if summary["top_keywords"]:
                print("\n🔍 Top keywords found:")
                for keyword, count in list(summary["top_keywords"].items())[:5]:
                    print(f"  • {keyword}: {count}")

            print(f"\n📋 Results saved to: {os.path.abspath(args.output)}")
            print("=" * 50)
        else:
            print("Analysis completed but no results were generated.")

    except Exception as e:
        print(f"Error: {e}")
        return


if __name__ == "__main__":
    main()
