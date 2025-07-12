#!/usr/bin/env python3
"""
Advanced WhatsApp Chat Content Analyzer - Enhanced Version

A powerful analyzer with support for:
- Larger datasets (10,000+ files, 500MB+ files)
- Advanced regex patterns and custom search
- Streaming analysis for memory efficiency
- Extended text analysis capabilities
"""

import argparse
import json
import logging
import os
import re
import shutil
import signal
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil

try:
    from bs4 import BeautifulSoup

    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

try:
    import multiprocessing as mp

    MULTIPROCESSING_AVAILABLE = True
except ImportError:
    MULTIPROCESSING_AVAILABLE = False

# Enhanced security and performance constants
DEFAULT_MAX_FILES = 10000  # Increased from 1000
DEFAULT_MAX_FILE_SIZE_MB = 500  # Increased from 50MB
DEFAULT_MAX_TEXT_ANALYSIS_MB = 50  # Increased from 1MB per file
DEFAULT_MAX_TOTAL_MEMORY_GB = 8  # Total memory limit
DEFAULT_CHUNK_SIZE_KB = 2048  # 2MB chunks for large files
DEFAULT_OVERLAP_SIZE_KB = 4  # 4KB overlap between chunks
ALLOWED_EXTENSIONS = {".html", ".htm", ".txt", ".json"}  # Added more formats
BLOCKED_PATTERNS = ["..", "~", "$", "|", ";", "&", "`", "\\", "../"]


class InterruptHandler:
    """Handle graceful interruptions and cleanup."""

    def __init__(self):
        self.interrupted = False
        self.analyzer = None
        self.cleanup_functions = []

        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle interrupt signals gracefully."""
        if self.interrupted:
            # Second interrupt - force exit
            print("\n⚠️  Second interrupt received - forcing exit...")
            sys.exit(1)

        self.interrupted = True
        signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"

        print(f"\n⚠️  {signal_name} received - gracefully stopping analysis...")
        print("💾 Saving partial results and cleaning up...")
        print("🛑 Press Ctrl+C again to force exit")

        # Run cleanup functions
        self._run_cleanup()

    def register_analyzer(self, analyzer):
        """Register the analyzer for cleanup."""
        self.analyzer = analyzer

    def add_cleanup_function(self, func):
        """Add a cleanup function to run on interrupt."""
        self.cleanup_functions.append(func)

    def _run_cleanup(self):
        """Run all cleanup procedures."""
        try:
            # Close progress tracker first
            if (
                self.analyzer
                and hasattr(self.analyzer, "progress_tracker")
                and self.analyzer.progress_tracker
            ):
                self.analyzer.progress_tracker.close()

            # Run custom cleanup functions
            for cleanup_func in self.cleanup_functions:
                try:
                    cleanup_func()
                except Exception as e:
                    print(f"⚠️  Cleanup function failed: {e}")

            # Save partial results if analyzer exists
            if (
                self.analyzer
                and hasattr(self.analyzer, "results")
                and self.analyzer.results
            ):
                self._save_partial_results()

        except Exception as e:
            print(f"⚠️  Error during cleanup: {e}")

    def _save_partial_results(self):
        """Save partial analysis results."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"interrupted_analysis_{timestamp}"

            print(
                f"💾 Saving {len(self.analyzer.results)} partial results to {output_dir}/"
            )

            # Save what we have so far
            success = self.analyzer.save_results(output_dir)
            if success:
                print("✅ Partial results saved successfully")
                print(
                    f"📊 Processed {len(self.analyzer.results)} files before interruption"
                )
            else:
                print("❌ Failed to save partial results")

        except Exception as e:
            print(f"❌ Error saving partial results: {e}")

    def check_interrupted(self):
        """Check if analysis was interrupted."""
        return self.interrupted


