"""
Advanced methods for the ContentAnalyzer
This file contains the advanced methods that will be integrated into the main analyzer.
"""
import json
import time
import hashlib
import logging
import sqlite3
from pathlib import Path
from typing import Optional, Dict, List, Tuple

def setup_advanced_logging(self):
    """Set up advanced logging with multiple levels and outputs."""
    from datetime import datetime

    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Configure advanced logging
    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    )

    # Main logger
    self.logger = logging.getLogger(f"ContentAnalyzer.{id(self)}")
    self.logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)

    # File handler for all logs
    log_file = logs_dir / f"analyzer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)

    # Error handler for critical issues
    error_file = logs_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.FileHandler(error_file, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)

    # Clear existing handlers
    self.logger.handlers.clear()

    # Add handlers
    self.logger.addHandler(console_handler)
    self.logger.addHandler(file_handler)
    self.logger.addHandler(error_handler)

    self.logger.info("Advanced logging system initialized")


def _load_configuration(self, config_file: Optional[str]) -> AnalysisConfig:
    """Load configuration from file or create default."""
    if config_file and Path(config_file).exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            return AnalysisConfig(
                keywords=config_data.get("keywords", []),
                use_regex=config_data.get("use_regex", False),
                case_sensitive=config_data.get("case_sensitive", False),
                date_from=config_data.get("date_from"),
                date_to=config_data.get("date_to"),
                participants_filter=config_data.get("participants_filter", []),
                sentiment_analysis=config_data.get("sentiment_analysis", False),
                language_detection=config_data.get("language_detection", False),
                topic_extraction=config_data.get("topic_extraction", False),
                anonymize_data=config_data.get("anonymize_data", False),
                encrypt_output=config_data.get("encrypt_output", False),
                generate_excel=config_data.get("generate_excel", False),
                generate_pdf=config_data.get("generate_pdf", False),
                generate_dashboard=config_data.get("generate_dashboard", False),
                max_workers=config_data.get("max_workers"),
                use_cache=config_data.get("use_cache", True),
                cache_directory=config_data.get("cache_directory", ".cache"),
            )
        except Exception as e:
            self.logger.error(f"Error loading config file {config_file}: {e}")
            return AnalysisConfig(keywords=self._get_default_keywords())
    else:
        return AnalysisConfig(keywords=self._get_default_keywords())


def _init_cache_system(self):
    """Initialize SQLite-based caching system."""
    if not self.cache_enabled:
        self.cache_connection = None
        return

    try:
        # Create cache directory
        self.cache_db_path.parent.mkdir(exist_ok=True)

        # Connect to cache database
        self.cache_connection = sqlite3.connect(str(self.cache_db_path))
        self.cache_connection.execute(
            """
            CREATE TABLE IF NOT EXISTS file_cache (
                file_path TEXT PRIMARY KEY,
                file_hash TEXT NOT NULL,
                analysis_config_hash TEXT NOT NULL,
                result_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        self.cache_connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_file_hash ON file_cache(file_hash);
        """
        )

        self.cache_connection.commit()
        self.logger.info("Cache system initialized")

    except Exception as e:
        self.logger.error(f"Failed to initialize cache system: {e}")
        self.cache_enabled = False
        self.cache_connection = None


def _get_file_hash(self, file_path: str) -> str:
    """Calculate SHA256 hash of file for caching."""
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        self.logger.error(f"Failed to calculate hash for {file_path}: {e}")
        return ""


def _get_config_hash(self) -> str:
    """Calculate hash of current configuration for cache validation."""
    config_str = json.dumps(asdict(self.config), sort_keys=True)
    return hashlib.sha256(config_str.encode()).hexdigest()


def _get_cached_result(
    self, file_path: str, file_hash: str
) -> Optional[AdvancedAnalysisResult]:
    """Retrieve cached analysis result if available and valid."""
    if not self.cache_enabled or not self.cache_connection:
        return None

    try:
        config_hash = self._get_config_hash()
        cursor = self.cache_connection.execute(
            "SELECT result_data FROM file_cache WHERE file_path = ? AND file_hash = ? AND analysis_config_hash = ?",
            (file_path, file_hash, config_hash),
        )

        row = cursor.fetchone()
        if row:
            # Update accessed time
            self.cache_connection.execute(
                "UPDATE file_cache SET accessed_at = CURRENT_TIMESTAMP WHERE file_path = ?",
                (file_path,),
            )
            self.cache_connection.commit()

            # Deserialize result
            result_data = json.loads(row[0])
            return AdvancedAnalysisResult(**result_data)

    except Exception as e:
        self.logger.error(f"Failed to retrieve cached result for {file_path}: {e}")

    return None


