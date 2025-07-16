#!/usr/bin/env python3
"""
WhatsApp Chat Cleaner - Advanced Chat Processing Tool

A comprehensive tool for cleaning, filtering, and preprocessing WhatsApp chat exports.

Features:
- Remove duplicate messages
- Filter by date ranges
- Clean system messages
- Anonymize personal information
- Validate and clean media references
- Multiple output formats
- Batch processing
- Safe operation with backups
"""

import argparse
import hashlib
import json
import logging
import re
import shutil
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from .data_model import ChatCollection

try:
    from bs4 import BeautifulSoup

    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class CleaningStats:
    """Statistics for cleaning operations."""

    files_processed: int = 0
    total_messages_before: int = 0
    total_messages_after: int = 0
    duplicates_removed: int = 0
    system_messages_removed: int = 0
    filtered_by_date: int = 0
    media_references_cleaned: int = 0
    anonymized_items: int = 0
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def messages_removed(self) -> int:
        """Total messages removed."""
        return self.total_messages_before - self.total_messages_after

    @property
    def removal_percentage(self) -> float:
        """Percentage of messages removed."""
        if self.total_messages_before == 0:
            return 0.0
        return (self.messages_removed / self.total_messages_before) * 100


@dataclass
class CleaningConfig:
    """Configuration for chat cleaning operations."""

    # Duplicate removal
    remove_duplicates: bool = True
    duplicate_threshold_seconds: int = 60  # Consider duplicates within 60 seconds

    # Date filtering
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # System message removal
    remove_system_messages: bool = False
    system_message_patterns: List[str] = field(
        default_factory=lambda: [
            r"joined using this group's invite link",
            r"left",
            r"changed the group name",
            r"changed this group's icon",
            r"added",
            r"removed",
            r"You created group",
            r"Messages and calls are end-to-end encrypted",
            r"changed their phone number",
            r"security code changed",
        ]
    )

    # Anonymization
    anonymize_names: bool = False
    anonymize_phones: bool = False
    anonymize_emails: bool = False
    preserve_structure: bool = True  # Keep message structure when anonymizing

    # Media cleaning
    clean_broken_media: bool = False
    validate_media_paths: bool = False
    media_base_path: Optional[str] = None

    # Output settings
    create_backup: bool = True
    output_format: str = "html"  # html, json, txt
    preserve_timestamps: bool = True

    # Performance
    batch_size: int = 1000
    max_memory_mb: int = 512


@dataclass
class MessageData:
    """Structured message data for processing."""

    timestamp: datetime
    sender: str
    content: str
    message_type: str = "text"  # text, system, media
    media_path: Optional[str] = None
    original_html: str = ""
    hash_content: str = ""  # For duplicate detection

    def __post_init__(self):
        """Generate content hash for duplicate detection."""
        if not self.hash_content:
            # Create hash from sender + content + approximate time
            time_rounded = self.timestamp.replace(second=0, microsecond=0)
            hash_data = f"{self.sender}:{self.content}:{time_rounded}"
            self.hash_content = hashlib.md5(hash_data.encode()).hexdigest()


