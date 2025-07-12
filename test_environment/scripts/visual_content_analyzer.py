#!/usr/bin/env python3
"""
Visual WhatsApp Chat Content Analyzer - Enhanced UI Version

A visually enhanced analyzer with:
- Real-time progress bars
- Time estimation and ETA
- Colorized output
- File processing status
- Memory usage monitoring
- Detailed progress reporting
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import psutil

# Enhanced progress and visual libraries
try:
    from rich import box
    from rich.columns import Columns
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        TaskID,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback for basic progress
    print("⚠️  Para mejor experiencia visual, instala: pip install rich")

try:
    from bs4 import BeautifulSoup

    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

# Import the advanced analyzer base
from advanced_content_analyzer import (
    ALLOWED_EXTENSIONS,
    AdvancedAnalysisConfig,
    AdvancedAnalysisResult,
    AdvancedPatternLibrary,
    AdvancedSecurityValidator,
)


class VisualProgressTracker:
    """Enhanced progress tracking with visual indicators."""

    def __init__(self, use_rich=True):
        self.use_rich = use_rich and RICH_AVAILABLE
        self.console = Console() if self.use_rich else None
        self.start_time = None
        self.files_processed = 0
        self.total_files = 0
        self.current_file = ""
        self.errors_count = 0
        self.warnings_count = 0

        # Progress tracking
        self.progress = None
        self.main_task = None
        self.file_task = None
        self.live_display = None

        # Statistics
        self.processing_stats = {
            "files_per_second": 0.0,
            "estimated_completion": None,
            "memory_usage_mb": 0.0,
            "total_patterns_found": 0,
            "current_batch": 0,
            "total_batches": 0,
        }

    def start_analysis(self, total_files: int, total_batches: int = 1):
        """Initialize progress tracking."""
        self.start_time = time.time()
        self.total_files = total_files
        self.files_processed = 0
        self.processing_stats["total_batches"] = total_batches

        if self.use_rich:
            self._start_rich_progress()
        else:
            self._start_basic_progress()

    def _start_rich_progress(self):
        """Start Rich-based progress display."""
        self.progress = Progress(
            TextColumn("[bold blue]Analizando...", justify="right"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            MofNCompleteColumn(),
            "•",
            TimeElapsedColumn(),
            "•",
            TimeRemainingColumn(),
            "•",
            TextColumn("[bold green]{task.description}"),
            console=self.console,
            expand=True,
        )

        self.main_task = self.progress.add_task(
            "Procesando archivos...", total=self.total_files
        )

        # Create layout for live display
        self._create_live_layout()

    def _create_live_layout(self):
        """Create rich live layout with multiple panels."""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=8),
        )

        layout["main"].split_row(
            Layout(name="progress", ratio=2), Layout(name="stats", ratio=1)
        )

        self.layout = layout
        self.live_display = Live(layout, console=self.console, refresh_per_second=2)
        self.live_display.start()

    def _start_basic_progress(self):
        """Start basic text-based progress display."""
        print(f"🚀 Iniciando análisis de {self.total_files} archivos...")
        print("=" * 60)

    def update_progress(
        self,
        files_completed: int = None,
        current_file: str = "",
        patterns_found: int = 0,
        batch_num: int = None,
    ):
        """Update progress display."""
        if files_completed is not None:
            self.files_processed = files_completed

        if current_file:
            self.current_file = os.path.basename(current_file)

        if batch_num is not None:
            self.processing_stats["current_batch"] = batch_num

        self.processing_stats["total_patterns_found"] += patterns_found

        # Calculate statistics
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        if elapsed_time > 0 and self.files_processed > 0:
            self.processing_stats["files_per_second"] = (
                self.files_processed / elapsed_time
            )
            remaining_files = self.total_files - self.files_processed
            eta_seconds = remaining_files / self.processing_stats["files_per_second"]
            self.processing_stats["estimated_completion"] = datetime.now() + timedelta(
                seconds=eta_seconds
            )

        # Memory usage
        self.processing_stats["memory_usage_mb"] = (
            psutil.Process().memory_info().rss / (1024 * 1024)
        )

        if self.use_rich:
            self._update_rich_display()
        else:
            self._update_basic_display()

    def _update_rich_display(self):
        """Update Rich display with current progress."""
        if not self.progress or not self.live_display:
            return

        # Update main progress
        self.progress.update(
            self.main_task,
            completed=self.files_processed,
            description=(
                f"📁 {self.current_file}" if self.current_file else "Procesando..."
            ),
        )

        # Update header
        elapsed = time.time() - self.start_time if self.start_time else 0
        header_text = Text.assemble(
            ("🔍 Analizador Visual de WhatsApp", "bold magenta"),
            (" • ", "dim"),
            (f"Tiempo: {elapsed:.1f}s", "green"),
            (" • ", "dim"),
            (f"Memoria: {self.processing_stats['memory_usage_mb']:.1f}MB", "yellow"),
            (" • ", "dim"),
            (
                f"Velocidad: {self.processing_stats['files_per_second']:.1f} archivos/s",
                "cyan",
            ),
        )

        self.layout["header"].update(
            Panel(header_text, title="Estado del Análisis", border_style="blue")
        )

        # Update main progress area
        self.layout["progress"].update(self.progress)

        # Update statistics panel
        stats_table = self._create_stats_table()
        self.layout["stats"].update(
            Panel(stats_table, title="📊 Estadísticas", border_style="green")
        )

        # Update footer with current file info
        footer_content = self._create_footer_info()
        self.layout["footer"].update(
            Panel(footer_content, title="📄 Información Actual", border_style="yellow")
        )

    def _create_stats_table(self):
        """Create statistics table."""
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Value", style="white")

        table.add_row(
            "📁 Archivos procesados", f"{self.files_processed:,}/{self.total_files:,}"
        )
        table.add_row(
            "📊 Progreso",
            (
                f"{(self.files_processed/self.total_files*100):.1f}%"
                if self.total_files > 0
                else "0%"
            ),
        )
        table.add_row(
            "🎯 Patrones encontrados",
            f"{self.processing_stats['total_patterns_found']:,}",
        )
        table.add_row(
            "⚡ Velocidad", f"{self.processing_stats['files_per_second']:.1f} arch/s"
        )
        table.add_row(
            "💾 Memoria", f"{self.processing_stats['memory_usage_mb']:.1f} MB"
        )

        if self.processing_stats["estimated_completion"]:
            eta = self.processing_stats["estimated_completion"].strftime("%H:%M:%S")
            table.add_row("⏰ ETA", eta)

        if self.processing_stats["total_batches"] > 1:
            table.add_row(
                "📦 Lote actual",
                f"{self.processing_stats['current_batch']}/{self.processing_stats['total_batches']}",
            )

        table.add_row("❌ Errores", f"{self.errors_count}")
        table.add_row("⚠️ Advertencias", f"{self.warnings_count}")

        return table

    def _create_footer_info(self):
        """Create footer information panel."""
        if not self.current_file:
            return Text("Esperando archivo...", style="dim")

        info_text = Text.assemble(
            ("📄 Archivo actual: ", "bold"),
            (self.current_file, "green"),
            ("\n"),
            ("🕒 Tiempo transcurrido: ", "bold"),
            (
                f"{time.time() - self.start_time:.1f}s" if self.start_time else "0s",
                "yellow",
            ),
        )

        if self.processing_stats["estimated_completion"]:
            remaining = self.processing_stats["estimated_completion"] - datetime.now()
            remaining_str = str(remaining).split(".")[0]  # Remove microseconds
            info_text.append(f"\n⏳ Tiempo restante: {remaining_str}")

        return info_text

    def _update_basic_display(self):
        """Update basic text display."""
        if self.total_files > 0:
            percentage = (self.files_processed / self.total_files) * 100
            bar_length = 40
            filled_length = int(bar_length * self.files_processed // self.total_files)
            bar = "█" * filled_length + "-" * (bar_length - filled_length)

            # Clear line and show progress
            print(
                f"\r[{bar}] {percentage:.1f}% ({self.files_processed}/{self.total_files}) - {self.current_file}",
                end="",
                flush=True,
            )

    def log_error(self, message: str):
        """Log an error."""
        self.errors_count += 1
        if self.use_rich:
            self.console.print(f"❌ Error: {message}", style="red")
        else:
            print(f"\n❌ Error: {message}")

    def log_warning(self, message: str):
        """Log a warning."""
        self.warnings_count += 1
        if self.use_rich:
            self.console.print(f"⚠️  Advertencia: {message}", style="yellow")
        else:
            print(f"\n⚠️  Advertencia: {message}")

    def finish_analysis(self, success: bool = True):
        """Finish progress tracking."""
        if self.use_rich:
            self._finish_rich_display(success)
        else:
            self._finish_basic_display(success)

    def _finish_rich_display(self, success: bool):
        """Finish Rich display."""
        if self.live_display:
            self.live_display.stop()

        total_time = time.time() - self.start_time if self.start_time else 0

        if success:
            self.console.print(
                Panel.fit(
                    f"✅ [bold green]¡Análisis Completado![/bold green]\n\n"
                    f"📁 Archivos procesados: [bold]{self.files_processed:,}[/bold]\n"
                    f"🎯 Patrones encontrados: [bold]{self.processing_stats['total_patterns_found']:,}[/bold]\n"
                    f"⏱️  Tiempo total: [bold]{total_time:.1f}s[/bold]\n"
                    f"⚡ Velocidad promedio: [bold]{self.processing_stats['files_per_second']:.1f}[/bold] archivos/s\n"
                    f"💾 Memoria máxima: [bold]{self.processing_stats['memory_usage_mb']:.1f}MB[/bold]",
                    title="🎉 Resumen Final",
                    border_style="green",
                )
            )
        else:
            self.console.print(
                Panel.fit(
                    f"❌ [bold red]Análisis Interrumpido[/bold red]\n\n"
                    f"📁 Archivos procesados: [bold]{self.files_processed:,}[/bold]\n"
                    f"⏱️  Tiempo transcurrido: [bold]{total_time:.1f}s[/bold]\n"
                    f"❌ Errores: [bold]{self.errors_count}[/bold]\n"
                    f"⚠️  Advertencias: [bold]{self.warnings_count}[/bold]",
                    title="⚠️  Análisis Incompleto",
                    border_style="red",
                )
            )

    def _finish_basic_display(self, success: bool):
        """Finish basic display."""
        print()  # New line after progress bar
        print("=" * 60)

        total_time = time.time() - self.start_time if self.start_time else 0

        if success:
            print("✅ ¡Análisis Completado!")
            print(f"📁 Archivos procesados: {self.files_processed:,}")
            print(
                f"🎯 Patrones encontrados: {self.processing_stats['total_patterns_found']:,}"
            )
            print(f"⏱️  Tiempo total: {total_time:.1f}s")
            print(
                f"⚡ Velocidad promedio: {self.processing_stats['files_per_second']:.1f} archivos/s"
            )
        else:
            print("❌ Análisis interrumpido")
            print(f"📁 Archivos procesados: {self.files_processed:,}")
            print(f"❌ Errores: {self.errors_count}")


class VisualAdvancedContentAnalyzer:
    """Visual enhanced version of the advanced content analyzer."""

    def __init__(
        self,
        keywords: List[str],
        base_directory: str,
        config: AdvancedAnalysisConfig = None,
    ):
        """Initialize with visual progress tracking."""
        self.setup_logging()

        # Base analyzer setup (reuse from advanced_content_analyzer)
        self.config = config or AdvancedAnalysisConfig()
        self.base_directory = str(Path(base_directory).resolve())

        if not os.path.isdir(self.base_directory):
            raise ValueError(f"Invalid base directory: {base_directory}")

        # Keywords and patterns
        self.keywords = [kw.strip() for kw in keywords if kw.strip()]
        self.keyword_patterns = {}
        self.regex_patterns = {}
        self.predefined_patterns = {}

        # Visual progress tracker
        self.progress_tracker = VisualProgressTracker(use_rich=RICH_AVAILABLE)

        # Results and statistics
        self.results: List[AdvancedAnalysisResult] = []
        self.processing_stats = {
            "files_processed": 0,
            "files_skipped": 0,
            "total_size_processed": 0,
            "total_processing_time": 0,
            "memory_warnings": 0,
        }

        # Compile patterns
        self._compile_keyword_patterns()
        self._load_predefined_patterns()

        # Show initialization summary
        self._show_initialization_summary()

    def _show_initialization_summary(self):
        """Show initialization summary with visual formatting."""
        if RICH_AVAILABLE:
            console = Console()
            table = Table(
                title="🚀 Configuración del Analizador Visual",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("Configuración", style="cyan", width=25)
            table.add_column("Valor", style="white")

            table.add_row("📝 Keywords", f"{len(self.keyword_patterns)}")
            table.add_row(
                "🎯 Patrones predefinidos", f"{len(self.predefined_patterns)}"
            )
            table.add_row("📁 Archivos máximos", f"{self.config.max_files:,}")
            table.add_row(
                "📄 Tamaño máximo archivo", f"{self.config.max_file_size_mb}MB"
            )
            table.add_row(
                "💾 Streaming habilitado",
                "✅ Sí" if self.config.enable_streaming else "❌ No",
            )
            table.add_row("⚡ Workers paralelos", f"{self.config.parallel_workers}")
            table.add_row(
                "🎨 Interfaz visual", "✅ Rich UI" if RICH_AVAILABLE else "📝 Básica"
            )

            console.print(table)
            console.print()
        else:
            print("🚀 Analizador Visual Inicializado:")
            print(f"   📝 Keywords: {len(self.keyword_patterns)}")
            print(f"   🎯 Patrones: {len(self.predefined_patterns)}")
            print(f"   📁 Max archivos: {self.config.max_files:,}")
            print(f"   📄 Max tamaño: {self.config.max_file_size_mb}MB")
            print(f"   ⚡ Workers: {self.config.parallel_workers}")
            print()

    def setup_logging(self):
        """Configure logging with visual enhancements."""
        if RICH_AVAILABLE:
            from rich.logging import RichHandler

            logging.basicConfig(
                level=logging.INFO,
                format="%(message)s",
                handlers=[RichHandler(console=Console(), show_path=False)],
            )
        else:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(message)s",
                handlers=[logging.StreamHandler(sys.stdout)],
            )
        self.logger = logging.getLogger(__name__)

    def _compile_keyword_patterns(self):
        """Compile keyword patterns (reuse from base class)."""
        for keyword in self.keywords:
            try:
                escaped_kw = re.escape(keyword)
                flags = re.MULTILINE
                if not self.config.case_sensitive_regex:
                    flags |= re.IGNORECASE

                pattern = re.compile(rf"\b{escaped_kw}\b", flags)
                self.keyword_patterns[keyword] = pattern
            except re.error as e:
                self.progress_tracker.log_warning(f"Keyword inválido '{keyword}': {e}")

    def _load_predefined_patterns(self):
        """Load predefined patterns (reuse from base class)."""
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
                    self.progress_tracker.log_warning(
                        f"Patrón predefinido '{name}' falló: {e}"
                    )
            else:
                self.progress_tracker.log_warning(
                    f"Patrón inseguro '{name}': {error_msg}"
                )

    def discover_files(self, directory: str) -> List[str]:
        """Discover files with visual feedback."""
        if RICH_AVAILABLE:
            console = Console()
            with console.status("[bold green]🔍 Buscando archivos...") as status:
                files = self._discover_files_internal(directory, status, console)
        else:
            print("🔍 Buscando archivos...")
            files = self._discover_files_internal(directory)

        return files

    def _discover_files_internal(self, directory: str, status=None, console=None):
        """Internal file discovery method."""
        files = []

        try:
            for file_path in Path(directory).rglob("*"):
                if len(files) >= self.config.max_files:
                    self.progress_tracker.log_warning(
                        f"Límite de archivos alcanzado ({self.config.max_files})"
                    )
                    break

                if (
                    file_path.is_file()
                    and file_path.suffix.lower() in ALLOWED_EXTENSIONS
                    and AdvancedSecurityValidator.is_safe_path(
                        str(file_path), self.base_directory
                    )
                ):
                    file_size = file_path.stat().st_size
                    max_size_bytes = self.config.max_file_size_mb * 1024 * 1024

                    if file_size <= max_size_bytes:
                        files.append(str(file_path))

                        # Update status if using Rich
                        if status and console and len(files) % 100 == 0:
                            status.update(
                                f"[bold green]🔍 Encontrados {len(files)} archivos..."
                            )
                    else:
                        self.processing_stats["files_skipped"] += 1

        except Exception as e:
            self.progress_tracker.log_error(f"Error buscando archivos: {e}")

        if RICH_AVAILABLE and console:
            console.print(
                f"✅ Encontrados [bold green]{len(files):,}[/bold green] archivos para analizar"
            )
        else:
            print(f"✅ Encontrados {len(files):,} archivos para analizar")

        return files

    def analyze_directory(self, directory: str = None) -> bool:
        """Analyze directory with enhanced visual feedback."""
        if directory is None:
            directory = self.base_directory

        # Discover files
        files = self.discover_files(directory)
        if not files:
            self.progress_tracker.log_error("No se encontraron archivos para analizar")
            return False

        # Process files in batches with visual feedback
        batch_size = self.config.batch_size
        total_batches = (len(files) + batch_size - 1) // batch_size

        # Start progress tracking
        self.progress_tracker.start_analysis(len(files), total_batches)

        try:
            successful_analyses = 0

            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, len(files))
                batch_files = files[start_idx:end_idx]

                # Update batch progress
                self.progress_tracker.update_progress(
                    batch_num=batch_num + 1,
                    current_file=f"Lote {batch_num + 1}/{total_batches}",
                )

                # Process batch
                batch_results = self._process_batch_visual(
                    batch_files, batch_num + 1, total_batches
                )
                successful_analyses += len(batch_results)
                self.results.extend(batch_results)

                # Update overall progress
                self.progress_tracker.update_progress(
                    files_completed=successful_analyses,
                    patterns_found=sum(
                        len(r.keyword_matches) + len(r.regex_matches)
                        for r in batch_results
                    ),
                )

                # Memory check
                if batch_num % 5 == 0:
                    memory_gb, is_safe = AdvancedSecurityValidator.check_memory_usage()
                    if not is_safe:
                        self.progress_tracker.log_warning(
                            f"Uso alto de memoria: {memory_gb:.1f}GB"
                        )
                        self.processing_stats["memory_warnings"] += 1
                        import gc

                        gc.collect()

            self.processing_stats["files_processed"] = successful_analyses
            self.progress_tracker.finish_analysis(success=True)

            return successful_analyses > 0

        except KeyboardInterrupt:
            self.progress_tracker.finish_analysis(success=False)
            self.progress_tracker.log_error("Análisis interrumpido por el usuario")
            return False
        except Exception as e:
            self.progress_tracker.finish_analysis(success=False)
            self.progress_tracker.log_error(f"Error durante el análisis: {e}")
            return False

    def _process_batch_visual(
        self, files: List[str], batch_num: int, total_batches: int
    ) -> List[AdvancedAnalysisResult]:
        """Process batch with visual feedback."""
        results = []

        if self.config.parallel_workers > 1:
            # Parallel processing with visual updates
            with ThreadPoolExecutor(
                max_workers=self.config.parallel_workers
            ) as executor:
                future_to_file = {}

                for file_path in files:
                    file_size = os.path.getsize(file_path)
                    future = executor.submit(
                        self._analyze_single_file_visual, file_path, file_size
                    )
                    future_to_file[future] = file_path

                completed_in_batch = 0
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    completed_in_batch += 1

                    # Update progress for current file
                    self.progress_tracker.update_progress(
                        current_file=os.path.basename(file_path)
                    )

                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                            self.processing_stats[
                                "total_size_processed"
                            ] += result.file_size_bytes
                    except Exception as e:
                        self.progress_tracker.log_error(
                            f"Error procesando {os.path.basename(file_path)}: {e}"
                        )
                        self.processing_stats["files_skipped"] += 1
        else:
            # Sequential processing
            for i, file_path in enumerate(files, 1):
                self.progress_tracker.update_progress(
                    current_file=os.path.basename(file_path)
                )

                try:
                    file_size = os.path.getsize(file_path)
                    result = self._analyze_single_file_visual(file_path, file_size)
                    if result:
                        results.append(result)
                        self.processing_stats[
                            "total_size_processed"
                        ] += result.file_size_bytes
                except Exception as e:
                    self.progress_tracker.log_error(
                        f"Error procesando {os.path.basename(file_path)}: {e}"
                    )
                    self.processing_stats["files_skipped"] += 1

        return results

    def _analyze_single_file_visual(
        self, file_path: str, file_size: int
    ) -> Optional[AdvancedAnalysisResult]:
        """Analyze single file with visual feedback."""
        start_time = time.time()

        # Initialize result
        result = AdvancedAnalysisResult(
            file_name=os.path.basename(file_path),
            file_size_bytes=file_size,
            processing_time=0.0,
            timestamp=datetime.now().isoformat(),
            total_messages=0,
            total_words=0,
            total_characters=0,
            unique_words=0,
        )

        try:
            # Determine if streaming is needed
            max_text_bytes = self.config.max_text_analysis_mb * 1024 * 1024
            use_streaming = self.config.enable_streaming and file_size > max_text_bytes

            if use_streaming:
                self._analyze_file_streaming_visual(file_path, result)
            else:
                self._analyze_file_standard_visual(file_path, result)

            result.processing_time = time.time() - start_time
            result.memory_usage_mb = psutil.Process().memory_info().rss / (1024 * 1024)

            return result

        except Exception as e:
            error_msg = f"Error analyzing file: {e}"
            result.errors.append(error_msg)
            return None

    def _analyze_file_streaming_visual(
        self, file_path: str, result: AdvancedAnalysisResult
    ):
        """Analyze file using streaming with visual feedback."""
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

                    text_to_analyze = previous_chunk + chunk
                    self._analyze_text_chunk_visual(
                        text_to_analyze, result, chunk_number
                    )

                    previous_chunk = (
                        chunk[-overlap_size:] if len(chunk) > overlap_size else chunk
                    )
                    chunk_number += 1

                result.chunks_processed = chunk_number

        except Exception as e:
            result.errors.append(f"Streaming analysis error: {e}")

    def _analyze_file_standard_visual(
        self, file_path: str, result: AdvancedAnalysisResult
    ):
        """Analyze file using standard approach with visual feedback."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Extract clean text
            if file_path.lower().endswith((".html", ".htm")):
                content = self._extract_text_from_html(content)

            self._analyze_text_chunk_visual(content, result, 0)
            result.chunks_processed = 1

        except Exception as e:
            result.errors.append(f"Standard analysis error: {e}")

    def _extract_text_from_html(self, html_content: str) -> str:
        """Extract clean text from HTML (reuse from base class)."""
        if not BS4_AVAILABLE:
            text = re.sub(r"<[^>]+>", " ", html_content)
            return re.sub(r"\s+", " ", text).strip()

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            for element in soup(["script", "style"]):
                element.decompose()
            return soup.get_text(separator=" ").strip()
        except Exception:
            text = re.sub(r"<[^>]+>", " ", html_content)
            return re.sub(r"\s+", " ", text).strip()

    def _analyze_text_chunk_visual(
        self, text: str, result: AdvancedAnalysisResult, chunk_number: int
    ):
        """Analyze text chunk with visual feedback (reuse logic from base class)."""
        if not text.strip():
            return

        # Basic text statistics
        words = text.split()
        result.total_words += len(words)
        result.total_characters += len(text)

        # Update unique words (approximate for streaming)
        if chunk_number == 0:
            unique_words = set(word.lower().strip('.,!?";()[]{}') for word in words)
            result.unique_words = len(unique_words)

            # Generate word frequency for first chunk
            if self.config.generate_statistics:
                word_freq = {}
                for word in words:
                    clean_word = word.lower().strip('.,!?";()[]{}')
                    if len(clean_word) > 2:
                        word_freq[clean_word] = word_freq.get(clean_word, 0) + 1

                result.word_frequency = dict(
                    sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:50]
                )

        # Estimate message count
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        message_indicators = [line for line in lines if ":" in line and len(line) > 10]
        result.total_messages += len(message_indicators)

        # Analyze patterns
        self._analyze_patterns_in_text_visual(text, result)

    def _analyze_patterns_in_text_visual(
        self, text: str, result: AdvancedAnalysisResult
    ):
        """Analyze patterns in text with visual feedback (reuse from base class)."""

        # Analyze keywords
        for keyword, pattern in self.keyword_patterns.items():
            try:
                matches = pattern.findall(text)
                if matches:
                    result.keyword_matches[keyword] = result.keyword_matches.get(
                        keyword, 0
                    ) + len(matches)

                    if self.config.save_match_examples:
                        if keyword not in result.pattern_examples:
                            result.pattern_examples[keyword] = []

                        for match in matches[: self.config.max_examples_per_pattern]:
                            if match not in result.pattern_examples[keyword]:
                                result.pattern_examples[keyword].append(match)
                                if (
                                    len(result.pattern_examples[keyword])
                                    >= self.config.max_examples_per_pattern
                                ):
                                    break
            except Exception as e:
                self.progress_tracker.log_warning(
                    f"Error analyzing keyword '{keyword}': {e}"
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

                    if self.config.save_match_examples:
                        for match in matches[:5]:
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
                self.progress_tracker.log_warning(
                    f"Error analyzing pattern '{pattern_name}': {e}"
                )

    # Reuse other methods from base class (save_results, generate_summary, etc.)
    def generate_comprehensive_summary(self) -> Dict:
        """Generate comprehensive summary (reuse from base class)."""
        if not self.results:
            return {"error": "No results to summarize"}

        # Basic statistics
        total_files = len(self.results)
        total_messages = sum(r.total_messages for r in self.results)
        total_words = sum(r.total_words for r in self.results)
        total_chars = sum(r.total_characters for r in self.results)
        total_size_mb = sum(r.file_size_bytes for r in self.results) / (1024 * 1024)
        avg_processing_time = sum(r.processing_time for r in self.results) / total_files

        # Aggregate patterns
        all_keywords = {}
        all_regex = {}

        for result in self.results:
            for keyword, count in result.keyword_matches.items():
                all_keywords[keyword] = all_keywords.get(keyword, 0) + count

            for pattern_name, pattern_data in result.regex_matches.items():
                if pattern_name not in all_regex:
                    all_regex[pattern_name] = {
                        "total_count": 0,
                        "files_with_matches": 0,
                    }

                all_regex[pattern_name]["total_count"] += pattern_data["count"]
                if pattern_data["count"] > 0:
                    all_regex[pattern_name]["files_with_matches"] += 1

        # Top patterns
        top_keywords = dict(
            sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)[:20]
        )
        top_regex = dict(
            sorted(all_regex.items(), key=lambda x: x[1]["total_count"], reverse=True)[
                :20
            ]
        )

        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "total_files_analyzed": total_files,
            "total_messages": total_messages,
            "total_words": total_words,
            "total_characters": total_chars,
            "total_size_mb": round(total_size_mb, 2),
            "average_processing_time": round(avg_processing_time, 2),
            "top_keywords": top_keywords,
            "top_regex_patterns": top_regex,
            "processing_statistics": self.processing_stats,
        }

    def save_results(self, output_dir: str = "visual_analysis_results") -> bool:
        """Save results with visual feedback."""
        try:
            output_path = Path(output_dir).resolve()
            output_path.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary = self.generate_comprehensive_summary()

            # Save JSON
            json_file = output_path / f"visual_analysis_{timestamp}.json"
            report_data = {
                "summary": summary,
                "detailed_results": [asdict(result) for result in self.results],
                "processing_statistics": self.processing_stats,
            }

            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            # Save text summary
            txt_file = output_path / f"visual_summary_{timestamp}.txt"
            with open(txt_file, "w", encoding="utf-8") as f:
                f.write("ANÁLISIS VISUAL DE WHATSAPP - RESUMEN COMPLETO\n")
                f.write("=" * 60 + "\n\n")

                for key, value in summary.items():
                    if isinstance(value, dict):
                        f.write(f"{key.replace('_', ' ').title()}:\n")
                        for k, v in list(value.items())[:10]:
                            f.write(f"  - {k}: {v}\n")
                    else:
                        f.write(f"{key.replace('_', ' ').title()}: {value}\n")
                f.write("\n")

            if RICH_AVAILABLE:
                console = Console()
                console.print("✅ [bold green]Resultados guardados:[/bold green]")
                console.print(f"   📄 JSON: {json_file}")
                console.print(f"   📝 Resumen: {txt_file}")
                console.print(f"   📁 Directorio: {output_path}")
            else:
                print("✅ Resultados guardados:")
                print(f"   📄 JSON: {json_file}")
                print(f"   📝 Resumen: {txt_file}")
                print(f"   📁 Directorio: {output_path}")

            return True

        except Exception as e:
            self.progress_tracker.log_error(f"Error guardando resultados: {e}")
            return False


