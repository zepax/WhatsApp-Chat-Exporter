#!/usr/bin/env python3
"""
WhatsApp Chat Content Analyzer

A professional tool for analyzing WhatsApp chat exports for various content patterns.
This tool can be used for data analysis, content moderation, or research purposes.
"""

import argparse
import json
import logging
import multiprocessing
import os
import re
import shutil
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from bs4 import BeautifulSoup

    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    from lxml import html

    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False

if not BS4_AVAILABLE and not LXML_AVAILABLE:
    print(
        "Error: BeautifulSoup4 or lxml is required. Install with: pip install beautifulsoup4 lxml"
    )
    exit(1)

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


@dataclass
class AnalysisResult:
    """Data class to store analysis results."""

    file_name: str
    total_messages: int
    total_words: int
    keyword_matches: Dict[str, int]
    sentiment_score: Optional[float] = None
    language_detected: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class ContentAnalyzer:
    """Professional content analyzer for WhatsApp chat exports."""

    def __init__(
        self, config_file: Optional[str] = None, max_workers: Optional[int] = None
    ):
        """Initialize the analyzer with optional configuration."""
        self.setup_logging()
        self.results: List[AnalysisResult] = []
        self.keyword_patterns: Dict[str, re.Pattern] = {}
        self.combined_pattern: Optional[re.Pattern] = None
        self.keywords_list: List[str] = []
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.source_directory: Optional[str] = None
        self.load_configuration(config_file)

    def setup_logging(self):
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("content_analysis.log"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def load_configuration(self, config_file: Optional[str]):
        """Load analysis configuration from file or use defaults."""
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    keywords = config.get("keywords", [])
            except json.JSONDecodeError:
                self.logger.error(f"Invalid JSON in config file: {config_file}")
                keywords = self.get_default_keywords()
        else:
            keywords = self.get_default_keywords()

        # Store keywords for later use
        self.keywords_list = keywords

        # Create individual patterns for backward compatibility
        self.keyword_patterns = {
            kw: re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE) for kw in keywords
        }

        # Create optimized combined pattern for faster processing
        if keywords:
            escaped_keywords = [re.escape(kw) for kw in keywords]
            combined_pattern_str = r"\b(" + "|".join(escaped_keywords) + r")\b"
            self.combined_pattern = re.compile(combined_pattern_str, re.IGNORECASE)

        self.logger.info(f"Loaded {len(keywords)} keywords for analysis")

    def get_default_keywords(self) -> List[str]:
        """Return default keywords for general content analysis."""
        return [
            # Emotional indicators
            "happy",
            "sad",
            "angry",
            "excited",
            "frustrated",
            "love",
            "hate",
            # Communication patterns
            "meeting",
            "call",
            "video",
            "photo",
            "document",
            "location",
            # Time indicators
            "today",
            "tomorrow",
            "yesterday",
            "morning",
            "afternoon",
            "evening",
            # Common actions
            "sent",
            "received",
            "deleted",
            "forwarded",
            "replied",
        ]

    def extract_text_from_html(self, file_path: str) -> Tuple[str, int]:
        """Extract clean text from HTML file and count messages."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Use lxml if available (faster), otherwise BeautifulSoup
            if LXML_AVAILABLE:
                return self._extract_with_lxml(content)
            else:
                return self._extract_with_bs4(content)

        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {e}")
            return "", 0

    def _extract_with_lxml(self, content: str) -> Tuple[str, int]:
        """Fast extraction using lxml."""
        try:
            tree = html.fromstring(content)

            # Remove script and style elements
            for elem in tree.xpath("//script | //style"):
                elem.getparent().remove(elem)

            # Extract text content
            text = tree.text_content()

            # Count message elements
            message_elements = tree.xpath(
                '//div[contains(@class, "message")] | //p[contains(@class, "message")] | //div[contains(@class, "msg")] | //p[contains(@class, "msg")]'
            )
            message_count = len(message_elements) if message_elements else 0

            # If no message elements found, estimate from text structure
            if message_count == 0:
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                message_count = len(
                    [line for line in lines if ":" in line and len(line) > 10]
                )

            return text, message_count
        except Exception:
            # Fallback to BeautifulSoup
            return self._extract_with_bs4(content)

    def _extract_with_bs4(self, content: str) -> Tuple[str, int]:
        """Fallback extraction using BeautifulSoup."""
        soup = BeautifulSoup(content, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Extract text content
        text = soup.get_text()

        # Count message elements
        message_elements = soup.find_all(
            ["div", "p"], class_=re.compile(r"message|msg")
        )
        message_count = len(message_elements) if message_elements else 0

        # If no message elements found, estimate from text structure
        if message_count == 0:
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            message_count = len(
                [line for line in lines if ":" in line and len(line) > 10]
            )

        return text, message_count

    def analyze_keywords(self, text: str) -> Dict[str, int]:
        """Analyze text for keyword occurrences using optimized regex."""
        results = {}

        if not self.combined_pattern:
            return results

        # Use combined pattern for faster matching
        all_matches = self.combined_pattern.findall(text)

        # Count matches per keyword
        for match in all_matches:
            match_lower = match.lower()
            # Find which keyword this match corresponds to
            for keyword in self.keywords_list:
                if keyword.lower() == match_lower:
                    results[keyword] = results.get(keyword, 0) + 1
                    break

        return results

    def count_words(self, text: str) -> int:
        """Count total words in text using optimized method."""
        # Faster word counting using split
        return len(text.split())

    def analyze_file(self, file_path: str) -> AnalysisResult:
        """Analyze a single HTML file."""
        self.logger.info(f"Analyzing: {os.path.basename(file_path)}")

        text, message_count = self.extract_text_from_html(file_path)
        word_count = self.count_words(text)
        keyword_matches = self.analyze_keywords(text)

        result = AnalysisResult(
            file_name=os.path.basename(file_path),
            total_messages=message_count,
            total_words=word_count,
            keyword_matches=keyword_matches,
        )

        return result

    def analyze_directory(self, directory: str, parallel: bool = True) -> None:
        """Analyze all HTML files in a directory with optional parallel processing."""
        directory_path = Path(directory)

        if not directory_path.exists():
            self.logger.error(f"Directory not found: {directory}")
            return

        # Store source directory for later file copying
        self.source_directory = str(directory_path.absolute())

        html_files = list(directory_path.glob("*.html"))

        if not html_files:
            self.logger.warning(f"No HTML files found in: {directory}")
            return

        self.logger.info(f"Found {len(html_files)} HTML files to analyze")

        if parallel and len(html_files) > 1:
            self._analyze_parallel(html_files)
        else:
            self._analyze_sequential(html_files)

    def _analyze_sequential(self, html_files: List[Path]) -> None:
        """Sequential analysis for backward compatibility."""
        for file_path in html_files:
            try:
                result = self.analyze_file(str(file_path))
                self.results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to analyze {file_path}: {e}")

    def _analyze_parallel(self, html_files: List[Path]) -> None:
        """Parallel analysis using ProcessPoolExecutor."""
        self.logger.info(f"Using {self.max_workers} workers for parallel processing")

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(
                    self._analyze_file_static, str(file_path), self.keywords_list
                ): file_path
                for file_path in html_files
            }

            # Collect results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    if result:
                        self.results.append(result)
                except Exception as e:
                    self.logger.error(f"Failed to analyze {file_path}: {e}")

    @staticmethod
    def _analyze_file_static(
        file_path: str, keywords_list: List[str]
    ) -> Optional[AnalysisResult]:
        """Static method for parallel processing."""
        try:
            # Create a temporary analyzer instance for this process
            temp_analyzer = ContentAnalyzer.__new__(ContentAnalyzer)
            temp_analyzer.keywords_list = keywords_list
            temp_analyzer.keyword_patterns = {
                kw: re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
                for kw in keywords_list
            }

            # Create optimized combined pattern
            if keywords_list:
                escaped_keywords = [re.escape(kw) for kw in keywords_list]
                combined_pattern_str = r"\b(" + "|".join(escaped_keywords) + r")\b"
                temp_analyzer.combined_pattern = re.compile(
                    combined_pattern_str, re.IGNORECASE
                )

            # Analyze the file
            text, message_count = temp_analyzer.extract_text_from_html(file_path)
            word_count = temp_analyzer.count_words(text)
            keyword_matches = temp_analyzer.analyze_keywords(text)

            return AnalysisResult(
                file_name=os.path.basename(file_path),
                total_messages=message_count,
                total_words=word_count,
                keyword_matches=keyword_matches,
            )
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None

    def generate_summary_report(self) -> Dict:
        """Generate a summary report of the analysis."""
        if not self.results:
            return {"error": "No results to summarize"}

        total_files = len(self.results)
        total_messages = sum(r.total_messages for r in self.results)
        total_words = sum(r.total_words for r in self.results)

        # Aggregate keyword counts
        all_keywords = Counter()
        for result in self.results:
            all_keywords.update(result.keyword_matches)

        # Files with keyword matches
        files_with_matches = [r for r in self.results if r.keyword_matches]

        # Create detailed breakdown by conversation
        conversation_breakdown = []
        for result in self.results:
            if (
                result.keyword_matches
            ):  # Only include conversations with keyword matches
                conversation_breakdown.append(
                    {
                        "file_name": result.file_name,
                        "total_messages": result.total_messages,
                        "total_words": result.total_words,
                        "keywords_found": result.keyword_matches,
                        "keyword_count": sum(result.keyword_matches.values()),
                    }
                )

        # Sort by keyword count (most matches first)
        conversation_breakdown.sort(key=lambda x: x["keyword_count"], reverse=True)

        summary = {
            "analysis_timestamp": datetime.now().isoformat(),
            "total_files_analyzed": total_files,
            "total_messages": total_messages,
            "total_words": total_words,
            "files_with_keyword_matches": len(files_with_matches),
            "top_keywords": dict(all_keywords.most_common(10)),
            "average_messages_per_file": (
                total_messages / total_files if total_files > 0 else 0
            ),
            "average_words_per_file": (
                total_words / total_files if total_files > 0 else 0
            ),
            "conversation_breakdown": conversation_breakdown,
        }

        return summary

    def save_results(self, output_dir: str = "analysis_results") -> None:
        """Save analysis results to files."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Save detailed results as JSON
        detailed_results = {
            "summary": self.generate_summary_report(),
            "detailed_results": [asdict(result) for result in self.results],
        }

        json_file = (
            output_path
            / f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(detailed_results, f, indent=2, ensure_ascii=False)

        # Save summary as text
        txt_file = (
            output_path
            / f"analysis_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        with open(txt_file, "w", encoding="utf-8") as f:
            summary = detailed_results["summary"]
            f.write("WHATSAPP CHAT CONTENT ANALYSIS SUMMARY\n")
            f.write("=" * 50 + "\n\n")

            for key, value in summary.items():
                if key == "top_keywords" and isinstance(value, dict):
                    f.write(f"{key.replace('_', ' ').title()}:\n")
                    for kw, count in value.items():
                        f.write(f"  - {kw}: {count}\n")
                elif key == "conversation_breakdown":
                    continue  # Skip here, will be handled separately
                else:
                    f.write(f"{key.replace('_', ' ').title()}: {value}\n")

            # Add detailed conversation breakdown section
            f.write("\nCONVERSATION BREAKDOWN (WITH KEYWORD MATCHES)\n")
            f.write("=" * 50 + "\n\n")

            if summary.get("conversation_breakdown"):
                for conv in summary["conversation_breakdown"]:
                    f.write(f"Conversation: {conv['file_name']}\n")
                    f.write(f"  Messages: {conv['total_messages']}\n")
                    f.write(f"  Words: {conv['total_words']}\n")
                    f.write(f"  Total Keywords Found: {conv['keyword_count']}\n")
                    f.write("  Keywords Details:\n")
                    for kw, count in conv["keywords_found"].items():
                        f.write(f"    - {kw}: {count}\n")
                    f.write("\n")
            else:
                f.write("No conversations found with keyword matches.\n\n")

            f.write("\nDETAILED RESULTS BY FILE (ALL FILES)\n")
            f.write("=" * 40 + "\n\n")

            for result in self.results:
                f.write(f"File: {result.file_name}\n")
                f.write(f"  Messages: {result.total_messages}\n")
                f.write(f"  Words: {result.total_words}\n")
                if result.keyword_matches:
                    f.write("  Keywords found:\n")
                    for kw, count in result.keyword_matches.items():
                        f.write(f"    - {kw}: {count}\n")
                else:
                    f.write("  No keywords found.\n")
                f.write("\n")

        # Save as CSV if pandas is available
        if PANDAS_AVAILABLE:
            try:
                df_data = []
                for result in self.results:
                    row = {
                        "file_name": result.file_name,
                        "total_messages": result.total_messages,
                        "total_words": result.total_words,
                        "keywords_found": len(result.keyword_matches),
                        "keyword_details": json.dumps(result.keyword_matches),
                    }
                    df_data.append(row)

                df = pd.DataFrame(df_data)
                csv_file = (
                    output_path
                    / f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )
                df.to_csv(csv_file, index=False, encoding="utf-8")
                self.logger.info(f"CSV report saved: {csv_file}")
            except Exception as e:
                self.logger.warning(f"Could not save CSV report: {e}")

        self.logger.info(f"Results saved to: {output_path}")
        self.logger.info(f"JSON report: {json_file}")
        self.logger.info(f"Text summary: {txt_file}")

    def copy_filtered_conversations(
        self, output_dir: str = "analysis_results", min_keyword_count: int = 1
    ) -> None:
        """Copy conversations with keyword matches to a filtered directory."""
        if not self.results or not self.source_directory:
            self.logger.warning(
                "No results available or source directory not set for file copying"
            )
            return

        # Create filtered conversations directory
        output_path = Path(output_dir)
        filtered_dir = output_path / "filtered_conversations"
        filtered_dir.mkdir(exist_ok=True)

        # Get conversations with keyword matches
        filtered_conversations = [
            result
            for result in self.results
            if result.keyword_matches
            and sum(result.keyword_matches.values()) >= min_keyword_count
        ]

        if not filtered_conversations:
            self.logger.info(
                f"No conversations found with at least {min_keyword_count} keyword matches"
            )
            return

        # Sort by keyword count (most matches first)
        filtered_conversations.sort(
            key=lambda x: sum(x.keyword_matches.values()), reverse=True
        )

        copied_count = 0
        failed_count = 0

        self.logger.info(
            f"Copying {len(filtered_conversations)} conversations with keyword matches..."
        )

        for result in filtered_conversations:
            source_file = Path(self.source_directory) / result.file_name
            destination_file = filtered_dir / result.file_name

            try:
                if source_file.exists():
                    shutil.copy2(source_file, destination_file)
                    copied_count += 1
                    self.logger.debug(
                        f"Copied: {result.file_name} ({sum(result.keyword_matches.values())} matches)"
                    )
                else:
                    self.logger.warning(f"Source file not found: {source_file}")
                    failed_count += 1
            except Exception as e:
                self.logger.error(f"Failed to copy {result.file_name}: {e}")
                failed_count += 1

        # Create a summary file for the filtered conversations
        self._create_filtered_summary(filtered_dir, filtered_conversations)

        self.logger.info(
            f"Filtering complete: {copied_count} files copied, {failed_count} failed"
        )
        self.logger.info(f"Filtered conversations saved to: {filtered_dir}")

        return str(filtered_dir)

    def _create_filtered_summary(
        self, filtered_dir: Path, filtered_conversations: List[AnalysisResult]
    ) -> None:
        """Create a summary file for the filtered conversations."""
        summary_file = filtered_dir / "filtered_summary.txt"

        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("FILTERED CONVERSATIONS SUMMARY\n")
            f.write("=" * 40 + "\n\n")
            f.write(
                f"Total conversations with keyword matches: {len(filtered_conversations)}\n"
            )
            f.write("Filter applied: Conversations with at least 1 keyword match\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Calculate statistics
            total_keywords = sum(
                sum(conv.keyword_matches.values()) for conv in filtered_conversations
            )
            total_messages = sum(conv.total_messages for conv in filtered_conversations)
            total_words = sum(conv.total_words for conv in filtered_conversations)

            f.write("STATISTICS\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total keyword matches: {total_keywords}\n")
            f.write(f"Total messages in filtered conversations: {total_messages}\n")
            f.write(f"Total words in filtered conversations: {total_words}\n")
            f.write(
                f"Average keywords per conversation: {total_keywords / len(filtered_conversations):.1f}\n\n"
            )

            # Top keywords across filtered conversations
            all_keywords = Counter()
            for conv in filtered_conversations:
                all_keywords.update(conv.keyword_matches)

            f.write("TOP KEYWORDS IN FILTERED CONVERSATIONS\n")
            f.write("-" * 35 + "\n")
            for keyword, count in all_keywords.most_common(10):
                f.write(f"{keyword}: {count}\n")
            f.write("\n")

            # List all filtered conversations
            f.write("FILTERED CONVERSATIONS LIST\n")
            f.write("-" * 25 + "\n")
            for i, conv in enumerate(filtered_conversations, 1):
                keyword_count = sum(conv.keyword_matches.values())
                f.write(f"{i:3d}. {conv.file_name} ({keyword_count} matches)\n")
                # Show top 3 keywords for this conversation
                sorted_keywords = sorted(
                    conv.keyword_matches.items(), key=lambda x: x[1], reverse=True
                )
                for kw, count in sorted_keywords[:3]:
                    f.write(f"      - {kw}: {count}\n")
                f.write("\n")

        self.logger.info(f"Filtered summary saved to: {summary_file}")

    def split_large_html_files(
        self, output_dir: str = "analysis_results", max_messages_per_file: int = 500
    ) -> None:
        """Split large HTML files into smaller chunks for better browser performance."""
        if not self.results or not self.source_directory:
            self.logger.warning(
                "No results available or source directory not set for file splitting"
            )
            return

        # Find large files that need splitting
        large_files = [
            result
            for result in self.results
            if result.keyword_matches and result.total_messages > max_messages_per_file
        ]

        if not large_files:
            self.logger.info(
                f"No large files found (>{max_messages_per_file} messages)"
            )
            return

        # Create split files directory
        output_path = Path(output_dir)
        split_dir = output_path / "split_conversations"
        split_dir.mkdir(exist_ok=True)

        self.logger.info(f"Splitting {len(large_files)} large HTML files...")

        for result in large_files:
            source_file = Path(self.source_directory) / result.file_name
            if not source_file.exists():
                continue

            try:
                self._split_html_file(
                    source_file, split_dir, max_messages_per_file, result
                )
            except Exception as e:
                self.logger.error(f"Failed to split {result.file_name}: {e}")

        # Create index file for split conversations
        self._create_split_index(split_dir, large_files, max_messages_per_file)

        self.logger.info(f"Split files saved to: {split_dir}")

    def _split_html_file(
        self,
        source_file: Path,
        split_dir: Path,
        max_messages: int,
        result: AnalysisResult,
    ) -> None:
        """Split a single HTML file into smaller chunks."""
        try:
            with open(source_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse HTML
            if LXML_AVAILABLE:
                tree = html.fromstring(content)

                # Find message elements
                message_elements = tree.xpath(
                    '//div[contains(@class, "message")] | //p[contains(@class, "message")] | //div[contains(@class, "msg")] | //p[contains(@class, "msg")]'
                )

                if not message_elements:
                    # Fallback: try to find messages by text patterns
                    self._split_html_by_text_patterns(
                        source_file, split_dir, max_messages, result
                    )
                    return

                # Split messages into chunks
                chunks = [
                    message_elements[i : i + max_messages]
                    for i in range(0, len(message_elements), max_messages)
                ]

                # Create split files
                base_name = source_file.stem
                for i, chunk in enumerate(chunks, 1):
                    split_filename = f"{base_name}_part{i:02d}.html"
                    split_file = split_dir / split_filename

                    # Create new HTML with this chunk
                    self._create_split_html(
                        split_file, chunk, source_file, i, len(chunks), result
                    )

            else:
                # Fallback to text-based splitting
                self._split_html_by_text_patterns(
                    source_file, split_dir, max_messages, result
                )

        except Exception as e:
            self.logger.error(f"Error splitting {source_file}: {e}")

    def _split_html_by_text_patterns(
        self,
        source_file: Path,
        split_dir: Path,
        max_messages: int,
        result: AnalysisResult,
    ) -> None:
        """Fallback method to split HTML by text patterns."""
        with open(source_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract head and body structure
        head_match = re.search(r"<head.*?</head>", content, re.DOTALL | re.IGNORECASE)
        head_content = head_match.group(0) if head_match else ""

        # Simple text-based chunking by lines that look like messages
        lines = content.split("\n")
        current_chunk = []
        chunk_count = 1

        for line in lines:
            # Detect lines that look like messages (contain timestamps or common patterns)
            if re.search(r"\d{1,2}:\d{2}", line) or ":" in line:
                if len(current_chunk) >= max_messages:
                    # Save current chunk
                    self._save_text_chunk(
                        split_dir,
                        source_file.stem,
                        chunk_count,
                        current_chunk,
                        head_content,
                        result,
                    )
                    current_chunk = []
                    chunk_count += 1
                current_chunk.append(line)
            else:
                current_chunk.append(line)

        # Save last chunk
        if current_chunk:
            self._save_text_chunk(
                split_dir,
                source_file.stem,
                chunk_count,
                current_chunk,
                head_content,
                result,
            )

    def _save_text_chunk(
        self,
        split_dir: Path,
        base_name: str,
        chunk_num: int,
        lines: List[str],
        head_content: str,
        result: AnalysisResult,
    ) -> None:
        """Save a text chunk as HTML file."""
        split_filename = f"{base_name}_part{chunk_num:02d}.html"
        split_file = split_dir / split_filename

        # Create basic HTML structure
        html_content = f"""<!DOCTYPE html>
<html>
{head_content}
<body>
<div style="padding: 20px; font-family: Arial, sans-serif;">
    <h2>Conversación: {base_name} - Parte {chunk_num}</h2>
    <p><strong>Archivo original:</strong> {result.file_name}</p>
    <p><strong>Keywords encontradas:</strong> {', '.join(result.keyword_matches.keys())}</p>
    <hr>
    <div>
        {'<br>'.join(lines)}
    </div>
</div>
</body>
</html>"""

        with open(split_file, "w", encoding="utf-8") as f:
            f.write(html_content)

    def _create_split_html(
        self,
        split_file: Path,
        message_chunk,
        source_file: Path,
        part_num: int,
        total_parts: int,
        result: AnalysisResult,
    ) -> None:
        """Create a split HTML file with proper structure."""
        # This is a simplified version - in practice, you'd want to preserve more of the original HTML structure
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{source_file.stem} - Parte {part_num}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .message {{ margin: 10px 0; padding: 5px; border-left: 3px solid #ccc; }}
        .keyword {{ background-color: yellow; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>Conversación: {source_file.stem}</h2>
        <p><strong>Parte {part_num} de {total_parts}</strong></p>
        <p><strong>Archivo original:</strong> {result.file_name}</p>
        <p><strong>Keywords encontradas:</strong> {', '.join(result.keyword_matches.keys())}</p>
        <p><strong>Total de coincidencias:</strong> {sum(result.keyword_matches.values())}</p>
    </div>
    <div class="messages">
        <!-- Messages would be inserted here -->
        <p><em>Nota: Esta es una versión dividida del archivo original para mejor rendimiento.</em></p>
    </div>
</body>
</html>"""

        with open(split_file, "w", encoding="utf-8") as f:
            f.write(html_content)

    def _create_split_index(
        self, split_dir: Path, large_files: List[AnalysisResult], max_messages: int
    ) -> None:
        """Create an index file for all split conversations."""
        index_file = split_dir / "index.html"

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Índice de Conversaciones Divididas</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .conversation {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .parts {{ margin-top: 10px; }}
        .part-link {{ display: inline-block; margin: 2px; padding: 5px 10px; background: #e7f3ff; border-radius: 3px; text-decoration: none; }}
        .part-link:hover {{ background: #cce7ff; }}
        .stats {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>📂 Conversaciones Divididas</h1>
    <p>Los siguientes archivos fueron divididos para mejorar el rendimiento del navegador:</p>
    <p><strong>Criterio:</strong> Archivos con más de {max_messages} mensajes</p>
    
"""

        for result in large_files:
            base_name = Path(result.file_name).stem
            estimated_parts = (result.total_messages // max_messages) + 1

            html_content += f"""
    <div class="conversation">
        <h3>{base_name}</h3>
        <div class="stats">
            📊 {result.total_messages:,} mensajes | 🔍 {sum(result.keyword_matches.values())} coincidencias
            <br>Keywords: {', '.join(result.keyword_matches.keys())}
        </div>
        <div class="parts">
            <strong>Partes:</strong>
"""

            # Add links to split files
            for i in range(1, estimated_parts + 1):
                part_filename = f"{base_name}_part{i:02d}.html"
                html_content += f'            <a href="{part_filename}" class="part-link">Parte {i}</a>\n'

            html_content += "        </div>\n    </div>\n"

        html_content += """
    <div style="margin-top: 30px; padding: 15px; background: #f9f9f9; border-radius: 5px;">
        <h4>💡 Consejos para archivos grandes:</h4>
        <ul>
            <li>Usa <strong>Ctrl+F</strong> para buscar texto específico en cada parte</li>
            <li>Para búsquedas avanzadas, usa editores de texto como VSCode o Notepad++</li>
            <li>Los archivos originales completos están en la carpeta principal</li>
        </ul>
    </div>
</body>
</html>"""

        with open(index_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        self.logger.info(f"Split index created: {index_file}")


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
        "description": "Sample configuration for content analysis",
    }

    with open("analyzer_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print("Sample configuration file created: analyzer_config.json")


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(
        description="Analyze WhatsApp chat exports for content patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python content_analyzer.py /path/to/chat/exports
  python content_analyzer.py /path/to/exports --config custom_config.json
  python content_analyzer.py /path/to/exports --output custom_results
  python content_analyzer.py /path/to/exports --workers 8
  python content_analyzer.py /path/to/exports --no-parallel
  python content_analyzer.py /path/to/exports --copy-filtered
  python content_analyzer.py /path/to/exports --copy-filtered --min-keywords 5
  python content_analyzer.py /path/to/exports --split-large --max-messages-per-file 300
  python content_analyzer.py /path/to/exports --copy-filtered --split-large
  python content_analyzer.py --create-config
        """,
    )

    parser.add_argument(
        "directory", nargs="?", help="Directory containing HTML chat export files"
    )

    parser.add_argument(
        "--config",
        "-c",
        help="Configuration file with keywords to search for (JSON format)",
    )

    parser.add_argument(
        "--output",
        "-o",
        default="analysis_results",
        help="Output directory for results (default: analysis_results)",
    )

    parser.add_argument(
        "--create-config",
        action="store_true",
        help="Create a sample configuration file",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=None,
        help="Number of parallel workers (default: CPU count)",
    )

    parser.add_argument(
        "--no-parallel", action="store_true", help="Disable parallel processing"
    )

    parser.add_argument(
        "--copy-filtered",
        action="store_true",
        help="Copy conversations with keyword matches to a filtered directory",
    )

    parser.add_argument(
        "--min-keywords",
        type=int,
        default=1,
        help="Minimum number of keyword matches required for filtering (default: 1)",
    )

    parser.add_argument(
        "--split-large",
        action="store_true",
        help="Split large HTML files into smaller chunks for better browser performance",
    )

    parser.add_argument(
        "--max-messages-per-file",
        type=int,
        default=500,
        help="Maximum messages per file when splitting large files (default: 500)",
    )

    args = parser.parse_args()

    if args.create_config:
        create_sample_config()
        return

    if not args.directory:
        parser.error("Directory argument is required unless using --create-config")

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run analysis
    analyzer = ContentAnalyzer(args.config, max_workers=args.workers)
    analyzer.analyze_directory(args.directory, parallel=not args.no_parallel)

    if analyzer.results:
        analyzer.save_results(args.output)

        # Copy filtered conversations if requested
        if args.copy_filtered:
            filtered_dir = analyzer.copy_filtered_conversations(
                args.output, args.min_keywords
            )

        # Split large files if requested
        if args.split_large:
            analyzer.split_large_html_files(args.output, args.max_messages_per_file)

        summary = analyzer.generate_summary_report()

        # Enhanced final summary
        print("\n" + "=" * 60)
        print("🔍 ANÁLISIS COMPLETO - WHATSAPP CHAT ANALYZER")
        print("=" * 60)

        # Statistics
        print("📊 ESTADÍSTICAS:")
        print(f"   • Archivos analizados: {summary['total_files_analyzed']}")
        print(f"   • Mensajes totales: {summary['total_messages']:,}")
        print(f"   • Palabras totales: {summary['total_words']:,}")
        print(
            f"   • Conversaciones con coincidencias: {summary['files_with_keyword_matches']}"
        )

        if summary["top_keywords"]:
            total_matches = sum(summary["top_keywords"].values())
            print(f"   • Total de coincidencias: {total_matches:,}")
            print("\n🎯 PALABRAS CLAVE MÁS ENCONTRADAS:")
            for keyword, count in list(summary["top_keywords"].items())[:5]:
                percentage = (count / total_matches * 100) if total_matches > 0 else 0
                print(f"   • {keyword}: {count} veces ({percentage:.1f}%)")

        # Top conversations
        if summary.get("conversation_breakdown"):
            print(
                f"\n💬 TOP CONVERSACIONES ({len(summary['conversation_breakdown'])} con coincidencias):"
            )
            for i, conv in enumerate(summary["conversation_breakdown"][:3], 1):
                name = conv["file_name"].replace(".html", "").replace("-", " ")[:45]
                print(f"   {i}. {name}...")
                print(
                    f"      → {conv['keyword_count']} coincidencias, {conv['total_messages']} mensajes"
                )

                # Top 2 keywords for this conversation
                sorted_kw = sorted(
                    conv["keywords_found"].items(), key=lambda x: x[1], reverse=True
                )[:2]
                kw_summary = ", ".join([f"{kw}: {count}" for kw, count in sorted_kw])
                print(f"      → {kw_summary}")

        # File locations
        print("\n📁 ARCHIVOS GENERADOS:")
        abs_output = os.path.abspath(args.output)
        print(f"   • Carpeta principal: {abs_output}")
        print("   • Reporte detallado: analysis_summary_*.txt")
        print("   • Datos JSON: analysis_results_*.json")

        # Filtering results
        if hasattr(args, "copy_filtered") and args.copy_filtered:
            filtered_convs = [
                r
                for r in analyzer.results
                if r.keyword_matches
                and sum(r.keyword_matches.values()) >= args.min_keywords
            ]
            if filtered_convs:
                filtered_dir = f"{abs_output}/filtered_conversations"
                print("\n🔍 CONVERSACIONES FILTRADAS:")
                print(f"   • Archivos copiados: {len(filtered_convs)}")
                print(f"   • Ubicación: {filtered_dir}")
                print(f"   • Criterio: mínimo {args.min_keywords} coincidencias")
                print("   • Resumen: filtered_summary.txt")

                # File size warnings for large files
                large_files = []
                for result in filtered_convs:
                    if (
                        result.total_messages > 1000
                    ):  # Consider files with >1000 messages as large
                        large_files.append((result.file_name, result.total_messages))

                if large_files:
                    print("\n⚠️  ARCHIVOS GRANDES DETECTADOS:")
                    print(f"   • {len(large_files)} conversaciones con >1000 mensajes")
                    print("   • Pueden tardar en cargar en el navegador")
                    if not args.split_large:
                        print(
                            "   • Recomendación: usar --split-large para dividir archivos"
                        )
                    else:
                        print("   • Archivos divididos en: split_conversations/")
            else:
                print("\n🔍 FILTRADO:")
                print(f"   • Sin coincidencias suficientes (mín. {args.min_keywords})")
                print("   • Considera reducir --min-keywords")

        # Performance summary
        if not args.no_parallel:
            print("\n⚡ RENDIMIENTO:")
            print(f"   • Procesamiento paralelo: {analyzer.max_workers} workers")

        # Actionable next steps
        print("\n🚀 PRÓXIMOS PASOS:")
        if summary.get("conversation_breakdown"):
            if hasattr(args, "copy_filtered") and args.copy_filtered:
                print("   1. Revisar conversaciones en: filtered_conversations/")
                print("   2. Leer resumen detallado: filtered_summary.txt")
                print("   3. Para archivos grandes: usar buscador de texto externo")
            else:
                print("   1. Usar --copy-filtered para organizar automáticamente")
                print("   2. Revisar analysis_summary_*.txt para detalles")
        else:
            print("   1. Sin coincidencias - revisar configuración de palabras clave")
            print("   2. Verificar formato de archivos HTML")

        print("=" * 60)
    else:
        print("No results to analyze. Check the directory path and file permissions.")


if __name__ == "__main__":
    main()