class ChatCleaner:
    """Advanced WhatsApp chat cleaning tool."""

    def __init__(self, config: CleaningConfig):
        """Initialize the chat cleaner."""
        self.config = config
        self.stats = CleaningStats()
        self.setup_logging()

        # Processing state
        self.seen_hashes: Set[str] = set()
        self.anonymization_map: Dict[str, str] = {}
        self.name_counter = 1
        self.phone_counter = 1
        self.email_counter = 1

        # Compiled patterns for performance
        self.system_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.config.system_message_patterns
        ]

        # Privacy patterns
        self.phone_pattern = re.compile(r"\+?[\d\s\-\(\)]{10,}")
        self.email_pattern = re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        )

    @staticmethod
    def clean(collection: "ChatCollection") -> None:
        """Simplified cleaner for :class:`ChatCollection`.

        This helper removes empty messages, deduplicates by content and
        timestamp, and drops chats left empty. It preserves order and
        mutates ``collection`` in place.
        """
        for chat_id in list(collection.keys()):
            chat = collection.get_chat(chat_id)
            if chat is None:
                continue

            seen: set[tuple[str | None, float]] = set()
            to_remove: list[str] = []
            for key in list(chat.keys()):
                msg = chat.get_message(key)
                if msg is None:
                    continue

                if msg.data is None or msg.data == "":
                    to_remove.append(key)
                    continue

                identifier = (str(msg.data), float(msg.timestamp))
                if identifier in seen:
                    to_remove.append(key)
                else:
                    seen.add(identifier)

            for key in to_remove:
                chat.delete_message(key)

            if len(chat) == 0:
                collection.remove_chat(chat_id)

    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        self.logger = logging.getLogger(__name__)

    def clean_file(self, input_path: str, output_path: Optional[str] = None) -> bool:
        """Clean a single chat file."""
        start_time = time.time()

        try:
            input_file = Path(input_path)
            if not input_file.exists():
                self.logger.error(f"Input file not found: {input_path}")
                return False

            # Determine output path
            if output_path is None:
                output_path = self._generate_output_path(input_path)

            # Create backup if requested
            if self.config.create_backup:
                self._create_backup(input_path)

            # Process the file
            success = self._process_chat_file(input_path, output_path)

            self.stats.processing_time = time.time() - start_time
            self.stats.files_processed += 1

            return success

        except Exception as e:
            self.logger.error(f"Error cleaning file {input_path}: {e}")
            self.stats.errors.append(f"File {input_path}: {str(e)}")
            return False

    def clean_directory(self, input_dir: str, output_dir: Optional[str] = None) -> bool:
        """Clean all chat files in a directory."""
        try:
            input_path = Path(input_dir)
            if not input_path.is_dir():
                self.logger.error(f"Input directory not found: {input_dir}")
                return False

            # Find all chat files
            chat_files = []
            for ext in [".html", ".htm", ".json", ".txt"]:
                chat_files.extend(input_path.glob(f"*{ext}"))

            if not chat_files:
                self.logger.warning(f"No chat files found in {input_dir}")
                return False

            self.logger.info(f"Found {len(chat_files)} chat files to process")

            # Setup output directory
            if output_dir is None:
                output_dir = str(input_path / "cleaned_chats")

            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)

            # Process files
            success_count = 0
            for chat_file in chat_files:
                output_file = output_path / f"cleaned_{chat_file.name}"
                if self.clean_file(str(chat_file), str(output_file)):
                    success_count += 1

            self.logger.info(
                f"Successfully processed {success_count}/{len(chat_files)} files"
            )
            return success_count > 0

        except Exception as e:
            self.logger.error(f"Error cleaning directory {input_dir}: {e}")
            return False

    def _process_chat_file(self, input_path: str, output_path: str) -> bool:
        """Process a single chat file with all cleaning operations."""
        try:
            # Detect file format and parse
            file_ext = Path(input_path).suffix.lower()

            if file_ext in [".html", ".htm"]:
                messages = self._parse_html_chat(input_path)
            elif file_ext == ".json":
                messages = self._parse_json_chat(input_path)
            elif file_ext == ".txt":
                messages = self._parse_text_chat(input_path)
            else:
                self.logger.error(f"Unsupported file format: {file_ext}")
                return False

            if not messages:
                self.logger.warning(f"No messages found in {input_path}")
                return False

            self.stats.total_messages_before += len(messages)
            self.logger.info(f"Loaded {len(messages)} messages from {input_path}")

            # Apply cleaning operations
            cleaned_messages = self._apply_cleaning_operations(messages)

            self.stats.total_messages_after += len(cleaned_messages)
            self.logger.info(f"After cleaning: {len(cleaned_messages)} messages remain")

            # Save cleaned chat
            return self._save_cleaned_chat(cleaned_messages, output_path, file_ext)

        except Exception as e:
            self.logger.error(f"Error processing {input_path}: {e}")
            self.stats.errors.append(f"Processing {input_path}: {str(e)}")
            return False

    def _parse_html_chat(self, file_path: str) -> List[MessageData]:
        """Parse HTML chat export."""
        if not BS4_AVAILABLE:
            raise ImportError(
                "BeautifulSoup4 required for HTML parsing: pip install beautifulsoup4"
            )

        messages = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            soup = BeautifulSoup(content, "html.parser")

            # Try different HTML structures
            message_elements = (
                soup.find_all("div", class_=re.compile(r"message|msg"))
                or soup.find_all("div", attrs={"data-testid": "msg"})
                or soup.find_all("div", class_="chat-message")
                or soup.find_all("p")  # Fallback
            )

            for element in message_elements:
                try:
                    message = self._extract_message_from_html(element)
                    if message:
                        messages.append(message)
                except Exception as e:
                    self.stats.warnings.append(f"Failed to parse message element: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error parsing HTML file {file_path}: {e}")
            raise

        return messages

    def _extract_message_from_html(self, element) -> Optional[MessageData]:
        """Extract message data from HTML element."""
        try:
            text_content = element.get_text().strip()
            if not text_content:
                return None

            # Try to extract timestamp, sender, and content
            # This is a simplified parser - would need adaptation for specific formats

            # Look for time patterns
            time_patterns = [
                r"(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)",
                r"(\d{1,2}/\d{1,2}/\d{2,4})",
                r"(\d{4}-\d{2}-\d{2})",
            ]

            timestamp = datetime.now()  # Default
            for pattern in time_patterns:
                time_match = re.search(pattern, text_content)
                if time_match:
                    try:
                        time_str = time_match.group(1)
                        # Try to parse different time formats
                        for fmt in ["%H:%M", "%I:%M %p", "%m/%d/%Y", "%Y-%m-%d"]:
                            try:
                                timestamp = datetime.strptime(time_str, fmt)
                                break
                            except ValueError:
                                continue
                    except:
                        pass
                    break

            # Extract sender and content
            parts = text_content.split(":", 2)
            if len(parts) >= 2:
                sender = parts[0].strip()
                content = ":".join(parts[1:]).strip()
            else:
                sender = "Unknown"
                content = text_content

            # Determine message type
            message_type = "text"
            if any(pattern.search(content) for pattern in self.system_patterns):
                message_type = "system"
            elif any(
                media_indicator in content.lower()
                for media_indicator in [
                    "<Media omitted>",
                    "image",
                    "video",
                    "audio",
                    "document",
                ]
            ):
                message_type = "media"

            return MessageData(
                timestamp=timestamp,
                sender=sender,
                content=content,
                message_type=message_type,
                original_html=str(element),
            )

        except Exception as e:
            self.logger.debug(f"Error extracting message: {e}")
            return None

    def _parse_json_chat(self, file_path: str) -> List[MessageData]:
        """Parse JSON chat export."""
        messages = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Handle different JSON structures
            if isinstance(data, list):
                message_list = data
            elif isinstance(data, dict):
                message_list = data.get("messages", data.get("chat", []))
            else:
                raise ValueError("Unsupported JSON structure")

            for msg_data in message_list:
                try:
                    timestamp = datetime.fromisoformat(msg_data.get("timestamp", ""))
                except:
                    timestamp = datetime.now()

                message = MessageData(
                    timestamp=timestamp,
                    sender=msg_data.get("sender", msg_data.get("from", "Unknown")),
                    content=msg_data.get("text", msg_data.get("content", "")),
                    message_type=msg_data.get("type", "text"),
                    media_path=msg_data.get("media_path"),
                )
                messages.append(message)

        except Exception as e:
            self.logger.error(f"Error parsing JSON file {file_path}: {e}")
            raise

        return messages

    def _parse_text_chat(self, file_path: str) -> List[MessageData]:
        """Parse plain text chat export."""
        messages = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Try to parse WhatsApp text format: [date, time] sender: message
                match = re.match(
                    r"\[?(\d{1,2}/\d{1,2}/\d{2,4}),?\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)\]?\s*([^:]+):\s*(.*)",
                    line,
                )

                if match:
                    date_str, time_str, sender, content = match.groups()

                    try:
                        # Combine date and time
                        datetime_str = f"{date_str} {time_str}"
                        for fmt in [
                            "%m/%d/%Y %H:%M",
                            "%m/%d/%Y %I:%M %p",
                            "%d/%m/%Y %H:%M",
                        ]:
                            try:
                                timestamp = datetime.strptime(datetime_str, fmt)
                                break
                            except ValueError:
                                continue
                        else:
                            timestamp = datetime.now()
                    except:
                        timestamp = datetime.now()

                    message_type = "text"
                    if any(pattern.search(content) for pattern in self.system_patterns):
                        message_type = "system"

                    message = MessageData(
                        timestamp=timestamp,
                        sender=sender.strip(),
                        content=content.strip(),
                        message_type=message_type,
                    )
                    messages.append(message)

        except Exception as e:
            self.logger.error(f"Error parsing text file {file_path}: {e}")
            raise

        return messages

    def _apply_cleaning_operations(
        self, messages: List[MessageData]
    ) -> List[MessageData]:
        """Apply all configured cleaning operations to messages."""
        cleaned_messages = messages.copy()

        self.logger.info("Applying cleaning operations...")

        # 1. Remove duplicates
        if self.config.remove_duplicates:
            cleaned_messages = self._remove_duplicates(cleaned_messages)

        # 2. Filter by date range
        if self.config.start_date or self.config.end_date:
            cleaned_messages = self._filter_by_date(cleaned_messages)

        # 3. Remove system messages
        if self.config.remove_system_messages:
            cleaned_messages = self._remove_system_messages(cleaned_messages)

        # 4. Clean media references
        if self.config.clean_broken_media:
            cleaned_messages = self._clean_media_references(cleaned_messages)

        # 5. Anonymize content
        if (
            self.config.anonymize_names
            or self.config.anonymize_phones
            or self.config.anonymize_emails
        ):
            cleaned_messages = self._anonymize_content(cleaned_messages)

        return cleaned_messages

    def _remove_duplicates(self, messages: List[MessageData]) -> List[MessageData]:
        """Remove duplicate messages based on content and timing."""
        if not messages:
            return messages

        self.logger.info("Removing duplicate messages...")

        # Sort messages by timestamp for efficient processing
        sorted_messages = sorted(messages, key=lambda m: m.timestamp)
        unique_messages = []
        seen_exact = set()

        for message in sorted_messages:
            # Check for exact duplicates first
            exact_key = f"{message.sender}:{message.content}:{message.timestamp}"
            if exact_key in seen_exact:
                self.stats.duplicates_removed += 1
                continue

            # Check for near-duplicates within time threshold
            is_duplicate = False
            for existing in reversed(
                unique_messages[-10:]
            ):  # Check last 10 messages for performance
                time_diff = abs(
                    (message.timestamp - existing.timestamp).total_seconds()
                )

                if (
                    time_diff <= self.config.duplicate_threshold_seconds
                    and message.sender == existing.sender
                    and self._messages_similar(message.content, existing.content)
                ):
                    is_duplicate = True
                    self.stats.duplicates_removed += 1
                    break

            if not is_duplicate:
                unique_messages.append(message)
                seen_exact.add(exact_key)

        self.logger.info(f"Removed {self.stats.duplicates_removed} duplicate messages")
        return unique_messages

    def _messages_similar(
        self, content1: str, content2: str, similarity_threshold: float = 0.9
    ) -> bool:
        """Check if two message contents are similar enough to be considered duplicates."""
        if content1 == content2:
            return True

        # Simple similarity check based on character overlap
        if len(content1) == 0 or len(content2) == 0:
            return False

        # Normalize content
        norm1 = re.sub(r"\s+", " ", content1.lower().strip())
        norm2 = re.sub(r"\s+", " ", content2.lower().strip())

        if norm1 == norm2:
            return True

        # Check character overlap
        set1 = set(norm1)
        set2 = set(norm2)

        if len(set1.union(set2)) == 0:
            return False

        overlap = len(set1.intersection(set2))
        similarity = overlap / len(set1.union(set2))

        return similarity >= similarity_threshold

    def _filter_by_date(self, messages: List[MessageData]) -> List[MessageData]:
        """Filter messages by date range."""
        if not (self.config.start_date or self.config.end_date):
            return messages

        self.logger.info(
            f"Filtering messages by date range: {self.config.start_date} to {self.config.end_date}"
        )

        filtered_messages = []

        for message in messages:
            include_message = True

            if self.config.start_date and message.timestamp < self.config.start_date:
                include_message = False
                self.stats.filtered_by_date += 1

            if self.config.end_date and message.timestamp > self.config.end_date:
                include_message = False
                self.stats.filtered_by_date += 1

            if include_message:
                filtered_messages.append(message)

        self.logger.info(f"Filtered out {self.stats.filtered_by_date} messages by date")
        return filtered_messages

    def _remove_system_messages(self, messages: List[MessageData]) -> List[MessageData]:
        """Remove system and notification messages."""
        self.logger.info("Removing system messages...")

        filtered_messages = []

        for message in messages:
            is_system = message.message_type == "system" or any(
                pattern.search(message.content) for pattern in self.system_patterns
            )

            if is_system:
                self.stats.system_messages_removed += 1
            else:
                filtered_messages.append(message)

        self.logger.info(
            f"Removed {self.stats.system_messages_removed} system messages"
        )
        return filtered_messages

    def _clean_media_references(self, messages: List[MessageData]) -> List[MessageData]:
        """Clean and validate media references."""
        if not self.config.clean_broken_media:
            return messages

        self.logger.info("Cleaning media references...")

        for message in messages:
            if message.media_path:
                # Check if media file exists
                if self.config.media_base_path:
                    full_path = Path(self.config.media_base_path) / message.media_path
                    if not full_path.exists():
                        message.media_path = None
                        message.content = f"{message.content} [Media file not found]"
                        self.stats.media_references_cleaned += 1

            # Clean broken media references in content
            media_patterns = [
                r"<Media omitted>",
                r"\[Media file not available\]",
                r"\[Image not available\]",
                r"\[Video not available\]",
                r"\[Audio not available\]",
                r"\[Document not available\]",
            ]

            for pattern in media_patterns:
                if re.search(pattern, message.content, re.IGNORECASE):
                    message.content = re.sub(
                        pattern, "[Media]", message.content, flags=re.IGNORECASE
                    )
                    self.stats.media_references_cleaned += 1

        self.logger.info(
            f"Cleaned {self.stats.media_references_cleaned} media references"
        )
        return messages

    def _anonymize_content(self, messages: List[MessageData]) -> List[MessageData]:
        """Anonymize personal information in messages."""
        self.logger.info("Anonymizing personal information...")

        for message in messages:
            # Anonymize sender names
            if self.config.anonymize_names:
                message.sender = self._anonymize_name(message.sender)

            # Anonymize content
            content = message.content

            if self.config.anonymize_phones:
                content = self._anonymize_phones(content)

            if self.config.anonymize_emails:
                content = self._anonymize_emails(content)

            if self.config.anonymize_names:
                content = self._anonymize_names_in_content(content)

            if content != message.content:
                message.content = content
                self.stats.anonymized_items += 1

        self.logger.info(f"Anonymized {self.stats.anonymized_items} items")
        return messages

    def _anonymize_name(self, name: str) -> str:
        """Anonymize a person's name consistently."""
        if name in self.anonymization_map:
            return self.anonymization_map[name]

        if self.config.preserve_structure:
            # Preserve name structure (first/last names)
            parts = name.split()
            if len(parts) == 1:
                anonymous_name = f"Person{self.name_counter}"
            elif len(parts) == 2:
                anonymous_name = (
                    f"Person{self.name_counter}_A Person{self.name_counter}_B"
                )
            else:
                anonymous_name = f"Person{self.name_counter}_{'_'.join([f'N{i}' for i in range(len(parts))])}"
        else:
            anonymous_name = f"Person{self.name_counter}"

        self.anonymization_map[name] = anonymous_name
        self.name_counter += 1

        return anonymous_name

    def _anonymize_phones(self, content: str) -> str:
        """Anonymize phone numbers in content."""

        def replace_phone(match):
            phone = match.group(0)
            if phone not in self.anonymization_map:
                self.anonymization_map[phone] = f"+1-555-{self.phone_counter:04d}"
                self.phone_counter += 1
            return self.anonymization_map[phone]

        return self.phone_pattern.sub(replace_phone, content)

    def _anonymize_emails(self, content: str) -> str:
        """Anonymize email addresses in content."""

        def replace_email(match):
            email = match.group(0)
            if email not in self.anonymization_map:
                domain = email.split("@")[1] if "@" in email else "example.com"
                self.anonymization_map[email] = f"user{self.email_counter}@{domain}"
                self.email_counter += 1
            return self.anonymization_map[email]

        return self.email_pattern.sub(replace_email, content)

    def _anonymize_names_in_content(self, content: str) -> str:
        """Anonymize person names mentioned in message content."""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated NLP for name recognition

        # Replace names that are already in the anonymization map
        for original_name, anonymous_name in self.anonymization_map.items():
            if original_name in content:
                content = content.replace(original_name, anonymous_name)

        return content

    def _save_cleaned_chat(
        self, messages: List[MessageData], output_path: str, original_format: str
    ) -> bool:
        """Save cleaned messages to file."""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            if self.config.output_format == "json":
                return self._save_as_json(messages, output_path)
            elif self.config.output_format == "txt":
                return self._save_as_text(messages, output_path)
            elif self.config.output_format == "html":
                return self._save_as_html(messages, output_path)
            else:
                # Default to original format
                if original_format in [".html", ".htm"]:
                    return self._save_as_html(messages, output_path)
                elif original_format == ".json":
                    return self._save_as_json(messages, output_path)
                else:
                    return self._save_as_text(messages, output_path)

        except Exception as e:
            self.logger.error(f"Error saving cleaned chat: {e}")
            return False

    def _save_as_html(self, messages: List[MessageData], output_path: str) -> bool:
        """Save messages as HTML format."""
        try:
            html_content = self._generate_html_content(messages)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            self.logger.info(f"Saved cleaned chat as HTML: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving HTML: {e}")
            return False

    def _save_as_json(self, messages: List[MessageData], output_path: str) -> bool:
        """Save messages as JSON format."""
        try:
            json_data = {
                "metadata": {
                    "total_messages": len(messages),
                    "export_time": datetime.now().isoformat(),
                    "cleaning_stats": asdict(self.stats),
                },
                "messages": [
                    {
                        "timestamp": msg.timestamp.isoformat(),
                        "sender": msg.sender,
                        "content": msg.content,
                        "type": msg.message_type,
                        "media_path": msg.media_path,
                    }
                    for msg in messages
                ],
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved cleaned chat as JSON: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving JSON: {e}")
            return False

    def _save_as_text(self, messages: List[MessageData], output_path: str) -> bool:
        """Save messages as plain text format."""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("# Cleaned WhatsApp Chat Export\n")
                f.write(f"# Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Total messages: {len(messages)}\n\n")

                for message in messages:
                    timestamp_str = message.timestamp.strftime("%m/%d/%Y, %H:%M")
                    f.write(f"[{timestamp_str}] {message.sender}: {message.content}\n")

            self.logger.info(f"Saved cleaned chat as text: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving text: {e}")
            return False

    def _generate_html_content(self, messages: List[MessageData]) -> str:
        """Generate clean HTML content for messages."""
        html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cleaned WhatsApp Chat</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f0f0f0; }}
        .chat-container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; padding: 20px; }}
        .message {{ margin: 10px 0; padding: 10px; border-radius: 8px; }}
        .message.text {{ background-color: #e3f2fd; }}
        .message.media {{ background-color: #f3e5f5; }}
        .message.system {{ background-color: #f5f5f5; font-style: italic; }}
        .timestamp {{ font-size: 0.8em; color: #666; }}
        .sender {{ font-weight: bold; color: #1976d2; }}
        .content {{ margin-top: 5px; }}
        .stats {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="stats">
            <h3>📊 Cleaning Statistics</h3>
            <p><strong>Total messages:</strong> {total_messages}</p>
            <p><strong>Messages removed:</strong> {messages_removed} ({removal_percentage:.1f}%)</p>
            <p><strong>Duplicates removed:</strong> {duplicates_removed}</p>
            <p><strong>System messages removed:</strong> {system_messages_removed}</p>
            <p><strong>Processing time:</strong> {processing_time:.2f} seconds</p>
        </div>

        <div class="messages">
{message_content}
        </div>
    </div>
</body>
</html>"""

        message_html_parts = []
        for message in messages:
            timestamp_str = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")

            message_html = f"""            <div class="message {message.message_type}">
                <div class="timestamp">{timestamp_str}</div>
                <div class="sender">{self._escape_html(message.sender)}</div>
                <div class="content">{self._escape_html(message.content)}</div>
            </div>"""

            message_html_parts.append(message_html)

        return html_template.format(
            total_messages=len(messages),
            messages_removed=self.stats.messages_removed,
            removal_percentage=self.stats.removal_percentage,
            duplicates_removed=self.stats.duplicates_removed,
            system_messages_removed=self.stats.system_messages_removed,
            processing_time=self.stats.processing_time,
            message_content="\n".join(message_html_parts),
        )

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )

    def _generate_output_path(self, input_path: str) -> str:
        """Generate output path for cleaned file."""
        input_file = Path(input_path)
        return str(input_file.parent / f"cleaned_{input_file.name}")

    def _create_backup(self, file_path: str) -> None:
        """Create backup of original file."""
        try:
            input_file = Path(file_path)
            backup_path = (
                input_file.parent / f"{input_file.stem}_backup{input_file.suffix}"
            )
            shutil.copy2(file_path, backup_path)
            self.logger.info(f"Backup created: {backup_path}")
        except Exception as e:
            self.logger.warning(f"Failed to create backup: {e}")

    def get_stats(self) -> CleaningStats:
        """Get cleaning statistics."""
        return self.stats

    def print_summary(self) -> None:
        """Print summary of cleaning operations."""
        print("\n" + "=" * 60)
        print("🧹 CHAT CLEANING SUMMARY")
        print("=" * 60)
        print(f"📁 Files processed: {self.stats.files_processed}")
        print(f"💬 Messages before: {self.stats.total_messages_before:,}")
        print(f"💬 Messages after: {self.stats.total_messages_after:,}")
        print(
            f"🗑️  Messages removed: {self.stats.messages_removed:,} ({self.stats.removal_percentage:.1f}%)"
        )
        print(f"🔄 Duplicates removed: {self.stats.duplicates_removed:,}")
        print(f"🤖 System messages removed: {self.stats.system_messages_removed:,}")
        print(f"📅 Filtered by date: {self.stats.filtered_by_date:,}")
        print(f"🎭 Items anonymized: {self.stats.anonymized_items:,}")
        print(f"⏱️  Processing time: {self.stats.processing_time:.2f} seconds")

        if self.stats.errors:
            print(f"\n❌ Errors ({len(self.stats.errors)}):")
            for error in self.stats.errors[:5]:  # Show first 5 errors
                print(f"  • {error}")
            if len(self.stats.errors) > 5:
                print(f"  • ... and {len(self.stats.errors) - 5} more errors")

        if self.stats.warnings:
            print(f"\n⚠️  Warnings ({len(self.stats.warnings)}):")
            for warning in self.stats.warnings[:5]:  # Show first 5 warnings
                print(f"  • {warning}")
            if len(self.stats.warnings) > 5:
                print(f"  • ... and {len(self.stats.warnings) - 5} more warnings")

        print("=" * 60)


def create_default_config() -> CleaningConfig:
    """Create default cleaning configuration."""
    return CleaningConfig()


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string in various formats."""
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(
        description="WhatsApp Chat Cleaner - Clean and process WhatsApp chat exports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic cleaning with duplicate removal
  python chat_cleaner.py input.html

  # Clean with anonymization
  python chat_cleaner.py input.html --anonymize-names --anonymize-phones

  # Remove system messages and filter by date
  python chat_cleaner.py input.html --remove-system --start-date 2024-01-01 --end-date 2024-12-31

  # Clean entire directory
  python chat_cleaner.py /path/to/chats --directory --output /path/to/cleaned

  # Advanced cleaning with custom configuration
  python chat_cleaner.py input.html --output-format json --no-backup --duplicate-threshold 30

Supported Formats:
  Input:  .html, .htm, .json, .txt
  Output: .html, .json, .txt
        """,
    )

    # Input/Output options
    parser.add_argument("input", help="Input chat file or directory")
    parser.add_argument(
        "-o", "--output", help="Output file or directory (default: auto-generated)"
    )
    parser.add_argument(
        "-d", "--directory", action="store_true", help="Process entire directory"
    )
    parser.add_argument(
        "--output-format",
        choices=["html", "json", "txt"],
        help="Output format (default: same as input)",
    )

    # Duplicate removal options
    parser.add_argument(
        "--no-duplicates",
        action="store_false",
        dest="remove_duplicates",
        help="Disable duplicate removal",
    )
    parser.add_argument(
        "--duplicate-threshold",
        type=int,
        default=60,
        help="Duplicate detection threshold in seconds (default: 60)",
    )

    # Date filtering options
    parser.add_argument(
        "--start-date", type=str, help="Start date (YYYY-MM-DD or MM/DD/YYYY)"
    )
    parser.add_argument(
        "--end-date", type=str, help="End date (YYYY-MM-DD or MM/DD/YYYY)"
    )

    # System message options
    parser.add_argument(
        "--remove-system",
        action="store_true",
        help="Remove system messages and notifications",
    )

    # Anonymization options
    parser.add_argument(
        "--anonymize-names", action="store_true", help="Anonymize person names"
    )
    parser.add_argument(
        "--anonymize-phones", action="store_true", help="Anonymize phone numbers"
    )
    parser.add_argument(
        "--anonymize-emails", action="store_true", help="Anonymize email addresses"
    )
    parser.add_argument(
        "--preserve-structure",
        action="store_true",
        default=True,
        help="Preserve name structure when anonymizing",
    )

    # Media cleaning options
    parser.add_argument(
        "--clean-media", action="store_true", help="Clean broken media references"
    )
    parser.add_argument(
        "--media-path", type=str, help="Base path for media files validation"
    )

    # Backup and safety options
    parser.add_argument(
        "--no-backup",
        action="store_false",
        dest="create_backup",
        help="Don't create backup of original files",
    )

    # Performance options
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Processing batch size (default: 1000)",
    )
    parser.add_argument(
        "--max-memory",
        type=int,
        default=512,
        help="Maximum memory usage in MB (default: 512)",
    )

    # Output options
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress output except errors"
    )
    parser.add_argument("--stats", action="store_true", help="Show detailed statistics")

    args = parser.parse_args()

    # Setup logging
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    # Validate input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Error: Input path not found: {args.input}")
        return 1

    if args.directory and not input_path.is_dir():
        print(
            f"❌ Error: Directory flag specified but input is not a directory: {args.input}"
        )
        return 1

    # Parse dates
    start_date = None
    end_date = None

    if args.start_date:
        start_date = parse_date(args.start_date)
        if not start_date:
            print(f"❌ Error: Invalid start date format: {args.start_date}")
            return 1

    if args.end_date:
        end_date = parse_date(args.end_date)
        if not end_date:
            print(f"❌ Error: Invalid end date format: {args.end_date}")
            return 1

    if start_date and end_date and start_date > end_date:
        print("❌ Error: Start date must be before end date")
        return 1

    # Create configuration
    config = CleaningConfig(
        remove_duplicates=args.remove_duplicates,
        duplicate_threshold_seconds=args.duplicate_threshold,
        start_date=start_date,
        end_date=end_date,
        remove_system_messages=args.remove_system,
        anonymize_names=args.anonymize_names,
        anonymize_phones=args.anonymize_phones,
        anonymize_emails=args.anonymize_emails,
        preserve_structure=args.preserve_structure,
        clean_broken_media=args.clean_media,
        media_base_path=args.media_path,
        create_backup=args.create_backup,
        output_format=args.output_format,
        batch_size=args.batch_size,
        max_memory_mb=args.max_memory,
    )

    # Initialize cleaner
    try:
        cleaner = ChatCleaner(config)

        print("🧹 WhatsApp Chat Cleaner")
        print("=" * 50)

        if not args.quiet:
            print(f"📁 Input: {args.input}")
            if args.output:
                print(f"📂 Output: {args.output}")

            # Show configuration
            print("\n⚙️ Configuration:")
            print(f"  • Remove duplicates: {config.remove_duplicates}")
            if config.remove_duplicates:
                print(f"    - Threshold: {config.duplicate_threshold_seconds}s")

            if config.start_date or config.end_date:
                print(
                    f"  • Date filter: {config.start_date or 'any'} to {config.end_date or 'any'}"
                )

            print(f"  • Remove system messages: {config.remove_system_messages}")

            if (
                config.anonymize_names
                or config.anonymize_phones
                or config.anonymize_emails
            ):
                print("  • Anonymization:")
                if config.anonymize_names:
                    print("    - Names")
                if config.anonymize_phones:
                    print("    - Phone numbers")
                if config.anonymize_emails:
                    print("    - Email addresses")

            print(f"  • Create backup: {config.create_backup}")
            print(f"  • Output format: {config.output_format}")

        # Process files
        print("\n🚀 Starting cleaning process...")
        start_time = time.time()

        if args.directory:
            success = cleaner.clean_directory(args.input, args.output)
        else:
            success = cleaner.clean_file(args.input, args.output)

        total_time = time.time() - start_time

        # Show results
        if success:
            print(f"\n✅ Cleaning completed in {total_time:.2f} seconds")

            if args.stats or args.verbose:
                cleaner.print_summary()
            else:
                stats = cleaner.get_stats()
                print(
                    f"📊 Summary: {stats.total_messages_before:,} → {stats.total_messages_after:,} messages "
                    f"({stats.removal_percentage:.1f}% removed)"
                )
                if stats.duplicates_removed:
                    print(f"🔄 Removed {stats.duplicates_removed:,} duplicates")
                if stats.system_messages_removed:
                    print(
                        f"🤖 Removed {stats.system_messages_removed:,} system messages"
                    )
                if stats.anonymized_items:
                    print(f"🎭 Anonymized {stats.anonymized_items:,} items")

            return 0
        else:
            print("\n❌ Cleaning failed")
            if not args.quiet:
                cleaner.print_summary()
            return 1

    except KeyboardInterrupt:
        print("\n⚠️ Cleaning interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
