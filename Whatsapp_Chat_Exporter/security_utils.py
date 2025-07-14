"""
Security utilities for file path validation and secure operations.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)


class PathTraversalError(Exception):
    """Exception raised for path traversal attempts.

    This exception is raised when a file path is detected to be attempting
    to access files outside of the allowed directory structure, which could
    indicate a security vulnerability or attack.

    Common scenarios that trigger this exception:
    - Paths containing ".." (parent directory) components
    - Paths that resolve outside the specified base directory
    - Symlink attacks that point to unauthorized locations
    """

    def __init__(
        self, message: str = "Path traversal attempt detected", path: str = None
    ):
        super().__init__(message)
        self.path = path


class SecurePathValidator:
    """Validates and sanitizes file paths to prevent path traversal attacks."""

    @staticmethod
    def validate_path(
        path: Union[str, Path], base_dir: Optional[Union[str, Path]] = None
    ) -> Path:
        """
        Validate and normalize a file path to prevent path traversal attacks.

        Args:
            path: The path to validate
            base_dir: Optional base directory to restrict access to

        Returns:
            Validated and normalized Path object

        Raises:
            PathTraversalError: If path traversal is detected
            ValueError: If path is invalid
        """
        if not path:
            raise ValueError("Path cannot be empty")

        # Convert to Path object for consistent handling
        path_obj = Path(path)

        # Resolve to absolute path to handle relative paths and symlinks
        try:
            resolved_path = path_obj.resolve()
        except (OSError, RuntimeError) as e:
            raise ValueError(f"Invalid path: {e}")

        # Check for path traversal attempts
        if base_dir:
            base_path = Path(base_dir).resolve()
            try:
                # Check if resolved path is within base directory
                resolved_path.relative_to(base_path)
            except ValueError:
                raise PathTraversalError(
                    f"Path traversal detected: {path} resolves outside of {base_dir}"
                )

        # Additional security checks
        path_str = str(resolved_path)

        # Check for dangerous path components
        dangerous_components = [
            "..",  # Parent directory
            "~",  # Home directory
            "$",  # Environment variables
        ]

        for component in dangerous_components:
            if component in path_str:
                logger.warning(
                    f"Potentially dangerous path component detected: {component} in {path}"
                )

        return resolved_path

    @staticmethod
    def safe_join(base_path: Union[str, Path], *parts: str) -> Path:
        """
        Safely join path components, preventing path traversal.

        Args:
            base_path: Base directory path
            *parts: Path components to join

        Returns:
            Safely joined path

        Raises:
            PathTraversalError: If path traversal is detected
        """
        base = Path(base_path).resolve()

        # Join all parts
        joined_path = base
        for part in parts:
            if not part:
                continue
            joined_path = joined_path / part

        # Validate the final path
        return SecurePathValidator.validate_path(joined_path, base)


class SecureFileOperations:
    """Secure file operations with proper validation and error handling."""

    @staticmethod
    def secure_copy(
        src: Union[str, Path],
        dst: Union[str, Path],
        base_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        """
        Securely copy a file with path validation.

        Args:
            src: Source file path
            dst: Destination file path
            base_dir: Optional base directory for validation

        Raises:
            PathTraversalError: If path traversal is detected
            FileNotFoundError: If source file doesn't exist
            PermissionError: If insufficient permissions
        """
        import shutil

        # Validate paths
        src_path = SecurePathValidator.validate_path(src, base_dir)
        dst_path = SecurePathValidator.validate_path(dst, base_dir)

        # Check source exists
        if not src_path.exists():
            raise FileNotFoundError(f"Source file not found: {src_path}")

        # Ensure destination directory exists
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        # Perform secure copy
        try:
            shutil.copy2(src_path, dst_path)
            logger.info(f"Successfully copied {src_path} to {dst_path}")
        except Exception as e:
            logger.error(f"Failed to copy {src_path} to {dst_path}: {e}")
            raise

    @staticmethod
    def secure_temp_file(
        suffix: str = "", prefix: str = "tmp", dir: Optional[Union[str, Path]] = None
    ) -> tempfile.NamedTemporaryFile:
        """
        Create a secure temporary file with proper permissions.

        Args:
            suffix: File suffix
            prefix: File prefix
            dir: Directory for temporary file

        Returns:
            Secure temporary file object
        """
        # Validate directory if provided
        if dir:
            dir_path = SecurePathValidator.validate_path(dir)
            dir = str(dir_path)

        # Create temporary file with secure permissions
        temp_file = tempfile.NamedTemporaryFile(
            mode="w+b", suffix=suffix, prefix=prefix, dir=dir, delete=False
        )

        # Set restrictive permissions (owner read/write only)
        os.chmod(temp_file.name, 0o600)

        logger.debug(f"Created secure temporary file: {temp_file.name}")
        return temp_file

    @staticmethod
    def secure_temp_dir(
        suffix: str = "", prefix: str = "tmp", dir: Optional[Union[str, Path]] = None
    ) -> tempfile.TemporaryDirectory:
        """
        Create a secure temporary directory with proper permissions.

        Args:
            suffix: Directory suffix
            prefix: Directory prefix
            dir: Parent directory for temporary directory

        Returns:
            Secure temporary directory object
        """
        # Validate directory if provided
        if dir:
            dir_path = SecurePathValidator.validate_path(dir)
            dir = str(dir_path)

        # Create temporary directory with secure permissions
        temp_dir = tempfile.TemporaryDirectory(suffix=suffix, prefix=prefix, dir=dir)

        # Set restrictive permissions (owner read/write/execute only)
        os.chmod(temp_dir.name, 0o700)

        logger.debug(f"Created secure temporary directory: {temp_dir.name}")
        return temp_dir