class HardwareDetector:
    """Automatic hardware detection and optimal worker configuration."""

    @staticmethod
    def detect_optimal_workers() -> Dict[str, Any]:
        """Detect optimal number of workers based on system hardware."""
        hardware_info = {
            "cpu_cores": 1,
            "cpu_threads": 1,
            "memory_gb": 1.0,
            "has_gpu": False,
            "gpu_info": None,
            "recommended_workers": 1,
            "io_bound_workers": 1,
            "cpu_bound_workers": 1,
        }

        try:
            # CPU detection
            if MULTIPROCESSING_AVAILABLE:
                hardware_info["cpu_cores"] = mp.cpu_count()
                hardware_info["cpu_threads"] = hardware_info["cpu_cores"]

            # Memory detection
            try:
                memory_bytes = psutil.virtual_memory().total
                hardware_info["memory_gb"] = memory_bytes / (1024**3)
            except:
                hardware_info["memory_gb"] = 4.0  # Default fallback

            # GPU detection (basic check for CUDA/OpenCL)
            gpu_detected = False
            gpu_info = []

            try:
                # Try to detect NVIDIA GPUs
                import subprocess

                result = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-gpu=name,memory.total",
                        "--format=csv,noheader,nounits",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0 and result.stdout.strip():
                    gpu_detected = True
                    for line in result.stdout.strip().split("\n"):
                        if line.strip():
                            parts = line.split(",")
                            if len(parts) >= 2:
                                gpu_info.append(
                                    {
                                        "name": parts[0].strip(),
                                        "memory_mb": (
                                            int(parts[1].strip())
                                            if parts[1].strip().isdigit()
                                            else 0
                                        ),
                                        "type": "NVIDIA",
                                    }
                                )
            except (
                subprocess.TimeoutExpired,
                subprocess.CalledProcessError,
                FileNotFoundError,
                ImportError,
            ):
                pass

            # If no NVIDIA, try basic GPU detection
            if not gpu_detected:
                try:
                    import subprocess

                    # Check for any GPU via lspci on Linux
                    result = subprocess.run(
                        ["lspci"], capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        gpu_lines = [
                            line
                            for line in result.stdout.split("\n")
                            if any(
                                keyword in line.lower()
                                for keyword in [
                                    "vga",
                                    "display",
                                    "gpu",
                                    "nvidia",
                                    "amd",
                                    "intel",
                                ]
                            )
                        ]
                        if gpu_lines:
                            gpu_detected = True
                            gpu_info.append({"name": "Generic GPU", "type": "Unknown"})
                except (
                    subprocess.TimeoutExpired,
                    subprocess.CalledProcessError,
                    FileNotFoundError,
                ):
                    pass

            hardware_info["has_gpu"] = gpu_detected
            hardware_info["gpu_info"] = gpu_info

            # Calculate optimal workers
            cpu_cores = hardware_info["cpu_cores"]
            memory_gb = hardware_info["memory_gb"]

            # Base calculation: use 75% of cores for I/O bound tasks like file reading
            io_workers = max(1, int(cpu_cores * 0.75))

            # For CPU-bound tasks (regex processing), use fewer workers to avoid context switching
            cpu_workers = max(1, int(cpu_cores * 0.5))

            # Memory-based adjustment: reduce workers if low memory
            if memory_gb < 4:
                io_workers = max(1, min(io_workers, 2))
                cpu_workers = max(1, min(cpu_workers, 2))
            elif memory_gb < 8:
                io_workers = max(1, min(io_workers, 4))
                cpu_workers = max(1, min(cpu_workers, 3))

            # GPU acceleration potential (for future use)
            if gpu_detected and gpu_info:
                # GPU can handle some parallel text processing
                # For now, we'll just note it's available
                hardware_info["gpu_acceleration_potential"] = True

            # Final recommendations
            hardware_info["io_bound_workers"] = io_workers
            hardware_info["cpu_bound_workers"] = cpu_workers
            hardware_info["recommended_workers"] = (
                io_workers  # Default to I/O bound for file processing
            )

        except Exception:
            # Fallback to safe defaults
            hardware_info["recommended_workers"] = 2
            hardware_info["io_bound_workers"] = 2
            hardware_info["cpu_bound_workers"] = 1

        return hardware_info

    @staticmethod
    def get_performance_recommendations(
        file_count: int, total_size_mb: float
    ) -> Dict[str, Any]:
        """Get performance recommendations based on workload and hardware."""
        hardware = HardwareDetector.detect_optimal_workers()

        recommendations = {
            "workers": hardware["recommended_workers"],
            "batch_size": 200,
            "streaming_threshold_mb": 100,
            "memory_check_interval": 50,
            "enable_streaming": True,
        }

        # Adjust based on workload size
        if file_count > 10000:
            # Large datasets: optimize for throughput
            recommendations["workers"] = min(
                hardware["io_bound_workers"], 8
            )  # Cap at 8 for stability
            recommendations["batch_size"] = 500
            recommendations["streaming_threshold_mb"] = 50
            recommendations["memory_check_interval"] = 25
        elif file_count > 1000:
            # Medium datasets: balanced approach
            recommendations["workers"] = hardware["recommended_workers"]
            recommendations["batch_size"] = 200
        else:
            # Small datasets: minimize overhead
            recommendations["workers"] = min(hardware["recommended_workers"], 4)
            recommendations["batch_size"] = 100

        # Memory-based adjustments
        if hardware["memory_gb"] < 4:
            recommendations["workers"] = min(recommendations["workers"], 2)
            recommendations["batch_size"] = min(recommendations["batch_size"], 50)
            recommendations["streaming_threshold_mb"] = 25

        # Large file adjustments
        if total_size_mb > 10000:  # >10GB
            recommendations["enable_streaming"] = True
            recommendations["streaming_threshold_mb"] = 50
            recommendations["memory_check_interval"] = 10

        return {"hardware": hardware, "recommendations": recommendations}


class ProgressTracker:
    """Visual progress tracking with ETA estimates."""

    def __init__(self, total_files: int, enable_tqdm: bool = True):
        self.total_files = total_files
        self.processed_files = 0
        self.start_time = time.time()
        self.current_file = ""
        self.enable_tqdm = enable_tqdm and TQDM_AVAILABLE

        # Statistics
        self.total_size_mb = 0
        self.total_messages = 0
        self.total_matches = 0

        # Progress bar
        self.pbar = None
        if self.enable_tqdm:
            self.pbar = tqdm(
                total=total_files,
                desc="📊 Analyzing chats",
                unit="files",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
            )

    def update(
        self,
        file_name: str,
        file_size_mb: float = 0,
        messages: int = 0,
        matches: int = 0,
    ):
        """Update progress with current file info."""
        self.processed_files += 1
        self.current_file = os.path.basename(file_name)
        self.total_size_mb += file_size_mb
        self.total_messages += messages
        self.total_matches += matches

        if self.pbar:
            # Update progress bar with current file info
            self.pbar.set_postfix(
                {
                    "file": (
                        self.current_file[:15] + "..."
                        if len(self.current_file) > 15
                        else self.current_file
                    ),
                    "size": f"{self.total_size_mb:.1f}MB",
                    "msgs": f"{self.total_messages:,}",
                    "matches": f"{self.total_matches:,}",
                }
            )
            self.pbar.update(1)
        else:
            # Fallback console output
            elapsed = time.time() - self.start_time
            if elapsed > 0:
                rate = self.processed_files / elapsed
                eta = (
                    (self.total_files - self.processed_files) / rate if rate > 0 else 0
                )
                eta_str = f"{eta/60:.1f}m" if eta > 60 else f"{eta:.0f}s"

                print(
                    f"\r📊 [{self.processed_files:,}/{self.total_files:,}] "
                    f"{self.current_file[:20]:20} | "
                    f"ETA: {eta_str:>6} | "
                    f"Rate: {rate:.1f}/s",
                    end="",
                    flush=True,
                )

    def set_stage(self, stage: str):
        """Update the stage description."""
        if self.pbar:
            self.pbar.set_description(f"📊 {stage}")
        else:
            print(f"\n📊 {stage}")

    def close(self):
        """Close the progress tracker."""
        if self.pbar:
            self.pbar.close()
        else:
            print()  # New line for console output

    def get_stats(self) -> Dict:
        """Get current processing statistics."""
        elapsed = time.time() - self.start_time
        return {
            "files_processed": self.processed_files,
            "total_files": self.total_files,
            "elapsed_time": elapsed,
            "rate_per_second": self.processed_files / elapsed if elapsed > 0 else 0,
            "total_size_mb": self.total_size_mb,
            "total_messages": self.total_messages,
            "total_matches": self.total_matches,
        }


@dataclass
class AdvancedAnalysisConfig:
    """Advanced configuration for content analysis."""

    # File processing limits
    max_files: int = DEFAULT_MAX_FILES
    max_file_size_mb: int = DEFAULT_MAX_FILE_SIZE_MB
    max_text_analysis_mb: int = DEFAULT_MAX_TEXT_ANALYSIS_MB
    max_total_memory_gb: int = DEFAULT_MAX_TOTAL_MEMORY_GB

    # Text processing
    chunk_size_kb: int = DEFAULT_CHUNK_SIZE_KB
    overlap_size_kb: int = DEFAULT_OVERLAP_SIZE_KB
    enable_streaming: bool = True

    # Regex and pattern analysis
    enable_custom_regex: bool = True
    max_regex_patterns: int = 100  # Increased from 50
    regex_timeout_seconds: int = 10  # Per pattern timeout
    case_sensitive_regex: bool = False

    # Performance
    parallel_workers: int = 4
    auto_detect_workers: bool = True  # Automatically detect optimal workers
    batch_size: int = 200  # Process files in batches
    memory_check_interval: int = 50  # Check memory every N files

    # Advanced features
    save_match_examples: bool = True
    max_examples_per_pattern: int = 20
    generate_statistics: bool = True
    extract_unique_matches: bool = True


@dataclass
class AdvancedAnalysisResult:
    """Enhanced analysis result with more detailed information."""

    file_name: str
    file_size_bytes: int
    processing_time: float
    timestamp: str

    # Text statistics
    total_messages: int
    total_words: int
    total_characters: int
    unique_words: int

    # Pattern matches
    keyword_matches: Dict[str, int] = field(default_factory=dict)
    regex_matches: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Advanced analysis
    word_frequency: Dict[str, int] = field(default_factory=dict)
    pattern_examples: Dict[str, List[str]] = field(default_factory=dict)

    # Detailed conversation insights
    chat_metadata: Dict[str, Any] = field(default_factory=dict)
    conversation_insights: Dict[str, Any] = field(default_factory=dict)
    match_contexts: Dict[str, List[Dict]] = field(default_factory=dict)
    time_analysis: Dict[str, Any] = field(default_factory=dict)
    participant_analysis: Dict[str, Any] = field(default_factory=dict)

    # Content classification
    content_categories: Dict[str, int] = field(default_factory=dict)
    relevance_score: float = 0.0
    priority_level: str = "low"  # low, medium, high, critical

    # Processing info
    chunks_processed: int = 0
    memory_usage_mb: float = 0.0
    errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class ConversationAnalyzer:
    """Detailed conversation analysis and insights."""

    @staticmethod
    def analyze_conversation_details(
        text: str, file_path: str, matches: Dict
    ) -> Dict[str, Any]:
        """Extract detailed conversation insights."""
        insights = {
            "chat_name": Path(file_path).stem,
            "estimated_participants": ConversationAnalyzer._estimate_participants(text),
            "message_patterns": ConversationAnalyzer._analyze_message_patterns(text),
            "time_patterns": ConversationAnalyzer._analyze_time_patterns(text),
            "content_themes": ConversationAnalyzer._analyze_content_themes(
                text, matches
            ),
            "interaction_intensity": ConversationAnalyzer._calculate_interaction_intensity(
                text
            ),
            "language_analysis": ConversationAnalyzer._analyze_language(text),
        }
        return insights

    @staticmethod
    def _estimate_participants(text: str) -> Dict[str, Any]:
        """Estimate number and activity of participants."""
        # Look for participant patterns in WhatsApp exports
        participant_patterns = [
            r"(\d{1,2}/\d{1,2}/\d{2,4}),?\s*(\d{1,2}:\d{2})\s*[-–]\s*([^:]+):",  # WhatsApp format
            r'<div class="message.*?from_(.+?)">',  # HTML export format
            r"\[(\d{2}:\d{2}:\d{2})\] ([^:]+):",  # Alternative format
        ]

        participants = set()
        for pattern in participant_patterns:
            matches = re.findall(pattern, text[:5000])  # Sample first 5K chars
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    participant = match[-1].strip()
                    if (
                        len(participant) > 0 and len(participant) < 50
                    ):  # Reasonable name length
                        participants.add(participant)

        return {
            "estimated_count": len(participants),
            "participant_names": list(participants)[:10],  # Limit for privacy
            "is_group_chat": len(participants) > 2,
        }

    @staticmethod
    def _analyze_message_patterns(text: str) -> Dict[str, Any]:
        """Analyze message frequency and patterns."""
        lines = text.split("\n")
        message_lines = [
            line for line in lines if ":" in line and len(line.strip()) > 10
        ]

        return {
            "total_lines": len(lines),
            "estimated_messages": len(message_lines),
            "avg_message_length": sum(len(line) for line in message_lines)
            / max(len(message_lines), 1),
            "short_messages": len([line for line in message_lines if len(line) < 50]),
            "long_messages": len([line for line in message_lines if len(line) > 200]),
        }

    @staticmethod
    def _analyze_time_patterns(text: str) -> Dict[str, Any]:
        """Analyze temporal patterns in conversation."""
        # Extract timestamps
        timestamp_patterns = [
            r"(\d{1,2}/\d{1,2}/\d{2,4}),?\s*(\d{1,2}:\d{2})",
            r"(\d{2}:\d{2}:\d{2})",
            r"(\d{1,2}:\d{2})",
        ]

        timestamps = []
        for pattern in timestamp_patterns:
            timestamps.extend(
                re.findall(pattern, text[:10000])
            )  # Sample for performance

        # Analyze time distribution
        hours = []
        for ts in timestamps[:100]:  # Limit for performance
            try:
                if isinstance(ts, tuple):
                    time_part = ts[1] if len(ts) > 1 else ts[0]
                else:
                    time_part = ts

                if ":" in str(time_part):
                    hour = int(str(time_part).split(":")[0])
                    if 0 <= hour <= 23:
                        hours.append(hour)
            except:
                continue

        time_distribution = {}
        if hours:
            for hour in hours:
                time_distribution[hour] = time_distribution.get(hour, 0) + 1

        return {
            "total_timestamps": len(timestamps),
            "sample_hours": hours[:20],
            "time_distribution": time_distribution,
            "peak_hours": sorted(
                time_distribution.items(), key=lambda x: x[1], reverse=True
            )[:3],
        }

    @staticmethod
    def _analyze_content_themes(text: str, matches: Dict) -> Dict[str, Any]:
        """Analyze content themes and topics."""
        # Categorize based on keywords found
        themes = {
            "work_related": 0,
            "personal_family": 0,
            "social_events": 0,
            "emotional_content": 0,
            "media_sharing": 0,
            "logistics_planning": 0,
            "health_wellness": 0,
            "shopping_money": 0,
        }

        # Enhanced theme keyword mapping for Spanish/English
        theme_keywords = {
            "work_related": [
                # Spanish
                "trabajo",
                "oficina",
                "reunión",
                "jefe",
                "empresa",
                "proyecto",
                "cliente",
                "entrevista",
                "sueldo",
                "horario",
                "compañero",
                "empleado",
                "junta",
                "presentación",
                "informe",
                "tarea",
                "deadline",
                # English
                "work",
                "office",
                "meeting",
                "project",
                "boss",
                "company",
                "client",
                "interview",
                "salary",
                "schedule",
                "colleague",
                "employee",
                "presentation",
                "report",
                "task",
                "job",
            ],
            "personal_family": [
                # Spanish
                "familia",
                "familia",
                "amor",
                "hijo",
                "hija",
                "papa",
                "mama",
                "hermano",
                "hermana",
                "esposo",
                "esposa",
                "novio",
                "novia",
                "abuelo",
                "abuela",
                "tio",
                "tia",
                "primo",
                "prima",
                "sobrino",
                "sobrina",
                "matrimonio",
                "boda",
                "embarazo",
                "bebe",
                "niño",
                "niña",
                "padre",
                "madre",
                "pareja",
                # English
                "family",
                "love",
                "son",
                "daughter",
                "dad",
                "mom",
                "brother",
                "sister",
                "husband",
                "wife",
                "boyfriend",
                "girlfriend",
                "grandfather",
                "grandmother",
                "uncle",
                "aunt",
                "cousin",
                "nephew",
                "niece",
                "marriage",
                "wedding",
                "pregnancy",
                "baby",
                "child",
                "father",
                "mother",
                "partner",
            ],
            "social_events": [
                # Spanish
                "fiesta",
                "celebrar",
                "cumpleaños",
                "evento",
                "salir",
                "invitación",
                "cena",
                "comida",
                "reunión",
                "paseo",
                "viaje",
                "vacaciones",
                "fin de semana",
                "diversión",
                "baile",
                "concierto",
                "cine",
                "restaurante",
                "bar",
                "club",
                "parque",
                "playa",
                # English
                "party",
                "celebrate",
                "birthday",
                "event",
                "go out",
                "invitation",
                "dinner",
                "lunch",
                "gathering",
                "trip",
                "vacation",
                "weekend",
                "fun",
                "dance",
                "concert",
                "movies",
                "restaurant",
                "bar",
                "club",
                "park",
                "beach",
            ],
            "emotional_content": [
                # Spanish
                "feliz",
                "triste",
                "enojado",
                "preocupado",
                "nervioso",
                "emocionado",
                "deprimido",
                "ansioso",
                "contento",
                "alegre",
                "molesto",
                "furioso",
                "estresado",
                "cansado",
                "aburrido",
                "sorprendido",
                "asustado",
                "confundido",
                "orgulloso",
                "avergonzado",
                "celoso",
                "enamorado",
                # English
                "happy",
                "sad",
                "angry",
                "worried",
                "nervous",
                "excited",
                "depressed",
                "anxious",
                "glad",
                "upset",
                "furious",
                "stressed",
                "tired",
                "bored",
                "surprised",
                "scared",
                "confused",
                "proud",
                "embarrassed",
                "jealous",
            ],
            "media_sharing": [
                # Spanish
                "foto",
                "video",
                "imagen",
                "archivo",
                "documento",
                "link",
                "enlace",
                "adjunto",
                "compartir",
                "enviar",
                "mandar",
                "descargar",
                "subir",
                "gif",
                "sticker",
                "emoji",
                "meme",
                # English
                "photo",
                "video",
                "image",
                "file",
                "document",
                "link",
                "attachment",
                "share",
                "send",
                "download",
                "upload",
                "gif",
                "sticker",
                "emoji",
                "meme",
            ],
            "logistics_planning": [
                # Spanish
                "cuando",
                "donde",
                "hora",
                "tiempo",
                "lugar",
                "plan",
                "planear",
                "organizar",
                "coordinar",
                "confirmar",
                "cancelar",
                "posponer",
                "adelantar",
                "cambiar",
                "dirección",
                "ubicación",
                "transporte",
                "llegada",
                "salida",
                "cita",
                "reserva",
                "agenda",
                # English
                "when",
                "where",
                "time",
                "place",
                "plan",
                "organize",
                "coordinate",
                "confirm",
                "cancel",
                "postpone",
                "reschedule",
                "change",
                "address",
                "location",
                "transport",
                "arrival",
                "departure",
                "appointment",
                "reservation",
                "schedule",
            ],
            "health_wellness": [
                # Spanish
                "salud",
                "enfermo",
                "doctor",
                "médico",
                "hospital",
                "medicina",
                "dolor",
                "síntoma",
                "tratamiento",
                "ejercicio",
                "dieta",
                "gym",
                "deporte",
                "dormir",
                "descanso",
                "estrés",
                "relajar",
                # English
                "health",
                "sick",
                "doctor",
                "hospital",
                "medicine",
                "pain",
                "symptom",
                "treatment",
                "exercise",
                "diet",
                "gym",
                "sport",
                "sleep",
                "rest",
                "stress",
                "relax",
            ],
            "shopping_money": [
                # Spanish
                "comprar",
                "vender",
                "precio",
                "dinero",
                "peso",
                "dólar",
                "euro",
                "caro",
                "barato",
                "descuento",
                "oferta",
                "tienda",
                "mercado",
                "centro comercial",
                "banco",
                "tarjeta",
                "efectivo",
                "pagar",
                "cobrar",
                # English
                "buy",
                "sell",
                "price",
                "money",
                "dollar",
                "euro",
                "expensive",
                "cheap",
                "discount",
                "sale",
                "store",
                "market",
                "mall",
                "bank",
                "card",
                "cash",
                "pay",
                "charge",
            ],
        }

        text_lower = text.lower()
        for theme, keywords in theme_keywords.items():
            for keyword in keywords:
                themes[theme] += text_lower.count(keyword)

        # Add matches from analysis
        for keyword, count in matches.get("keyword_matches", {}).items():
            keyword_lower = keyword.lower()
            for theme, keywords in theme_keywords.items():
                if keyword_lower in keywords:
                    themes[theme] += count

        return themes

    @staticmethod
    def _calculate_interaction_intensity(text: str) -> Dict[str, Any]:
        """Calculate interaction intensity metrics."""
        # Count various interaction indicators
        questions = len(re.findall(r"\?", text))
        exclamations = len(re.findall(r"!", text))
        caps_words = len(re.findall(r"\b[A-Z]{2,}\b", text))

        text_length = len(text)
        if text_length == 0:
            return {"score": 0, "level": "none"}

        # Calculate intensity score
        intensity_score = (
            (questions * 2) + (exclamations * 1.5) + (caps_words * 3)
        ) / (
            text_length / 1000
        )  # Normalize per 1K characters

        level = "low"
        if intensity_score > 10:
            level = "high"
        elif intensity_score > 5:
            level = "medium"

        return {
            "score": round(intensity_score, 2),
            "level": level,
            "questions": questions,
            "exclamations": exclamations,
            "caps_words": caps_words,
        }

    @staticmethod
    def _analyze_language(text: str) -> Dict[str, Any]:
        """Enhanced language analysis for Spanish and English."""
        # Extract actual message content from HTML or raw text
        clean_text = ConversationAnalyzer._extract_message_content(text)

        # Enhanced Spanish indicators (more comprehensive)
        spanish_indicators = [
            # Common words
            "que",
            "como",
            "para",
            "con",
            "por",
            "en",
            "es",
            "la",
            "el",
            "de",
            "y",
            "un",
            "una",
            "los",
            "las",
            "pero",
            "si",
            "no",
            "ya",
            "me",
            "te",
            "se",
            "le",
            "lo",
            "muy",
            "mas",
            "bien",
            "todo",
            "cuando",
            # Spanish-specific
            "donde",
            "porque",
            "tambien",
            "desde",
            "hasta",
            "sobre",
            "entre",
            "durante",
            "antes",
            "despues",
            "aqui",
            "ahi",
            "alla",
            "este",
            "esta",
            "esto",
            "ese",
            "esa",
            "eso",
            "aquel",
            "aquella",
            "aquello",
            # Verbs
            "ser",
            "estar",
            "tener",
            "hacer",
            "ir",
            "ver",
            "dar",
            "saber",
            "querer",
            "poder",
            "decir",
            "trabajar",
            # WhatsApp specific
            "hola",
            "gracias",
            "saludos",
            "buenas",
            "bueno",
            "vale",
            "ok",
        ]

        # Enhanced English indicators
        english_indicators = [
            # Common words
            "the",
            "and",
            "to",
            "of",
            "a",
            "in",
            "is",
            "you",
            "that",
            "it",
            "he",
            "was",
            "for",
            "on",
            "are",
            "as",
            "with",
            "his",
            "they",
            "i",
            "at",
            "be",
            "this",
            "have",
            "from",
            "or",
            "one",
            "had",
            "by",
            "word",
            # English-specific
            "what",
            "where",
            "when",
            "why",
            "how",
            "who",
            "which",
            "there",
            "here",
            "would",
            "could",
            "should",
            "will",
            "can",
            "may",
            "might",
            "must",
            "shall",
            "going",
            "been",
            "being",
            "does",
            "did",
            "has",
            # WhatsApp specific
            "hello",
            "hi",
            "thanks",
            "thank",
            "yeah",
            "yes",
            "okay",
            "ok",
            "good",
            "great",
            "nice",
        ]

        # Spanish grammatical patterns
        spanish_patterns = [
            r"\b(el|la|los|las)\s+\w+",  # Articles
            r"\b\w+ción\b",  # Words ending in -ción
            r"\b\w+dad\b",  # Words ending in -dad
            r"\b\w+mente\b",  # Adverbs ending in -mente
            r"\b\w+ando\b",  # Gerunds ending in -ando
            r"\b\w+iendo\b",  # Gerunds ending in -iendo
            r"\b\w+ar\b",  # Infinitives ending in -ar
            r"\b\w+er\b",  # Infinitives ending in -er
            r"\b\w+ir\b",  # Infinitives ending in -ir
        ]

        # English grammatical patterns
        english_patterns = [
            r"\b\w+ing\b",  # Words ending in -ing
            r"\b\w+ed\b",  # Past tense -ed
            r"\b\w+ly\b",  # Adverbs ending in -ly
            r"\b\w+'s\b",  # Possessive 's
            r"\b\w+'t\b",  # Contractions like don't, can't
            r"\b\w+'re\b",  # Contractions like you're, we're
            r"\b\w+'ll\b",  # Contractions like I'll, you'll
            r"\bthe\s+\w+",  # The + word
        ]

        text_sample = clean_text.lower()[:10000]  # Larger sample for better accuracy

        # Count word indicators
        spanish_word_count = 0
        english_word_count = 0

        # Use word boundaries for more accurate counting
        for word in spanish_indicators:
            spanish_word_count += len(
                re.findall(rf"\b{re.escape(word)}\b", text_sample)
            )

        for word in english_indicators:
            english_word_count += len(
                re.findall(rf"\b{re.escape(word)}\b", text_sample)
            )

        # Count pattern matches
        spanish_pattern_count = 0
        english_pattern_count = 0

        for pattern in spanish_patterns:
            spanish_pattern_count += len(re.findall(pattern, text_sample))

        for pattern in english_patterns:
            english_pattern_count += len(re.findall(pattern, text_sample))

        # Weighted scoring (words count more than patterns)
        spanish_score = (spanish_word_count * 2) + spanish_pattern_count
        english_score = (english_word_count * 2) + english_pattern_count

        total_score = spanish_score + english_score

        if total_score == 0:
            return {
                "primary_language": "unknown",
                "confidence": 0,
                "spanish_score": 0,
                "english_score": 0,
                "detection_method": "no_indicators_found",
            }

        # Determine primary language
        if spanish_score > english_score:
            primary = "spanish"
            confidence = spanish_score / total_score
        elif english_score > spanish_score:
            primary = "english"
            confidence = english_score / total_score
        else:
            # Tie - check for mixed language
            primary = "mixed"
            confidence = 0.5

        # Language mixing detection
        mixing_threshold = 0.3
        is_mixed = False
        if total_score > 10:  # Only if we have enough data
            minority_ratio = min(spanish_score, english_score) / total_score
            if minority_ratio > mixing_threshold:
                is_mixed = True

        return {
            "primary_language": primary,
            "confidence": round(confidence, 2),
            "spanish_score": spanish_score,
            "english_score": english_score,
            "spanish_words": spanish_word_count,
            "english_words": english_word_count,
            "spanish_patterns": spanish_pattern_count,
            "english_patterns": english_pattern_count,
            "is_mixed_language": is_mixed,
            "total_indicators": total_score,
            "detection_method": "enhanced_analysis",
        }

    @staticmethod
    def _extract_message_content(text: str) -> str:
        """Extract actual message content from HTML or other formats."""
        # If it's HTML, extract text content
        if "<" in text and ">" in text:
            try:
                if BS4_AVAILABLE:
                    from bs4 import BeautifulSoup

                    soup = BeautifulSoup(text, "html.parser")

                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()

                    # Get text content
                    clean_text = soup.get_text()
                else:
                    # Fallback: simple HTML tag removal
                    clean_text = re.sub(r"<[^>]+>", " ", text)
            except:
                clean_text = text
        else:
            clean_text = text

        # Clean up whitespace and normalize
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        # Remove common non-message content
        filters = [
            r"WhatsApp Chat with .*",
            r"Messages and calls are end-to-end encrypted.*",
            r"This message was deleted",
            r"You deleted this message",
            r"<Media omitted>",
            r"\[.*?\]",  # Remove bracketed content like [Photo]
            r"http[s]?://\S+",  # Remove URLs
            r"\d{1,2}/\d{1,2}/\d{2,4}.*?\d{1,2}:\d{2}",  # Remove timestamps
        ]

        for filter_pattern in filters:
            clean_text = re.sub(filter_pattern, " ", clean_text, flags=re.IGNORECASE)

        return clean_text


class RelevantChatExtractor:
    """Extract and copy relevant chats based on analysis results."""

    def __init__(self, base_output_dir: str):
        self.base_output_dir = Path(base_output_dir)
        self.relevant_chats_dir = self.base_output_dir / "relevant_chats"
        self.metadata_file = self.relevant_chats_dir / "extraction_metadata.json"

    def extract_relevant_chats(
        self, results: List[Any], criteria: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Extract chats that meet relevance criteria."""
        if criteria is None:
            criteria = {
                "min_matches": 5,
                "min_relevance_score": 0.3,
                "priority_levels": ["medium", "high", "critical"],
                "required_themes": None,  # Any themes
            }

        # Create directories
        self._create_extraction_directories()

        relevant_results = []
        extraction_stats = {
            "total_analyzed": len(results),
            "total_relevant": 0,
            "extracted_files": [],
            "criteria_used": criteria,
            "extraction_timestamp": datetime.now().isoformat(),
        }

        for result in results:
            if self._meets_relevance_criteria(result, criteria):
                try:
                    # Copy the file
                    copied_path = self._copy_chat_file(result)
                    if copied_path:
                        relevant_results.append(result)
                        extraction_stats["extracted_files"].append(
                            {
                                "original_path": result.file_name,
                                "copied_path": str(copied_path),
                                "relevance_score": result.relevance_score,
                                "priority_level": result.priority_level,
                                "total_matches": sum(result.keyword_matches.values()),
                                "file_size_mb": result.file_size_bytes / (1024 * 1024),
                            }
                        )

                        # Create individual chat summary
                        self._create_chat_summary(result, copied_path)

                except Exception as e:
                    print(f"Error extracting chat {result.file_name}: {e}")

        extraction_stats["total_relevant"] = len(relevant_results)

        # Save extraction metadata
        self._save_extraction_metadata(extraction_stats)

        # Create master summary
        self._create_master_summary(relevant_results, extraction_stats)

        return extraction_stats

    def _create_extraction_directories(self):
        """Create necessary directories for extraction."""
        directories = [
            self.relevant_chats_dir,
            self.relevant_chats_dir / "high_priority",
            self.relevant_chats_dir / "medium_priority",
            self.relevant_chats_dir / "summaries",
            self.relevant_chats_dir / "by_theme",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _meets_relevance_criteria(self, result: Any, criteria: Dict) -> bool:
        """Check if a chat meets the relevance criteria."""
        # Check minimum matches
        total_matches = sum(result.keyword_matches.values())
        if total_matches < criteria.get("min_matches", 5):
            return False

        # Check relevance score
        if result.relevance_score < criteria.get("min_relevance_score", 0.3):
            return False

        # Check priority level
        allowed_priorities = criteria.get(
            "priority_levels", ["medium", "high", "critical"]
        )
        if result.priority_level not in allowed_priorities:
            return False

        # Check required themes
        required_themes = criteria.get("required_themes")
        if required_themes:
            chat_themes = result.content_categories
            has_required_theme = any(
                chat_themes.get(theme, 0) > 0 for theme in required_themes
            )
            if not has_required_theme:
                return False

        return True

    def _copy_chat_file(self, result: Any) -> Optional[Path]:
        """Copy chat file to relevant directory."""
        try:
            source_path = Path(result.file_name)

            # Determine destination based on priority
            if result.priority_level in ["critical", "high"]:
                dest_dir = self.relevant_chats_dir / "high_priority"
            else:
                dest_dir = self.relevant_chats_dir / "medium_priority"

            # Create safe filename
            safe_filename = self._create_safe_filename(source_path.name)
            dest_path = dest_dir / safe_filename

            # Copy file
            shutil.copy2(source_path, dest_path)

            return dest_path

        except Exception as e:
            print(f"Error copying file {result.file_name}: {e}")
            return None

    def _create_safe_filename(self, filename: str) -> str:
        """Create a safe filename for copying."""
        # Remove or replace problematic characters
        safe_chars = (
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_. "
        )
        safe_name = "".join(c if c in safe_chars else "_" for c in filename)

        # Limit length
        if len(safe_name) > 100:
            name_part = safe_name[:80]
            ext_part = safe_name[-15:] if "." in safe_name[-15:] else ""
            safe_name = name_part + "_" + ext_part

        return safe_name

    def _create_chat_summary(self, result: Any, copied_path: Path):
        """Create individual chat summary file."""
        summary_filename = copied_path.stem + "_summary.txt"
        summary_path = self.relevant_chats_dir / "summaries" / summary_filename

        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("CHAT ANALYSIS SUMMARY\n")
            f.write("=" * 50 + "\n\n")

            f.write(f"File: {result.file_name}\n")
            f.write(f"Copied to: {copied_path}\n")
            f.write(f"Priority Level: {result.priority_level.upper()}\n")
            f.write(f"Relevance Score: {result.relevance_score:.2f}\n")
            f.write(f"File Size: {result.file_size_bytes / (1024*1024):.1f}MB\n\n")

            # Conversation insights
            insights = result.conversation_insights
            f.write("CONVERSATION INSIGHTS:\n")
            f.write("-" * 25 + "\n")
            f.write(f"Chat Name: {insights.get('chat_name', 'Unknown')}\n")

            participants = insights.get("estimated_participants", {})
            f.write(f"Participants: {participants.get('estimated_count', 'Unknown')}")
            if participants.get("is_group_chat"):
                f.write(" (Group Chat)")
            f.write("\n")

            # Language analysis
            lang_info = insights.get("language_analysis", {})
            if lang_info.get("primary_language"):
                primary_lang = lang_info["primary_language"].title()
                confidence = lang_info.get("confidence", 0)

                f.write(
                    f"Primary Language: {primary_lang} ({confidence:.0%} confidence)\n"
                )

                # Show detailed language info if mixed
                if lang_info.get("is_mixed_language"):
                    f.write("Language Mixing Detected: Yes\n")
                    f.write(
                        f"Spanish indicators: {lang_info.get('spanish_score', 0)}\n"
                    )
                    f.write(
                        f"English indicators: {lang_info.get('english_score', 0)}\n"
                    )
                elif lang_info.get("detection_method") == "enhanced_analysis":
                    # Show brief detail for single language
                    if lang_info["primary_language"] == "spanish":
                        f.write(
                            f"Spanish indicators: {lang_info.get('spanish_score', 0)}\n"
                        )
                    else:
                        f.write(
                            f"English indicators: {lang_info.get('english_score', 0)}\n"
                        )

            f.write("\nMESSAGE STATISTICS:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total Messages: {result.total_messages:,}\n")
            f.write(f"Total Words: {result.total_words:,}\n")
            f.write(f"Total Characters: {result.total_characters:,}\n")

            # Keyword matches
            if result.keyword_matches:
                f.write("\nKEYWORD MATCHES:\n")
                f.write("-" * 17 + "\n")
                for keyword, count in sorted(
                    result.keyword_matches.items(), key=lambda x: x[1], reverse=True
                ):
                    f.write(f"• {keyword}: {count:,}\n")

            # Content themes
            themes = result.content_categories
            if themes:
                f.write("\nCONTENT THEMES:\n")
                f.write("-" * 15 + "\n")
                for theme, count in sorted(
                    themes.items(), key=lambda x: x[1], reverse=True
                ):
                    if count > 0:
                        f.write(f"• {theme.replace('_', ' ').title()}: {count:,}\n")

            # Interaction intensity
            intensity = insights.get("interaction_intensity", {})
            if intensity:
                f.write("\nINTERACTION INTENSITY:\n")
                f.write("-" * 22 + "\n")
                f.write(f"Level: {intensity.get('level', 'unknown').upper()}\n")
                f.write(f"Score: {intensity.get('score', 0):.2f}\n")
                f.write(f"Questions: {intensity.get('questions', 0):,}\n")
                f.write(f"Exclamations: {intensity.get('exclamations', 0):,}\n")

            # Time patterns
            time_patterns = insights.get("time_patterns", {})
            if time_patterns.get("peak_hours"):
                f.write("\nTIME PATTERNS:\n")
                f.write("-" * 14 + "\n")
                f.write("Peak Hours: ")
                peak_hours = time_patterns["peak_hours"][:3]
                peak_strs = [f"{hour}:00 ({count} msgs)" for hour, count in peak_hours]
                f.write(", ".join(peak_strs) + "\n")

            # Match examples
            if result.pattern_examples:
                f.write("\nMATCH EXAMPLES:\n")
                f.write("-" * 15 + "\n")
                for pattern, examples in result.pattern_examples.items():
                    if examples:
                        f.write(f"{pattern}: {examples[0][:100]}...\n")

    def _save_extraction_metadata(self, stats: Dict):
        """Save extraction metadata to JSON file."""
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

    def _create_master_summary(self, relevant_results: List[Any], stats: Dict):
        """Create master summary of all relevant chats."""
        summary_path = self.relevant_chats_dir / "MASTER_SUMMARY.txt"

        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("RELEVANT CHATS EXTRACTION SUMMARY\n")
            f.write("=" * 50 + "\n\n")

            f.write(f"Extraction Date: {stats['extraction_timestamp'][:19]}\n")
            f.write(f"Total Chats Analyzed: {stats['total_analyzed']:,}\n")
            f.write(f"Relevant Chats Found: {stats['total_relevant']:,}\n")
            f.write(
                f"Extraction Rate: {(stats['total_relevant']/stats['total_analyzed']*100):.1f}%\n\n"
            )

            # Criteria used
            criteria = stats["criteria_used"]
            f.write("EXTRACTION CRITERIA:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Minimum Matches: {criteria.get('min_matches', 'N/A')}\n")
            f.write(
                f"Minimum Relevance Score: {criteria.get('min_relevance_score', 'N/A')}\n"
            )
            f.write(
                f"Priority Levels: {', '.join(criteria.get('priority_levels', []))}\n\n"
            )

            # Summary by priority
            priority_counts = {}
            total_size_mb = 0
            total_matches = 0

            for file_info in stats["extracted_files"]:
                priority = file_info.get("priority_level", "unknown")
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
                total_size_mb += file_info.get("file_size_mb", 0)
                total_matches += file_info.get("total_matches", 0)

            f.write("SUMMARY BY PRIORITY:\n")
            f.write("-" * 20 + "\n")
            for priority, count in sorted(priority_counts.items()):
                f.write(f"{priority.capitalize()}: {count:,} chats\n")

            f.write("\nTOTAL STATISTICS:\n")
            f.write("-" * 17 + "\n")
            f.write(f"Total Size: {total_size_mb:.1f}MB\n")
            f.write(f"Total Matches: {total_matches:,}\n")
            if len(stats["extracted_files"]) > 0:
                f.write(
                    f"Average Matches per Chat: {total_matches/len(stats['extracted_files']):.1f}\n\n"
                )
            else:
                f.write("Average Matches per Chat: 0\n\n")

            # Top relevant chats
            if stats["extracted_files"]:
                f.write("TOP RELEVANT CHATS:\n")
                f.write("-" * 18 + "\n")

                # Sort by relevance score
                sorted_files = sorted(
                    stats["extracted_files"],
                    key=lambda x: x.get("relevance_score", 0),
                    reverse=True,
                )

                for i, file_info in enumerate(sorted_files[:10], 1):
                    original_name = Path(file_info["original_path"]).name
                    f.write(f"{i:2d}. {original_name[:40]:40} | ")
                    f.write(f"Score: {file_info.get('relevance_score', 0):.2f} | ")
                    f.write(f"Matches: {file_info.get('total_matches', 0):,}\n")

            f.write("\nFILES LOCATION:\n")
            f.write("-" * 15 + "\n")
            f.write(f"High Priority: {self.relevant_chats_dir}/high_priority/\n")
            f.write(f"Medium Priority: {self.relevant_chats_dir}/medium_priority/\n")
            f.write(f"Individual Summaries: {self.relevant_chats_dir}/summaries/\n")


class AdvancedPatternLibrary:
    """Library of predefined patterns for WhatsApp analysis."""

    COMMUNICATION_PATTERNS = {
        "questions": r"\?",
        "exclamations": r"!",
        "mentions": r"@\w+",
        "timestamps": r"\d{1,2}:\d{2}",
        "dates": r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
        "phone_numbers": r"\+?[\d\s\-\(\)]{10,15}",
        "emails": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "simple_urls": r"https?://[^\s]+",
    }

    WHATSAPP_SPECIFIC = {
        "media_omitted": r"(image omitted|video omitted|audio omitted|document omitted)",
        "stickers": r"sticker omitted",
        "gifs": r"GIF omitted",
        "voice_messages": r"audio omitted",
        "deleted_messages": r"(This message was deleted|Este mensaje fue eliminado)",
        "group_events": r"(joined using this group\'s invite link|left|was added|was removed)",
        "name_changes": r"(changed.*name|cambió.*nombre)",
        "security_code": r"security code.*changed",
    }

    CONTENT_PATTERNS = {
        "emojis": r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF]",
        "hashtags": r"#\w+",
        "all_caps": r"\b[A-Z]{3,}\b",
        "repeated_chars": r"(.)\1{2,}",
        "long_words": r"\b\w{15,}\b",
        "numbers": r"\b\d+\b",
        "special_chars": r'[!@#$%^&*()+=\[\]{}|\\:";\'<>?,./]',
    }

    @classmethod
    def get_all_patterns(cls) -> Dict[str, str]:
        """Get all predefined patterns."""
        patterns = {}
        patterns.update(cls.COMMUNICATION_PATTERNS)
        patterns.update(cls.WHATSAPP_SPECIFIC)
        patterns.update(cls.CONTENT_PATTERNS)
        return patterns

    @classmethod
    def get_category_patterns(cls, category: str) -> Dict[str, str]:
        """Get patterns by category."""
        categories = {
            "communication": cls.COMMUNICATION_PATTERNS,
            "whatsapp": cls.WHATSAPP_SPECIFIC,
            "content": cls.CONTENT_PATTERNS,
        }
        return categories.get(category, {})


class AdvancedSecurityValidator:
    """Enhanced security validation with better protection."""

    @staticmethod
    def validate_regex_pattern(pattern: str, timeout: int = 5) -> Tuple[bool, str]:
        """Validate regex pattern for safety and performance."""
        try:
            # Check for potentially dangerous patterns
            dangerous_patterns = [
                r"\(\?\#.*\)",  # Comments in regex
                r"\(\?\w*:.*\)",  # Non-capturing groups with modifiers
                r"(\w\{\d+,\}){5,}",  # Excessive repetition
                r"\(\?\w*\)",  # Modifiers
            ]

            for danger in dangerous_patterns:
                if re.search(danger, pattern):
                    return False, "Potentially dangerous regex pattern detected"

            # Test compilation and basic matching
            compiled = re.compile(pattern, re.IGNORECASE | re.MULTILINE)

            # Test with sample text to check for catastrophic backtracking
            test_text = "a" * 1000 + "b" * 1000
            start_time = time.time()
            try:
                compiled.search(test_text)
                if time.time() - start_time > timeout:
                    return False, "Pattern takes too long to execute"
            except:
                return False, "Pattern failed safety test"

            return True, "Valid pattern"

        except re.error as e:
            return False, f"Invalid regex: {e}"
        except Exception as e:
            return False, f"Pattern validation error: {e}"

    @staticmethod
    def is_safe_path(path: str, base_dir: str) -> bool:
        """Enhanced path validation."""
        try:
            path_obj = Path(path).resolve()
            base_obj = Path(base_dir).resolve()

            # Check path length
            if len(str(path_obj)) > 1000:  # Increased limit
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
    def check_memory_usage() -> Tuple[float, bool]:
        """Check current memory usage."""
        memory = psutil.virtual_memory()
        memory_used_gb = memory.used / (1024**3)
        memory_percent = memory.percent

        # Warning if using more than 80% of available memory
        is_safe = memory_percent < 80

        return memory_used_gb, is_safe


class AdvancedContentAnalyzer:
    """Advanced content analyzer with enhanced capabilities."""

    def __init__(
        self,
        keywords: List[str],
        base_directory: str,
        config: AdvancedAnalysisConfig = None,
        interrupt_handler: InterruptHandler = None,
    ):
        """Initialize advanced analyzer."""
        self.setup_logging()

        # Configuration
        self.config = config or AdvancedAnalysisConfig()
        self.base_directory = str(Path(base_directory).resolve())

        if not os.path.isdir(self.base_directory):
            raise ValueError(f"Invalid base directory: {base_directory}")

        # Keywords and patterns
        self.keywords = [kw.strip() for kw in keywords if kw.strip()]
        self.keyword_patterns = {}
        self.regex_patterns = {}
        self.predefined_patterns = {}

        # Results and statistics
        self.results: List[AdvancedAnalysisResult] = []
        self.processing_stats = {
            "files_processed": 0,
            "files_skipped": 0,
            "total_size_processed": 0,
            "total_processing_time": 0,
            "memory_warnings": 0,
            "chunks_processed": 0,
            "interrupted": False,
        }

        # Progress tracking and interruption handling
        self.progress_tracker = None
        self.interrupt_handler = interrupt_handler
        if self.interrupt_handler:
            self.interrupt_handler.register_analyzer(self)

        # Compile keyword patterns
        self._compile_keyword_patterns()

        # Load predefined patterns
        self._load_predefined_patterns()

        # Auto-detect hardware and optimize settings
        self.hardware_info = None
        if self.config.auto_detect_workers:
            self._auto_configure_performance()

        self.logger.info("Advanced analyzer initialized:")
        self.logger.info(f"  - Keywords: {len(self.keyword_patterns)}")
        self.logger.info(f"  - Predefined patterns: {len(self.predefined_patterns)}")
        self.logger.info(f"  - Max files: {self.config.max_files:,}")
        self.logger.info(f"  - Max file size: {self.config.max_file_size_mb}MB")
        self.logger.info(f"  - Streaming enabled: {self.config.enable_streaming}")
        self.logger.info(
            f"  - Workers: {self.config.parallel_workers} {'(auto-detected)' if self.config.auto_detect_workers else '(manual)'}"
        )

    def setup_logging(self):
        """Configure enhanced logging."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler("advanced_analyzer.log", encoding="utf-8"),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def _auto_configure_performance(self):
        """Auto-configure performance settings based on hardware detection."""
        try:
            # Get initial file count estimate for better recommendations
            files = self.discover_files(self.base_directory)
            file_count = len(files) if files else 100  # Default estimate

            # Calculate total size estimate
            total_size_mb = 0
            if files:
                # Sample first 10 files to estimate average size
                sample_files = files[: min(10, len(files))]
                sample_sizes = []
                for file_path in sample_files:
                    try:
                        size_bytes = os.path.getsize(file_path)
                        sample_sizes.append(size_bytes)
                    except:
                        continue

                if sample_sizes:
                    avg_size_bytes = sum(sample_sizes) / len(sample_sizes)
                    total_size_mb = (avg_size_bytes * file_count) / (1024 * 1024)

            # Get performance recommendations
            perf_data = HardwareDetector.get_performance_recommendations(
                file_count, total_size_mb
            )
            self.hardware_info = perf_data["hardware"]
            recommendations = perf_data["recommendations"]

            # Apply recommendations to config
            self.config.parallel_workers = recommendations["workers"]
            self.config.batch_size = recommendations["batch_size"]
            self.config.memory_check_interval = recommendations["memory_check_interval"]
            self.config.enable_streaming = recommendations["enable_streaming"]

            # Log hardware detection results
            hw = self.hardware_info
            self.logger.info("🔧 Hardware detected:")
            self.logger.info(
                f"  - CPU: {hw['cpu_cores']} cores, {hw['memory_gb']:.1f}GB RAM"
            )

            if hw["has_gpu"] and hw["gpu_info"]:
                gpu_names = [gpu["name"] for gpu in hw["gpu_info"]]
                self.logger.info(f"  - GPU: {', '.join(gpu_names)}")

            self.logger.info("⚡ Performance optimized:")
            self.logger.info(
                f"  - Workers: {recommendations['workers']} (I/O: {hw['io_bound_workers']}, CPU: {hw['cpu_bound_workers']})"
            )
            self.logger.info(f"  - Batch size: {recommendations['batch_size']}")
            self.logger.info(
                f"  - Estimated files: {file_count:,}, Size: {total_size_mb:.1f}MB"
            )

        except Exception as e:
            self.logger.warning(f"Hardware auto-detection failed: {e}")
            self.logger.info("Using default performance settings")

    def _compile_keyword_patterns(self):
        """Compile keyword patterns with validation."""
        for keyword in self.keywords:
            try:
                # Escape keyword for safe regex
                escaped_kw = re.escape(keyword)
                flags = re.MULTILINE
                if not self.config.case_sensitive_regex:
                    flags |= re.IGNORECASE

                pattern = re.compile(rf"\b{escaped_kw}\b", flags)
                self.keyword_patterns[keyword] = pattern
            except re.error as e:
                self.logger.warning(f"Invalid keyword '{keyword}': {e}")

    def _load_predefined_patterns(self):
        """Load and compile predefined patterns."""
        all_patterns = AdvancedPatternLibrary.get_all_patterns()

        for name, pattern in all_patterns.items():
            is_valid, error_msg = AdvancedSecurityValidator.validate_regex_pattern(
                pattern
            )
            if is_valid:
                try:
                    flags = re.MULTILINE
                    if not self.config.case_sensitive_regex:
                        flags |= re.IGNORECASE
                    compiled = re.compile(pattern, flags)
                    self.predefined_patterns[name] = compiled
                except re.error as e:
                    self.logger.warning(
                        f"Failed to compile predefined pattern '{name}': {e}"
                    )
            else:
                self.logger.warning(
                    f"Skipping unsafe predefined pattern '{name}': {error_msg}"
                )

    def add_custom_regex_patterns(self, patterns: Dict[str, str]) -> Dict[str, str]:
        """Add custom regex patterns with validation."""
        results = {}

        for name, pattern in patterns.items():
            if len(self.regex_patterns) >= self.config.max_regex_patterns:
                self.logger.warning(
                    f"Maximum regex patterns limit reached ({self.config.max_regex_patterns})"
                )
                break

            is_valid, error_msg = AdvancedSecurityValidator.validate_regex_pattern(
                pattern, self.config.regex_timeout_seconds
            )

            if is_valid:
                try:
                    flags = re.MULTILINE
                    if not self.config.case_sensitive_regex:
                        flags |= re.IGNORECASE
                    compiled = re.compile(pattern, flags)
                    self.regex_patterns[name] = compiled
                    results[name] = "Added successfully"
                except re.error as e:
                    results[name] = f"Compilation error: {e}"
            else:
                results[name] = f"Validation failed: {error_msg}"

        self.logger.info(
            f"Added {len([r for r in results.values() if 'successfully' in r])} custom regex patterns"
        )
        return results

    def discover_files(self, directory: str) -> List[str]:
        """Discover files for analysis with enhanced filtering."""
        files = []

        try:
            for file_path in Path(directory).rglob("*"):
                if len(files) >= self.config.max_files:
                    self.logger.warning(f"File limit reached ({self.config.max_files})")
                    break

                if (
                    file_path.is_file()
                    and file_path.suffix.lower() in ALLOWED_EXTENSIONS
                    and AdvancedSecurityValidator.is_safe_path(
                        str(file_path), self.base_directory
                    )
                ):
                    # Check file size
                    file_size = file_path.stat().st_size
                    max_size_bytes = self.config.max_file_size_mb * 1024 * 1024

                    if file_size <= max_size_bytes:
                        files.append(str(file_path))
                    else:
                        self.logger.debug(
                            f"Skipping large file: {file_path} ({file_size:,} bytes)"
                        )
                        self.processing_stats["files_skipped"] += 1

        except Exception as e:
            self.logger.error(f"Error discovering files: {e}")

        self.logger.info(f"Discovered {len(files):,} files for analysis")
        return files

    def analyze_text_streaming(
        self, file_path: str, file_size: int
    ) -> AdvancedAnalysisResult:
        """Analyze large files using streaming approach."""
        start_time = time.time()

        # Initialize result
        result = AdvancedAnalysisResult(
            file_name=file_path,  # Store full path, not just basename
            file_size_bytes=file_size,
            processing_time=0.0,
            timestamp=datetime.now().isoformat(),
            total_messages=0,
            total_words=0,
            total_characters=0,
            unique_words=0,
        )

        # Determine if streaming is needed
        max_text_bytes = self.config.max_text_analysis_mb * 1024 * 1024
        use_streaming = self.config.enable_streaming and file_size > max_text_bytes

        if use_streaming:
            self.logger.debug(f"Using streaming analysis for {result.file_name}")
            self._analyze_file_streaming(file_path, result)
        else:
            self.logger.debug(f"Using standard analysis for {result.file_name}")
            self._analyze_file_standard(file_path, result)

        result.processing_time = time.time() - start_time
        result.memory_usage_mb = psutil.Process().memory_info().rss / (1024 * 1024)

        # Add detailed conversation analysis
        self._add_detailed_analysis(file_path, result)

        # Calculate relevance score and priority
        self._calculate_relevance_metrics(result)

        return result

    def _analyze_file_streaming(self, file_path: str, result: AdvancedAnalysisResult):
        """Analyze file using streaming chunks."""
        chunk_size = self.config.chunk_size_kb * 1024
        overlap_size = self.config.overlap_size_kb * 1024

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                previous_chunk = ""
                chunk_number = 0

                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break

                    # Process chunk with overlap
                    text_to_analyze = previous_chunk + chunk
                    self._analyze_text_chunk(text_to_analyze, result, chunk_number)

                    # Keep overlap for next chunk
                    previous_chunk = (
                        chunk[-overlap_size:] if len(chunk) > overlap_size else chunk
                    )
                    chunk_number += 1

                result.chunks_processed = chunk_number

        except Exception as e:
            error_msg = f"Streaming analysis error: {e}"
            result.errors.append(error_msg)
            self.logger.error(f"Failed to analyze {file_path}: {e}")

    def _analyze_file_standard(self, file_path: str, result: AdvancedAnalysisResult):
        """Analyze file using standard approach."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Extract clean text
            if file_path.lower().endswith((".html", ".htm")):
                content = self._extract_text_from_html(content)

            self._analyze_text_chunk(content, result, 0)
            result.chunks_processed = 1

        except Exception as e:
            error_msg = f"Standard analysis error: {e}"
            result.errors.append(error_msg)
            self.logger.error(f"Failed to analyze {file_path}: {e}")

    def _extract_text_from_html(self, html_content: str) -> str:
        """Extract clean text from HTML."""
        if not BS4_AVAILABLE:
            # Fallback: simple regex cleaning
            text = re.sub(r"<[^>]+>", " ", html_content)
            return re.sub(r"\s+", " ", text).strip()

        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove scripts and styles
            for element in soup(["script", "style"]):
                element.decompose()

            return soup.get_text(separator=" ").strip()

        except Exception as e:
            self.logger.warning(f"HTML parsing failed, using fallback: {e}")
            text = re.sub(r"<[^>]+>", " ", html_content)
            return re.sub(r"\s+", " ", text).strip()

    def _analyze_text_chunk(
        self, text: str, result: AdvancedAnalysisResult, chunk_number: int
    ):
        """Analyze a chunk of text and update results."""
        if not text.strip():
            return

        # Basic text statistics
        words = text.split()
        result.total_words += len(words)
        result.total_characters += len(text)

        # Update unique words (approximate for streaming)
        if chunk_number == 0:  # Only for first chunk to avoid memory issues
            unique_words = set(word.lower().strip('.,!?";()[]{}') for word in words)
            result.unique_words = len(unique_words)

            # Generate word frequency for first chunk
            if self.config.generate_statistics:
                word_freq = {}
                for word in words:
                    clean_word = word.lower().strip('.,!?";()[]{}')
                    if len(clean_word) > 2:  # Skip short words
                        word_freq[clean_word] = word_freq.get(clean_word, 0) + 1

                # Keep top 50 words
                result.word_frequency = dict(
                    sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:50]
                )

        # Estimate message count
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        message_indicators = [line for line in lines if ":" in line and len(line) > 10]
        result.total_messages += len(message_indicators)

        # Analyze patterns
        self._analyze_patterns_in_text(text, result)

    def _analyze_patterns_in_text(self, text: str, result: AdvancedAnalysisResult):
        """Analyze all patterns in text chunk."""

        # Analyze keywords
        for keyword, pattern in self.keyword_patterns.items():
            try:
                matches = pattern.findall(text)
                if matches:
                    result.keyword_matches[keyword] = result.keyword_matches.get(
                        keyword, 0
                    ) + len(matches)

                    # Save examples if enabled
                    if self.config.save_match_examples:
                        if keyword not in result.pattern_examples:
                            result.pattern_examples[keyword] = []

                        # Add unique examples up to limit
                        for match in matches[: self.config.max_examples_per_pattern]:
                            if match not in result.pattern_examples[keyword]:
                                result.pattern_examples[keyword].append(match)
                                if (
                                    len(result.pattern_examples[keyword])
                                    >= self.config.max_examples_per_pattern
                                ):
                                    break

            except Exception as e:
                self.logger.warning(f"Error analyzing keyword '{keyword}': {e}")

        # Analyze custom regex patterns
        for pattern_name, pattern in self.regex_patterns.items():
            try:
                matches = pattern.findall(text)
                if matches:
                    if pattern_name not in result.regex_matches:
                        result.regex_matches[pattern_name] = {
                            "count": 0,
                            "examples": [],
                            "unique_matches": (
                                set() if self.config.extract_unique_matches else None
                            ),
                        }

                    result.regex_matches[pattern_name]["count"] += len(matches)

                    # Process matches
                    for match in matches:
                        match_str = str(match) if not isinstance(match, str) else match

                        # Add to unique matches
                        if self.config.extract_unique_matches:
                            result.regex_matches[pattern_name]["unique_matches"].add(
                                match_str
                            )

                        # Add examples
                        if (
                            self.config.save_match_examples
                            and len(result.regex_matches[pattern_name]["examples"])
                            < self.config.max_examples_per_pattern
                        ):
                            if (
                                match_str
                                not in result.regex_matches[pattern_name]["examples"]
                            ):
                                result.regex_matches[pattern_name]["examples"].append(
                                    match_str
                                )

            except Exception as e:
                self.logger.warning(
                    f"Error analyzing regex pattern '{pattern_name}': {e}"
                )

        # Analyze predefined patterns
        for pattern_name, pattern in self.predefined_patterns.items():
            try:
                matches = pattern.findall(text)
                if matches:
                    if pattern_name not in result.regex_matches:
                        result.regex_matches[pattern_name] = {
                            "count": 0,
                            "examples": [],
                            "unique_matches": (
                                set() if self.config.extract_unique_matches else None
                            ),
                        }

                    result.regex_matches[pattern_name]["count"] += len(matches)

                    # Add examples for predefined patterns too
                    if self.config.save_match_examples:
                        for match in matches[:5]:  # Limit examples for predefined
                            match_str = (
                                str(match) if not isinstance(match, str) else match
                            )
                            if (
                                match_str
                                not in result.regex_matches[pattern_name]["examples"]
                                and len(result.regex_matches[pattern_name]["examples"])
                                < 5
                            ):
                                result.regex_matches[pattern_name]["examples"].append(
                                    match_str
                                )

            except Exception as e:
                self.logger.warning(
                    f"Error analyzing predefined pattern '{pattern_name}': {e}"
                )

    def analyze_directory(self, directory: str = None) -> bool:
        """Analyze all files in directory with advanced features."""
        if directory is None:
            directory = self.base_directory

        # Discover files
        files = self.discover_files(directory)
        if not files:
            self.logger.warning("No files found for analysis")
            return False

        # Initialize progress tracker
        self.progress_tracker = ProgressTracker(len(files))

        try:
            # Process files in batches
            batch_size = self.config.batch_size
            total_batches = (len(files) + batch_size - 1) // batch_size

            print(
                f"\n🚀 Starting analysis of {len(files):,} files in {total_batches} batches"
            )
            print(
                f"📊 Configuration: {self.config.max_file_size_mb}MB max, {self.config.parallel_workers} workers"
            )

            successful_analyses = 0

            for batch_num in range(total_batches):
                # Check for interruption before each batch
                if (
                    self.interrupt_handler
                    and self.interrupt_handler.check_interrupted()
                ):
                    self.processing_stats["interrupted"] = True
                    print(
                        f"\n⚠️  Analysis interrupted after {successful_analyses} files"
                    )
                    break

                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, len(files))
                batch_files = files[start_idx:end_idx]

                # Update progress stage
                self.progress_tracker.set_stage(
                    f"Batch {batch_num + 1}/{total_batches}"
                )

                # Check memory before processing batch
                if batch_num % 5 == 0:  # Check every 5 batches
                    memory_gb, is_safe = AdvancedSecurityValidator.check_memory_usage()
                    if not is_safe:
                        self.logger.warning(
                            f"High memory usage detected: {memory_gb:.1f}GB"
                        )
                        self.processing_stats["memory_warnings"] += 1

                        # Force garbage collection
                        import gc

                        gc.collect()

                # Process batch
                batch_results = self._process_batch(batch_files)
                successful_analyses += len(batch_results)
                self.results.extend(batch_results)

            self.processing_stats["files_processed"] = successful_analyses

            # Show final stats
            final_stats = self.progress_tracker.get_stats()
            print(
                f"\n✅ Analysis complete: {successful_analyses:,}/{len(files):,} files processed"
            )
            print(
                f"📊 Total: {final_stats['total_size_mb']:.1f}MB, {final_stats['total_messages']:,} messages, {final_stats['total_matches']:,} matches"
            )
            print(
                f"⏱️  Time: {final_stats['elapsed_time']:.1f}s, Rate: {final_stats['rate_per_second']:.1f} files/s"
            )

            return successful_analyses > 0

        finally:
            # Always close progress tracker
            if self.progress_tracker:
                self.progress_tracker.close()

    def _process_batch(self, files: List[str]) -> List[AdvancedAnalysisResult]:
        """Process a batch of files."""
        results = []

        if self.config.parallel_workers > 1:
            # Parallel processing
            with ThreadPoolExecutor(
                max_workers=self.config.parallel_workers
            ) as executor:
                future_to_file = {}

                for file_path in files:
                    file_size = os.path.getsize(file_path)
                    future = executor.submit(
                        self.analyze_text_streaming, file_path, file_size
                    )
                    future_to_file[future] = file_path

                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                            self.processing_stats[
                                "total_size_processed"
                            ] += result.file_size_bytes

                            # Update progress with detailed info
                            total_matches = sum(result.keyword_matches.values()) + sum(
                                pattern_data.get("count", 0)
                                for pattern_data in result.regex_matches.values()
                            )

                            if self.progress_tracker:
                                self.progress_tracker.update(
                                    file_path,
                                    result.file_size_bytes
                                    / (1024 * 1024),  # Convert to MB
                                    result.total_messages,
                                    total_matches,
                                )
                    except Exception as e:
                        self.logger.error(f"Failed to process {file_path}: {e}")
                        self.processing_stats["files_skipped"] += 1
                        # Still update progress for failed files
                        if self.progress_tracker:
                            self.progress_tracker.update(file_path, 0, 0, 0)
        else:
            # Sequential processing
            for file_path in files:
                # Check for interruption before each file
                if (
                    self.interrupt_handler
                    and self.interrupt_handler.check_interrupted()
                ):
                    break

                try:
                    file_size = os.path.getsize(file_path)
                    result = self.analyze_text_streaming(file_path, file_size)
                    if result:
                        results.append(result)
                        self.processing_stats[
                            "total_size_processed"
                        ] += result.file_size_bytes

                        # Update progress with detailed info
                        total_matches = sum(result.keyword_matches.values()) + sum(
                            pattern_data.get("count", 0)
                            for pattern_data in result.regex_matches.values()
                        )

                        if self.progress_tracker:
                            self.progress_tracker.update(
                                file_path,
                                result.file_size_bytes / (1024 * 1024),  # Convert to MB
                                result.total_messages,
                                total_matches,
                            )
                except Exception as e:
                    self.logger.error(f"Failed to process {file_path}: {e}")
                    self.processing_stats["files_skipped"] += 1
                    # Still update progress for failed files
                    if self.progress_tracker:
                        self.progress_tracker.update(file_path, 0, 0, 0)

        return results

    def _add_detailed_analysis(self, file_path: str, result: AdvancedAnalysisResult):
        """Add detailed conversation analysis to result."""
        try:
            # Read file content for detailed analysis (sample for performance)
            sample_text = ""
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                sample_text = f.read(50000)  # First 50KB for analysis

            # Get conversation insights
            matches_dict = {
                "keyword_matches": result.keyword_matches,
                "regex_matches": result.regex_matches,
            }

            result.conversation_insights = (
                ConversationAnalyzer.analyze_conversation_details(
                    sample_text, file_path, matches_dict
                )
            )

            # Extract chat metadata
            result.chat_metadata = {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_extension": Path(file_path).suffix,
                "analysis_timestamp": datetime.now().isoformat(),
            }

            # Analyze content categories (themes)
            themes = result.conversation_insights.get("content_themes", {})
            result.content_categories = themes

            # Add context for matches (sample)
            if result.keyword_matches or result.regex_matches:
                result.match_contexts = self._extract_match_contexts(
                    sample_text, result
                )

        except Exception as e:
            result.errors.append(f"Detailed analysis error: {e}")
            self.logger.warning(f"Failed detailed analysis for {file_path}: {e}")

    def _extract_match_contexts(
        self, text: str, result: AdvancedAnalysisResult
    ) -> Dict[str, List[Dict]]:
        """Extract context around matches for better understanding."""
        contexts = {}

        # Sample lines for context extraction
        lines = text.split("\n")[:1000]  # First 1000 lines for performance

        try:
            # Extract context for keyword matches
            for keyword in result.keyword_matches.keys():
                keyword_contexts = []
                keyword_lower = keyword.lower()

                for i, line in enumerate(lines):
                    if keyword_lower in line.lower():
                        context = {
                            "line_number": i + 1,
                            "context": line.strip()[:200],  # Limit context length
                            "surrounding_lines": [],
                        }

                        # Add surrounding lines for context
                        for offset in [-1, 1]:
                            surr_idx = i + offset
                            if 0 <= surr_idx < len(lines):
                                context["surrounding_lines"].append(
                                    lines[surr_idx].strip()[:100]
                                )

                        keyword_contexts.append(context)

                        # Limit contexts per keyword
                        if len(keyword_contexts) >= 5:
                            break

                if keyword_contexts:
                    contexts[f"keyword_{keyword}"] = keyword_contexts

        except Exception as e:
            result.errors.append(f"Context extraction error: {e}")

        return contexts

    def _calculate_relevance_metrics(self, result: AdvancedAnalysisResult):
        """Calculate relevance score and priority level for the chat."""
        try:
            # Base relevance calculation
            total_matches = sum(result.keyword_matches.values())
            total_regex_matches = sum(
                pattern_data.get("count", 0)
                for pattern_data in result.regex_matches.values()
            )

            # Normalize by file size
            file_size_factor = max(1, result.file_size_bytes / (1024 * 1024))  # MB
            match_density = (
                total_matches + total_regex_matches * 0.1
            ) / file_size_factor

            # Content theme bonus
            themes = result.content_categories
            theme_score = 0
            high_value_themes = ["work_related", "personal_family", "emotional_content"]
            for theme in high_value_themes:
                theme_score += min(
                    themes.get(theme, 0) / 10, 5
                )  # Cap at 5 points per theme

            # Interaction intensity bonus
            intensity = result.conversation_insights.get("interaction_intensity", {})
            intensity_bonus = 0
            if intensity.get("level") == "high":
                intensity_bonus = 10
            elif intensity.get("level") == "medium":
                intensity_bonus = 5

            # Participant count factor
            participants = result.conversation_insights.get(
                "estimated_participants", {}
            )
            participant_factor = 1
            if participants.get("is_group_chat"):
                participant_factor = 1.5  # Group chats might be more relevant

            # Calculate final relevance score (0-1 scale)
            raw_score = (
                match_density + theme_score + intensity_bonus
            ) * participant_factor
            result.relevance_score = min(raw_score / 100, 1.0)  # Normalize to 0-1

            # Determine priority level
            if result.relevance_score >= 0.8 or total_matches >= 100:
                result.priority_level = "critical"
            elif result.relevance_score >= 0.5 or total_matches >= 50:
                result.priority_level = "high"
            elif result.relevance_score >= 0.2 or total_matches >= 10:
                result.priority_level = "medium"
            else:
                result.priority_level = "low"

        except Exception as e:
            result.errors.append(f"Relevance calculation error: {e}")
            result.relevance_score = 0.0
            result.priority_level = "low"

    def generate_comprehensive_summary(self) -> Dict:
        """Generate comprehensive analysis summary."""
        if not self.results:
            return {"error": "No results to summarize"}

        # Basic statistics
        total_files = len(self.results)
        total_messages = sum(r.total_messages for r in self.results)
        total_words = sum(r.total_words for r in self.results)
        total_chars = sum(r.total_characters for r in self.results)
        total_size_mb = sum(r.file_size_bytes for r in self.results) / (1024 * 1024)
        avg_processing_time = sum(r.processing_time for r in self.results) / total_files

        # Aggregate keyword matches
        all_keywords = {}
        for result in self.results:
            for keyword, count in result.keyword_matches.items():
                all_keywords[keyword] = all_keywords.get(keyword, 0) + count

        # Aggregate regex matches
        all_regex = {}
        for result in self.results:
            for pattern_name, pattern_data in result.regex_matches.items():
                if pattern_name not in all_regex:
                    all_regex[pattern_name] = {
                        "total_count": 0,
                        "files_with_matches": 0,
                        "unique_matches": set(),
                    }

                all_regex[pattern_name]["total_count"] += pattern_data["count"]
                if pattern_data["count"] > 0:
                    all_regex[pattern_name]["files_with_matches"] += 1

                # Aggregate unique matches if available
                if pattern_data.get("unique_matches"):
                    all_regex[pattern_name]["unique_matches"].update(
                        pattern_data["unique_matches"]
                    )

        # Convert sets to counts for JSON serialization
        for pattern_name in all_regex:
            unique_count = len(all_regex[pattern_name]["unique_matches"])
            all_regex[pattern_name]["unique_matches_count"] = unique_count
            del all_regex[pattern_name][
                "unique_matches"
            ]  # Remove set for JSON compatibility

        # Top patterns
        top_keywords = dict(
            sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)[:20]
        )
        top_regex = dict(
            sorted(all_regex.items(), key=lambda x: x[1]["total_count"], reverse=True)[
                :20
            ]
        )

        # Files with matches
        files_with_keyword_matches = len([r for r in self.results if r.keyword_matches])
        files_with_regex_matches = len([r for r in self.results if r.regex_matches])

        # Word frequency analysis
        combined_word_freq = {}
        for result in self.results:
            for word, freq in result.word_frequency.items():
                combined_word_freq[word] = combined_word_freq.get(word, 0) + freq

        top_words = dict(
            sorted(combined_word_freq.items(), key=lambda x: x[1], reverse=True)[:50]
        )

        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "configuration": {
                "max_files": self.config.max_files,
                "max_file_size_mb": self.config.max_file_size_mb,
                "streaming_enabled": self.config.enable_streaming,
                "parallel_workers": self.config.parallel_workers,
                "custom_regex_enabled": self.config.enable_custom_regex,
            },
            "processing_statistics": {
                "files_processed": total_files,
                "files_skipped": self.processing_stats["files_skipped"],
                "total_size_mb": round(total_size_mb, 2),
                "total_processing_time_seconds": round(
                    sum(r.processing_time for r in self.results), 2
                ),
                "average_processing_time": round(avg_processing_time, 2),
                "chunks_processed": sum(r.chunks_processed for r in self.results),
                "memory_warnings": self.processing_stats["memory_warnings"],
            },
            "content_statistics": {
                "total_messages": total_messages,
                "total_words": total_words,
                "total_characters": total_chars,
                "average_messages_per_file": (
                    round(total_messages / total_files, 1) if total_files > 0 else 0
                ),
                "average_words_per_file": (
                    round(total_words / total_files, 1) if total_files > 0 else 0
                ),
                "average_file_size_kb": (
                    round((total_size_mb * 1024) / total_files, 1)
                    if total_files > 0
                    else 0
                ),
            },
            "pattern_analysis": {
                "keyword_patterns": {
                    "total_patterns": len(self.keyword_patterns),
                    "files_with_matches": files_with_keyword_matches,
                    "top_matches": top_keywords,
                },
                "regex_patterns": {
                    "custom_patterns": len(self.regex_patterns),
                    "predefined_patterns": len(self.predefined_patterns),
                    "files_with_matches": files_with_regex_matches,
                    "top_matches": top_regex,
                },
                "word_frequency": {
                    "top_words": top_words,
                    "unique_words_analyzed": len(combined_word_freq),
                },
            },
            "keywords_searched": self.keywords,
        }

    def save_results(self, output_dir: str = "advanced_analysis_results") -> bool:
        """Save comprehensive results."""
        try:
            output_path = Path(output_dir).resolve()

            if not AdvancedSecurityValidator.is_safe_path(
                str(output_path), os.getcwd()
            ):
                self.logger.error(f"Unsafe output directory: {output_dir}")
                return False

            output_path.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Generate comprehensive summary
            summary = self.generate_comprehensive_summary()

            # Prepare detailed results for JSON (handle sets)
            detailed_results = []
            for result in self.results:
                result_dict = asdict(result)

                # Convert sets to lists for JSON serialization
                for pattern_name, pattern_data in result_dict.get(
                    "regex_matches", {}
                ).items():
                    if isinstance(pattern_data.get("unique_matches"), set):
                        pattern_data["unique_matches"] = list(
                            pattern_data["unique_matches"]
                        )

                detailed_results.append(result_dict)

            # Save comprehensive JSON report
            json_file = output_path / f"advanced_analysis_{timestamp}.json"
            report_data = {
                "summary": summary,
                "configuration": asdict(self.config),
                "detailed_results": detailed_results,
                "processing_statistics": self.processing_stats,
            }

            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            # Save enhanced text summary
            txt_file = output_path / f"advanced_summary_{timestamp}.txt"
            with open(txt_file, "w", encoding="utf-8") as f:
                f.write("ADVANCED WHATSAPP CHAT ANALYSIS REPORT\n")
                f.write("=" * 60 + "\n\n")

                # Configuration
                f.write("CONFIGURATION:\n")
                f.write("-" * 20 + "\n")
                config_info = summary["configuration"]
                for key, value in config_info.items():
                    f.write(f"{key.replace('_', ' ').title()}: {value}\n")
                f.write("\n")

                # Processing statistics
                f.write("PROCESSING STATISTICS:\n")
                f.write("-" * 25 + "\n")
                proc_stats = summary["processing_statistics"]
                for key, value in proc_stats.items():
                    f.write(f"{key.replace('_', ' ').title()}: {value:,}\n")
                f.write("\n")

                # Content statistics
                f.write("CONTENT STATISTICS:\n")
                f.write("-" * 22 + "\n")
                content_stats = summary["content_statistics"]
                for key, value in content_stats.items():
                    f.write(f"{key.replace('_', ' ').title()}: {value:,}\n")
                f.write("\n")

                # Pattern analysis
                f.write("PATTERN ANALYSIS:\n")
                f.write("-" * 20 + "\n")

                # Top keywords
                keyword_matches = summary["pattern_analysis"]["keyword_patterns"][
                    "top_matches"
                ]
                if keyword_matches:
                    f.write("Top Keyword Matches:\n")
                    for keyword, count in list(keyword_matches.items())[:10]:
                        f.write(f"  - {keyword}: {count:,}\n")
                    f.write("\n")

                # Top regex patterns
                regex_matches = summary["pattern_analysis"]["regex_patterns"][
                    "top_matches"
                ]
                if regex_matches:
                    f.write("Top Regex Pattern Matches:\n")
                    for pattern, data in list(regex_matches.items())[:10]:
                        f.write(
                            f"  - {pattern}: {data['total_count']:,} matches in {data['files_with_matches']} files\n"
                        )
                    f.write("\n")

                # Top words
                top_words = summary["pattern_analysis"]["word_frequency"]["top_words"]
                if top_words:
                    f.write("Most Frequent Words:\n")
                    for word, freq in list(top_words.items())[:20]:
                        f.write(f"  - {word}: {freq:,}\n")
                    f.write("\n")

            self.logger.info("Advanced analysis results saved:")
            self.logger.info(f"  JSON report: {json_file}")
            self.logger.info(f"  Text summary: {txt_file}")
            self.logger.info(f"  Output directory: {output_path}")

            # Extract relevant chats
            self._extract_relevant_chats(output_path)

            return True

        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
            return False

    def _extract_relevant_chats(self, output_path: Path):
        """Extract and copy relevant chats based on analysis results."""
        try:
            # Filter results that have enough matches to be considered relevant
            relevant_results = [
                result
                for result in self.results
                if (
                    sum(result.keyword_matches.values()) >= 5
                    or result.relevance_score >= 0.2
                    or result.priority_level in ["medium", "high", "critical"]
                )
            ]

            if not relevant_results:
                self.logger.info("No chats met relevance criteria for extraction")
                return

            # Initialize extractor
            extractor = RelevantChatExtractor(str(output_path))

            # Custom extraction criteria
            criteria = {
                "min_matches": 3,  # Lower threshold for broader capture
                "min_relevance_score": 0.1,
                "priority_levels": ["medium", "high", "critical"],
                "required_themes": None,  # Accept any themes
            }

            # Extract relevant chats
            extraction_stats = extractor.extract_relevant_chats(self.results, criteria)

            self.logger.info("📋 Relevant chat extraction complete:")
            self.logger.info(
                f"  Chats extracted: {extraction_stats['total_relevant']}/{extraction_stats['total_analyzed']}"
            )
            self.logger.info(
                f"  Extraction rate: {(extraction_stats['total_relevant']/extraction_stats['total_analyzed']*100):.1f}%"
            )
            self.logger.info(
                f"  Relevant chats directory: {output_path}/relevant_chats/"
            )

            # Print quick summary
            if extraction_stats["total_relevant"] > 0:
                print("\n📋 RELEVANT CHATS EXTRACTED:")
                print(f"   Total relevant: {extraction_stats['total_relevant']}")
                print(f"   High priority: {output_path}/relevant_chats/high_priority/")
                print(
                    f"   Medium priority: {output_path}/relevant_chats/medium_priority/"
                )
                print(
                    f"   Individual summaries: {output_path}/relevant_chats/summaries/"
                )
                print(
                    f"   Master summary: {output_path}/relevant_chats/MASTER_SUMMARY.txt"
                )

        except Exception as e:
            self.logger.error(f"Failed to extract relevant chats: {e}")


def load_config_from_file(config_file: str) -> AdvancedAnalysisConfig:
    """Load configuration from JSON file."""
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        # Extract configuration parameters
        config_params = config_data.get("advanced_config", {})

        return AdvancedAnalysisConfig(**config_params)

    except Exception as e:
        print(f"Error loading config file: {e}")
        print("Using default configuration")
        return AdvancedAnalysisConfig()


def create_advanced_sample_config():
    """Create an advanced sample configuration file."""
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
            "urgent",
            "important",
            "help",
        ],
        "custom_regex_patterns": {
            "phone_numbers": r"\+?[\d\s\-\(\)]{10,}",
            "email_addresses": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "urls": r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            "dates": r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
            "times": r"\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?",
            "money_amounts": r"\$?\d+(?:,\d{3})*(?:\.\d{2})?",
            "social_handles": r"@\w+",
            "hashtags": r"#\w+",
        },
        "predefined_pattern_categories": ["communication", "whatsapp", "content"],
        "advanced_config": {
            "max_files": 10000,
            "max_file_size_mb": 500,
            "max_text_analysis_mb": 50,
            "max_total_memory_gb": 8,
            "chunk_size_kb": 2048,
            "overlap_size_kb": 4,
            "enable_streaming": True,
            "enable_custom_regex": True,
            "max_regex_patterns": 100,
            "regex_timeout_seconds": 10,
            "case_sensitive_regex": False,
            "parallel_workers": 4,
            "batch_size": 200,
            "memory_check_interval": 50,
            "save_match_examples": True,
            "max_examples_per_pattern": 20,
            "generate_statistics": True,
            "extract_unique_matches": True,
        },
        "description": "Advanced configuration for comprehensive WhatsApp chat analysis with enhanced regex support and large dataset processing capabilities",
    }

    config_file = "advanced_analyzer_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"Advanced configuration created: {config_file}")


def main():
    """Main function with enhanced CLI interface."""
    parser = argparse.ArgumentParser(
        description="Advanced WhatsApp Chat Content Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python advanced_content_analyzer.py /path/to/chat/exports
  python advanced_content_analyzer.py /path/to/exports --config advanced_config.json
  python advanced_content_analyzer.py /path/to/exports --keywords love,family,work --regex-patterns
  python advanced_content_analyzer.py --create-config
  python advanced_content_analyzer.py /path/to/exports --parallel-workers 8 --max-files 50000
        """,
    )

    parser.add_argument(
        "directory", nargs="?", help="Directory containing chat export files"
    )

    parser.add_argument(
        "--config", "-c", help="JSON configuration file with advanced settings"
    )

    parser.add_argument(
        "--keywords", "-k", help="Comma-separated list of keywords to search for"
    )

    parser.add_argument(
        "--regex-patterns",
        "-r",
        help="JSON file or string containing custom regex patterns",
    )

    parser.add_argument(
        "--output",
        "-o",
        default="advanced_analysis_results",
        help="Output directory for results (default: advanced_analysis_results)",
    )

    parser.add_argument(
        "--create-config",
        action="store_true",
        help="Create an advanced sample configuration file",
    )

    parser.add_argument(
        "--max-files",
        type=int,
        help=f"Maximum number of files to process (default: {DEFAULT_MAX_FILES:,})",
    )

    parser.add_argument(
        "--max-file-size",
        type=int,
        help=f"Maximum file size in MB (default: {DEFAULT_MAX_FILE_SIZE_MB})",
    )

    parser.add_argument(
        "--parallel-workers",
        type=int,
        help="Number of parallel processing workers (default: auto-detect)",
    )

    parser.add_argument(
        "--disable-auto-workers",
        action="store_true",
        help="Disable automatic worker detection (use manual --parallel-workers)",
    )

    parser.add_argument(
        "--enable-streaming",
        action="store_true",
        default=True,
        help="Enable streaming analysis for large files (default: True)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.create_config:
        create_advanced_sample_config()
        return

    if not args.directory:
        parser.error("Directory argument is required unless using --create-config")

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load configuration
    if args.config:
        config = load_config_from_file(args.config)
    else:
        config = AdvancedAnalysisConfig()

    # Override config with command line arguments
    if args.max_files:
        config.max_files = args.max_files
    if args.max_file_size:
        config.max_file_size_mb = args.max_file_size

    # Handle worker configuration
    if args.disable_auto_workers:
        config.auto_detect_workers = False
        if args.parallel_workers:
            config.parallel_workers = args.parallel_workers
        else:
            config.parallel_workers = 4  # Default manual value
    elif args.parallel_workers:
        # Manual override provided
        config.auto_detect_workers = False
        config.parallel_workers = args.parallel_workers
    else:
        # Use auto-detection (default)
        config.auto_detect_workers = True

    if args.enable_streaming is not None:
        config.enable_streaming = args.enable_streaming

    # Load keywords
    keywords = []
    if args.config:
        try:
            with open(args.config, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                keywords = config_data.get("keywords", [])
        except Exception as e:
            print(f"Error loading keywords from config: {e}")

    if args.keywords:
        additional_keywords = [kw.strip() for kw in args.keywords.split(",")]
        keywords.extend(additional_keywords)

    if not keywords:
        # Default keywords for demo
        keywords = [
            "meeting",
            "call",
            "video",
            "photo",
            "happy",
            "work",
            "family",
            "important",
            "urgent",
            "love",
            "help",
            "travel",
            "food",
        ]
        print("Using default keywords for analysis")

    try:
        # Initialize interrupt handler
        interrupt_handler = InterruptHandler()

        # Create advanced analyzer
        print("Initializing Advanced Content Analyzer...")
        print(f"  Max files: {config.max_files:,}")
        print(f"  Max file size: {config.max_file_size_mb}MB")
        print(f"  Streaming: {config.enable_streaming}")
        print(f"  Workers: {config.parallel_workers}")
        print("💡 Press Ctrl+C to gracefully stop analysis and save partial results")

        analyzer = AdvancedContentAnalyzer(
            keywords, args.directory, config, interrupt_handler
        )

        # Add custom regex patterns if provided
        if args.regex_patterns:
            try:
                if os.path.isfile(args.regex_patterns):
                    with open(args.regex_patterns, "r", encoding="utf-8") as f:
                        regex_data = json.load(f)
                else:
                    regex_data = json.loads(args.regex_patterns)

                if isinstance(regex_data, dict):
                    results = analyzer.add_custom_regex_patterns(regex_data)
                    print(f"Custom regex patterns loaded: {len(results)} patterns")

            except Exception as e:
                print(f"Error loading regex patterns: {e}")

        # Load patterns from config file
        if args.config:
            try:
                with open(args.config, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    custom_patterns = config_data.get("custom_regex_patterns", {})
                    if custom_patterns:
                        results = analyzer.add_custom_regex_patterns(custom_patterns)
                        print(f"Config regex patterns loaded: {len(results)} patterns")
            except Exception as e:
                print(f"Error loading regex patterns from config: {e}")

        # Run analysis
        print(f"\nStarting analysis of directory: {args.directory}")
        start_time = time.time()

        success = analyzer.analyze_directory()

        analysis_time = time.time() - start_time

        if success and analyzer.results:
            # Save results
            print("\nSaving results...")
            analyzer.save_results(args.output)

            # Display comprehensive summary
            summary = analyzer.generate_comprehensive_summary()

            # Check if analysis was interrupted
            if analyzer.processing_stats.get("interrupted", False):
                print(f"\n{'=' * 80}")
                print("⚠️  ANALYSIS INTERRUPTED - PARTIAL RESULTS")
                print(f"{'=' * 80}")
            else:
                print(f"\n{'=' * 80}")
                print("🚀 ADVANCED ANALYSIS COMPLETE")
                print(f"{'=' * 80}")

            # Processing stats
            proc_stats = summary["processing_statistics"]
            print("📊 Processing Statistics:")
            print(f"   Files processed: {proc_stats['files_processed']:,}")
            print(f"   Files skipped: {proc_stats['files_skipped']:,}")
            print(f"   Total size: {proc_stats['total_size_mb']:,} MB")
            print(f"   Processing time: {analysis_time:.1f} seconds")
            print(f"   Chunks processed: {proc_stats['chunks_processed']:,}")

            if analyzer.processing_stats.get("interrupted", False):
                print("   ⚠️  Status: INTERRUPTED")

            # Content stats
            content_stats = summary["content_statistics"]
            print("\n📝 Content Statistics:")
            print(f"   Total messages: {content_stats['total_messages']:,}")
            print(f"   Total words: {content_stats['total_words']:,}")
            print(f"   Total characters: {content_stats['total_characters']:,}")
            print(
                f"   Avg messages/file: {content_stats['average_messages_per_file']:,}"
            )

            # Pattern matches
            pattern_analysis = summary["pattern_analysis"]

            if pattern_analysis["keyword_patterns"]["top_matches"]:
                print("\n🎯 Top Keyword Matches:")
                for keyword, count in list(
                    pattern_analysis["keyword_patterns"]["top_matches"].items()
                )[:5]:
                    print(f"   • {keyword}: {count:,}")

            if pattern_analysis["regex_patterns"]["top_matches"]:
                print("\n🔍 Top Regex Pattern Matches:")
                for pattern, data in list(
                    pattern_analysis["regex_patterns"]["top_matches"].items()
                )[:5]:
                    print(
                        f"   • {pattern}: {data['total_count']:,} matches in {data['files_with_matches']} files"
                    )

            print(f"\n📁 Results saved to: {os.path.abspath(args.output)}")
            print(f"{'=' * 80}")

        elif analyzer.results:
            # Analysis was interrupted but we have some results
            print("\n⚠️  Analysis was interrupted but partial results are available")
            print(f"📊 Processed {len(analyzer.results)} files before interruption")
        else:
            print("Analysis completed but no results were generated.")

    except Exception as e:
        print(f"Error during analysis: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    main()