def _cache_result(self, file_path: str, file_hash: str, result: AdvancedAnalysisResult):
    """Cache analysis result for future use."""
    if not self.cache_enabled or not self.cache_connection:
        return

    try:
        config_hash = self._get_config_hash()
        result_data = json.dumps(asdict(result), ensure_ascii=False)

        self.cache_connection.execute(
            """
            INSERT OR REPLACE INTO file_cache 
            (file_path, file_hash, analysis_config_hash, result_data)
            VALUES (?, ?, ?, ?)
        """,
            (file_path, file_hash, config_hash, result_data),
        )

        self.cache_connection.commit()
        self.logger.debug(f"Cached result for {file_path}")

    except Exception as e:
        self.logger.error(f"Failed to cache result for {file_path}: {e}")


def _init_sentiment_analyzer(self):
    """Initialize sentiment analysis capabilities."""
    self.sentiment_analyzer = None
    if SENTIMENT_AVAILABLE and self.config.sentiment_analysis:
        try:
            # TextBlob is ready to use out of the box
            self.sentiment_analyzer = TextBlob
            self.logger.info("Sentiment analysis enabled")
        except Exception as e:
            self.logger.error(f"Failed to initialize sentiment analyzer: {e}")


def _init_topic_extractor(self):
    """Initialize topic extraction capabilities."""
    self.topic_extractor = None
    if self.config.topic_extraction:
        try:
            # Simple keyword-based topic extraction for now
            # Could be enhanced with NLP libraries like spaCy or NLTK
            self.topic_keywords = {
                "work": [
                    "work",
                    "job",
                    "office",
                    "meeting",
                    "project",
                    "deadline",
                    "boss",
                ],
                "family": [
                    "mom",
                    "dad",
                    "sister",
                    "brother",
                    "family",
                    "home",
                    "parents",
                ],
                "social": [
                    "party",
                    "friends",
                    "fun",
                    "weekend",
                    "hangout",
                    "celebration",
                ],
                "travel": [
                    "trip",
                    "vacation",
                    "travel",
                    "flight",
                    "hotel",
                    "beach",
                    "airport",
                ],
                "food": [
                    "dinner",
                    "lunch",
                    "restaurant",
                    "food",
                    "eat",
                    "cooking",
                    "recipe",
                ],
                "health": [
                    "doctor",
                    "hospital",
                    "medicine",
                    "sick",
                    "health",
                    "exercise",
                ],
                "education": [
                    "school",
                    "study",
                    "exam",
                    "university",
                    "class",
                    "homework",
                ],
                "technology": [
                    "phone",
                    "computer",
                    "app",
                    "software",
                    "internet",
                    "tech",
                ],
            }
            self.logger.info("Topic extraction enabled")
        except Exception as e:
            self.logger.error(f"Failed to initialize topic extractor: {e}")


def _compile_patterns(self):
    """Compile all search patterns for efficient matching."""
    try:
        self.keyword_patterns = {}
        regex_patterns = []

        for keyword in self.config.keywords:
            if self.config.use_regex:
                try:
                    flags = 0 if self.config.case_sensitive else re.IGNORECASE
                    pattern = re.compile(keyword, flags)
                    self.keyword_patterns[keyword] = pattern
                    regex_patterns.append(keyword)
                except re.error as e:
                    self.logger.error(f"Invalid regex pattern '{keyword}': {e}")
                    continue
            else:
                escaped = re.escape(keyword)
                flags = 0 if self.config.case_sensitive else re.IGNORECASE
                pattern = re.compile(rf"\b{escaped}\b", flags)
                self.keyword_patterns[keyword] = pattern
                regex_patterns.append(rf"\b{escaped}\b")

        # Create combined pattern for faster processing
        if regex_patterns:
            combined_pattern_str = "|".join(
                f"({pattern})" for pattern in regex_patterns
            )
            flags = 0 if self.config.case_sensitive else re.IGNORECASE
            self.combined_pattern = re.compile(combined_pattern_str, flags)

        self.logger.info(f"Compiled {len(self.keyword_patterns)} search patterns")

    except Exception as e:
        self.logger.error(f"Failed to compile patterns: {e}")