def main():
    """Main function with enhanced visual interface."""
    parser = argparse.ArgumentParser(
        description="Analizador Visual de Contenido de WhatsApp",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🎨 Características Visuales:
  • Barras de progreso en tiempo real
  • Estimación de tiempo restante (ETA)
  • Estadísticas en vivo
  • Indicadores coloridos
  • Monitoreo de memoria
  • Velocidad de procesamiento

Ejemplos:
  python3 visual_content_analyzer.py /path/to/chats
  python3 visual_content_analyzer.py /path/to/chats --config spanish_config.json
  python3 visual_content_analyzer.py /path/to/chats --keywords "amor,familia,trabajo"
        """,
    )

    parser.add_argument("directory", nargs="?", help="Directorio con archivos de chat")
    parser.add_argument("--config", "-c", help="Archivo de configuración JSON")
    parser.add_argument("--keywords", "-k", help="Palabras clave separadas por comas")
    parser.add_argument(
        "--output", "-o", default="visual_analysis_results", help="Directorio de salida"
    )
    parser.add_argument("--max-files", type=int, help="Número máximo de archivos")
    parser.add_argument(
        "--parallel-workers", type=int, help="Número de workers paralelos"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Logging detallado"
    )

    args = parser.parse_args()

    if not args.directory:
        parser.error("Directorio es requerido")

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load configuration
    config = AdvancedAnalysisConfig()
    keywords = []

    if args.config:
        try:
            with open(args.config, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                keywords = config_data.get("keywords", [])

                # Update config
                if "advanced_config" in config_data:
                    for key, value in config_data["advanced_config"].items():
                        if hasattr(config, key):
                            setattr(config, key, value)
        except Exception as e:
            print(f"❌ Error cargando configuración: {e}")
            return

    if args.keywords:
        additional_keywords = [kw.strip() for kw in args.keywords.split(",")]
        keywords.extend(additional_keywords)

    if not keywords:
        keywords = ["amor", "familia", "trabajo", "importante", "urgente", "feliz"]

    # Override config with command line arguments
    if args.max_files:
        config.max_files = args.max_files
    if args.parallel_workers:
        config.parallel_workers = args.parallel_workers

    try:
        # Show welcome message
        if RICH_AVAILABLE:
            console = Console()
            console.print(
                Panel.fit(
                    "[bold magenta]🎨 Analizador Visual de WhatsApp[/bold magenta]\n"
                    "[cyan]Interfaz mejorada con progreso en tiempo real[/cyan]",
                    border_style="magenta",
                )
            )
        else:
            print("🎨 Analizador Visual de WhatsApp")
            print("=" * 40)

        # Create analyzer
        analyzer = VisualAdvancedContentAnalyzer(keywords, args.directory, config)

        # Run analysis
        start_time = time.time()
        success = analyzer.analyze_directory()
        analysis_time = time.time() - start_time

        if success and analyzer.results:
            # Save results
            analyzer.save_results(args.output)

            # Show final summary
            summary = analyzer.generate_comprehensive_summary()

            if RICH_AVAILABLE:
                console = Console()
                final_table = Table(
                    title="📊 Resumen Final",
                    show_header=True,
                    header_style="bold green",
                )
                final_table.add_column("Métrica", style="cyan")
                final_table.add_column("Valor", style="white")

                final_table.add_row(
                    "📁 Archivos analizados", f"{summary['total_files_analyzed']:,}"
                )
                final_table.add_row(
                    "📊 Total mensajes", f"{summary['total_messages']:,}"
                )
                final_table.add_row("📝 Total palabras", f"{summary['total_words']:,}")
                final_table.add_row(
                    "💾 Tamaño total", f"{summary['total_size_mb']:.1f} MB"
                )
                final_table.add_row("⏱️ Tiempo total", f"{analysis_time:.1f}s")

                console.print(final_table)

                if summary["top_keywords"]:
                    console.print("\n🔍 [bold]Top Keywords:[/bold]")
                    for keyword, count in list(summary["top_keywords"].items())[:5]:
                        console.print(f"  • {keyword}: [bold]{count:,}[/bold]")

            else:
                print("\n📊 Resumen Final:")
                print(f"   📁 Archivos: {summary['total_files_analyzed']:,}")
                print(f"   📊 Mensajes: {summary['total_messages']:,}")
                print(f"   📝 Palabras: {summary['total_words']:,}")
                print(f"   ⏱️ Tiempo: {analysis_time:.1f}s")
        else:
            print("❌ No se generaron resultados")

    except KeyboardInterrupt:
        print("\n⚠️ Análisis interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    main()
