"""
Comprehensive logging configuration for WhatsApp Chat Exporter.
"""

import functools
import json
import logging
import logging.handlers
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class SecurityFilter(logging.Filter):
    """Filter to prevent logging of sensitive information."""

    SENSITIVE_PATTERNS = [
        "password",
        "key",
        "token",
        "secret",
        "credential",
        "auth",
        "login",
        "session",
        "cookie",
        "private",
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out log records containing sensitive information."""
        message = record.getMessage().lower()

        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in message:
                # Replace with sanitized message
                record.msg = "[SENSITIVE DATA FILTERED]"
                record.args = ()
                break

        return True


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for better log analysis."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields (avoid overwriting existing keys)
        for key, value in record.__dict__.items():
            if (
                key
                not in [
                    "name",
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "pathname",
                    "filename",
                    "module",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                    "lineno",
                    "funcName",
                    "created",
                    "msecs",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "processName",
                    "process",
                    "getMessage",
                ]
                and key not in log_entry
            ):
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


class WhatsAppLoggerConfig:
    """Centralized logging configuration for WhatsApp Chat Exporter."""

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        log_level: str = "INFO",
        verbose: bool = False,
    ):
        """
        Initialize logging configuration.

        Args:
            log_dir: Directory for log files (default: ./logs)
            log_level: Default logging level
            verbose: Enable verbose console output
        """
        self.log_dir = log_dir or Path("logs")
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.verbose = verbose
        self.loggers: Dict[str, logging.Logger] = {}

        # Ensure log directory exists
        self.log_dir.mkdir(exist_ok=True)

        # Configure root logger
        self._setup_root_logger()

    def _setup_root_logger(self) -> None:
        """Set up the root logger with appropriate handlers."""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)

        # Clear existing handlers
        root_logger.handlers.clear()

        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        # Set console level based on verbose flag
        console_level = logging.DEBUG if self.verbose else logging.INFO
        console_handler.setLevel(console_level)
        console_formatter = logging.Formatter(
            "%(levelname)s: %(message)s"
            if not self.verbose
            else "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(SecurityFilter())
        root_logger.addHandler(console_handler)

        # File handler for general logs
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "whatsapp_exporter.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = StructuredFormatter()
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(SecurityFilter())
        root_logger.addHandler(file_handler)

        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "errors.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,  # 5MB
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        error_handler.addFilter(SecurityFilter())
        root_logger.addHandler(error_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a configured logger for a specific module.

        Args:
            name: Logger name (usually __name__)

        Returns:
            Configured logger instance
        """
        if name not in self.loggers:
            logger = logging.getLogger(name)
            logger.setLevel(self.log_level)
            self.loggers[name] = logger

        return self.loggers[name]

    def setup_security_logger(self) -> logging.Logger:
        """Set up dedicated security event logger."""
        security_logger = logging.getLogger("security")
        security_logger.setLevel(logging.WARNING)

        # Security events handler
        security_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "security.log", maxBytes=5 * 1024 * 1024, backupCount=10
        )
        security_handler.setLevel(logging.WARNING)
        security_handler.setFormatter(StructuredFormatter())

        # Don't filter security logs - we need all details
        security_logger.addHandler(security_handler)
        security_logger.propagate = False  # Don't send to root logger

        return security_logger

    def setup_performance_logger(self) -> logging.Logger:
        """Set up dedicated performance monitoring logger."""
        perf_logger = logging.getLogger("performance")
        perf_logger.setLevel(logging.INFO)

        # Performance handler
        perf_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "performance.log", maxBytes=10 * 1024 * 1024, backupCount=5
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(StructuredFormatter())
        perf_handler.addFilter(SecurityFilter())

        perf_logger.addHandler(perf_handler)
        perf_logger.propagate = False

        return perf_logger

    def log_startup_info(self) -> None:
        """Log application startup information."""
        logger = self.get_logger("startup")

        startup_info = {
            "event": "application_start",
            "python_version": sys.version,
            "platform": sys.platform,
            "log_level": logging.getLevelName(self.log_level),
            "log_directory": str(self.log_dir),
            "pid": os.getpid(),
        }

        logger.info("Application startup", extra=startup_info)


# Global logger configuration instance
_logger_config: Optional[WhatsAppLoggerConfig] = None


def setup_logging(
    log_dir: Optional[Path] = None, log_level: str = "INFO", verbose: bool = False
) -> WhatsAppLoggerConfig:
    """
    Set up global logging configuration.

    Args:
        log_dir: Directory for log files
        log_level: Default logging level
        verbose: Enable verbose console output

    Returns:
        Logger configuration instance
    """
    global _logger_config
    _logger_config = WhatsAppLoggerConfig(log_dir, log_level, verbose)
    _logger_config.log_startup_info()
    return _logger_config


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    if _logger_config is None:
        setup_logging()

    return _logger_config.get_logger(name)


def get_security_logger() -> logging.Logger:
    """Get the security events logger."""
    if _logger_config is None:
        setup_logging()

    return _logger_config.setup_security_logger()


def get_performance_logger() -> logging.Logger:
    """Get the performance monitoring logger."""
    if _logger_config is None:
        setup_logging()

    return _logger_config.setup_performance_logger()


# Performance monitoring decorators and context managers


def log_performance(func):
    """Decorator to log function performance metrics."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        perf_logger = get_performance_logger()
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            perf_logger.info(
                f"Function {func.__name__} completed successfully",
                extra={
                    "function": func.__name__,
                    "source_module": func.__module__,
                    "duration_seconds": duration,
                    "status": "success",
                },
            )
            return result

        except Exception as e:
            duration = time.time() - start_time
            perf_logger.error(
                f"Function {func.__name__} failed",
                extra={
                    "function": func.__name__,
                    "source_module": func.__module__,
                    "duration_seconds": duration,
                    "status": "error",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
            )
            raise

    return wrapper


@contextmanager
def log_operation(operation_name: str, **context):
    """Context manager to log operation performance and status."""
    perf_logger = get_performance_logger()
    start_time = time.time()

    perf_logger.info(
        f"Starting operation: {operation_name}",
        extra={"operation": operation_name, "status": "started", **context},
    )

    try:
        yield
        duration = time.time() - start_time
        perf_logger.info(
            f"Operation completed: {operation_name}",
            extra={
                "operation": operation_name,
                "status": "completed",
                "duration_seconds": duration,
                **context,
            },
        )

    except Exception as e:
        duration = time.time() - start_time
        perf_logger.error(
            f"Operation failed: {operation_name}",
            extra={
                "operation": operation_name,
                "status": "failed",
                "duration_seconds": duration,
                "error_type": type(e).__name__,
                "error_message": str(e),
                **context,
            },
        )
        raise