@retry_on_failure(max_retries=3)
def _extract_advanced_text_info(self, file_path: str) -> Tuple[str, dict]:
    """Extract text and metadata with advanced parsing."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        metadata = {
            "total_messages": 0,
            "participants": set(),
            "date_range": [None, None],
            "message_frequency": {},
            "media_count": {"photos": 0, "videos": 0, "documents": 0, "audio": 0},
            "word_count": 0,
        }

        # Use lxml if available for faster parsing
        if LXML_AVAILABLE:
            text, meta = self._extract_with_advanced_lxml(content)
        else:
            text, meta = self._extract_with_advanced_bs4(content)

        metadata.update(meta)
        metadata["word_count"] = len(text.split())

        return text, metadata

    except Exception as e:
        self.logger.error(f"Failed to extract text from {file_path}: {e}")
        return "", {}


def _extract_with_advanced_lxml(self, content: str) -> Tuple[str, dict]:
    """Advanced extraction using lxml with metadata collection."""
    tree = html.fromstring(content)
    metadata = {
        "total_messages": 0,
        "participants": set(),
        "date_range": [None, None],
        "message_frequency": {},
        "media_count": {"photos": 0, "videos": 0, "documents": 0, "audio": 0},
    }

    # Remove script and style elements
    for elem in tree.xpath("//script | //style"):
        elem.getparent().remove(elem)

    # Extract text content
    text = tree.text_content()

    # Try to extract message metadata
    # This would need to be adapted based on WhatsApp export format
    message_elements = tree.xpath('//div[contains(@class, "message")]')
    metadata["total_messages"] = len(message_elements)

    # Extract participants and timestamps (format-dependent)
    for elem in message_elements:
        elem_text = elem.text_content()
        # Look for timestamp patterns
        timestamp_match = re.search(
            r"\d{1,2}/\d{1,2}/\d{2,4},?\s+\d{1,2}:\d{2}", elem_text
        )
        if timestamp_match:
            # Parse timestamp and update frequency data
            pass

        # Look for participant patterns
        participant_match = re.search(r"^([^:]+):", elem_text.strip())
        if participant_match:
            metadata["participants"].add(participant_match.group(1).strip())

    # Convert participants set to list
    metadata["participants"] = list(metadata["participants"])

    return text, metadata


def _extract_with_advanced_bs4(self, content: str) -> Tuple[str, dict]:
    """Advanced extraction using BeautifulSoup with metadata collection."""
    soup = BeautifulSoup(content, "html.parser")
    metadata = {
        "total_messages": 0,
        "participants": set(),
        "date_range": [None, None],
        "message_frequency": {},
        "media_count": {"photos": 0, "videos": 0, "documents": 0, "audio": 0},
    }

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Extract text content
    text = soup.get_text()

    # Extract message metadata (similar to lxml version)
    message_elements = soup.find_all(["div", "p"], class_=re.compile(r"message|msg"))
    metadata["total_messages"] = len(message_elements)

    for elem in message_elements:
        elem_text = elem.get_text()
        # Extract timestamps and participants (implementation depends on format)
        # This is a simplified version
        participant_match = re.search(r"^([^:]+):", elem_text.strip())
        if participant_match:
            metadata["participants"].add(participant_match.group(1).strip())

    metadata["participants"] = list(metadata["participants"])

    return text, metadata


def _analyze_sentiment(self, text: str) -> Optional[float]:
    """Analyze sentiment of text content."""
    if not self.sentiment_analyzer or not SENTIMENT_AVAILABLE:
        return None

    try:
        blob = TextBlob(text)
        sentiment = blob.sentiment
        # Return polarity score (-1 to 1)
        return sentiment.polarity
    except Exception as e:
        self.logger.error(f"Sentiment analysis failed: {e}")
        return None


def _detect_language(self, text: str) -> Optional[str]:
    """Detect language of text content."""
    if not SENTIMENT_AVAILABLE:  # TextBlob also handles language detection
        return None

    try:
        blob = TextBlob(text)
        return blob.detect_language()
    except Exception as e:
        self.logger.debug(f"Language detection failed: {e}")
        return None


def _extract_topics(self, text: str) -> List[str]:
    """Extract topics from text using keyword matching."""
    if not self.topic_extractor:
        return []

    topics = []
    text_lower = text.lower()

    for topic, keywords in self.topic_keywords.items():
        matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
        if matches >= 2:  # Require at least 2 keyword matches
            topics.append(topic)

    return topics


@handle_errors(default_return={})
def _analyze_advanced_keywords(self, text: str) -> Dict[str, int]:
    """Advanced keyword analysis with support for regex and boolean operators."""
    results = {}

    if not self.combined_pattern:
        return results

    # Use combined pattern for faster matching
    matches = self.combined_pattern.findall(text)

    # Count matches per keyword
    for match_groups in matches:
        if isinstance(match_groups, tuple):
            # Multiple groups from combined pattern
            for i, match in enumerate(match_groups):
                if match:  # Non-empty match
                    # Map back to original keyword
                    keyword = list(self.config.keywords)[i]
                    results[keyword] = results.get(keyword, 0) + 1
        else:
            # Single match
            for keyword in self.config.keywords:
                if self.keyword_patterns[keyword].search(match_groups):
                    results[keyword] = results.get(keyword, 0) + 1
                    break

    return results


def _should_process_file(self, file_path: str, file_hash: str) -> bool:
    """Determine if file should be processed based on cache and filters."""
    # Check cache first
    if self.cache_enabled:
        cached_result = self._get_cached_result(file_path, file_hash)
        if cached_result:
            self.logger.debug(f"Using cached result for {file_path}")
            self.results.append(cached_result)
            return False

    return True


@retry_on_failure(max_retries=2)
def analyze_file_advanced(self, file_path: str) -> Optional[AdvancedAnalysisResult]:
    """Analyze a single file with advanced features."""
    start_time = time.time()
    errors = []

    try:
        self.logger.info(f"Analyzing: {Path(file_path).name}")

        # Calculate file hash for caching
        file_hash = self._get_file_hash(file_path)
        file_size_kb = Path(file_path).stat().st_size / 1024

        # Check if we should process this file
        if not self._should_process_file(file_path, file_hash):
            return None  # Already processed from cache

        # Extract text and metadata
        text, metadata = self._extract_advanced_text_info(file_path)

        if not text:
            errors.append("No text content extracted")

        # Perform keyword analysis
        keyword_matches = self._analyze_advanced_keywords(text)

        # Advanced analysis features
        sentiment_score = None
        if self.config.sentiment_analysis:
            sentiment_score = self._analyze_sentiment(text)

        language_detected = None
        if self.config.language_detection:
            language_detected = self._detect_language(text)

        topics_detected = []
        if self.config.topic_extraction:
            topics_detected = self._extract_topics(text)

        # Create result object
        result = AdvancedAnalysisResult(
            file_name=Path(file_path).name,
            file_path=file_path,
            file_size_kb=file_size_kb,
            file_hash=file_hash,
            total_messages=metadata.get("total_messages", 0),
            total_words=metadata.get("word_count", 0),
            keyword_matches=keyword_matches,
            sentiment_score=sentiment_score,
            language_detected=language_detected,
            participants=metadata.get("participants", []),
            date_range=tuple(metadata.get("date_range", [None, None])),
            message_frequency=metadata.get("message_frequency", {}),
            media_count=metadata.get("media_count", {}),
            topics_detected=topics_detected,
            processing_time=time.time() - start_time,
            errors=errors,
        )

        # Cache the result
        if self.cache_enabled:
            self._cache_result(file_path, file_hash, result)

        return result

    except Exception as e:
        self.logger.error(f"Failed to analyze {file_path}: {e}")
        errors.append(str(e))

        # Return minimal result with error
        return AdvancedAnalysisResult(
            file_name=Path(file_path).name,
            file_path=file_path,
            file_size_kb=0,
            file_hash="",
            total_messages=0,
            total_words=0,
            keyword_matches={},
            processing_time=time.time() - start_time,
            errors=errors,
        )
