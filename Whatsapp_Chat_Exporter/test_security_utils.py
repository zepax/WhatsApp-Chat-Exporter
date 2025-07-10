"""
Tests for security utilities.
"""

import os
from pathlib import Path

import pytest

from Whatsapp_Chat_Exporter.security_utils import (
    PathTraversalError,
    SecureFileOperations,
    SecurePathValidator,
)


class TestSecurePathValidator:
    """Tests for SecurePathValidator class."""

    def test_validate_path_normal(self, tmp_path):
        """Test validation of normal paths."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        result = SecurePathValidator.validate_path(test_file)
        assert result.exists()
        assert result.is_absolute()

    def test_validate_path_with_base_dir(self, tmp_path):
        """Test validation with base directory restriction."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        result = SecurePathValidator.validate_path(test_file, tmp_path)
        assert result.exists()
        assert result.is_absolute()

    def test_validate_path_traversal_attempt(self, tmp_path):
        """Test detection of path traversal attempts."""
        malicious_path = tmp_path / ".." / "etc" / "passwd"

        with pytest.raises(PathTraversalError):
            SecurePathValidator.validate_path(malicious_path, tmp_path)

    def test_validate_path_empty(self):
        """Test validation with empty path."""
        with pytest.raises(ValueError):
            SecurePathValidator.validate_path("")

    def test_safe_join_normal(self, tmp_path):
        """Test safe joining of path components."""
        result = SecurePathValidator.safe_join(tmp_path, "sub", "file.txt")
        expected = tmp_path / "sub" / "file.txt"
        assert result == expected.resolve()

    def test_safe_join_traversal_attempt(self, tmp_path):
        """Test safe join with path traversal attempt."""
        with pytest.raises(PathTraversalError):
            SecurePathValidator.safe_join(tmp_path, "..", "etc", "passwd")


class TestSecureFileOperations:
    """Tests for SecureFileOperations class."""

    def test_secure_copy_success(self, tmp_path):
        """Test successful secure copy operation."""
        src_file = tmp_path / "source.txt"
        dst_file = tmp_path / "destination.txt"

        src_file.write_text("test content")

        SecureFileOperations.secure_copy(src_file, dst_file, tmp_path)

        assert dst_file.exists()
        assert dst_file.read_text() == "test content"

    def test_secure_copy_nonexistent_source(self, tmp_path):
        """Test secure copy with non-existent source."""
        src_file = tmp_path / "nonexistent.txt"
        dst_file = tmp_path / "destination.txt"

        with pytest.raises(FileNotFoundError):
            SecureFileOperations.secure_copy(src_file, dst_file, tmp_path)

    def test_secure_copy_path_traversal(self, tmp_path):
        """Test secure copy with path traversal attempt."""
        src_file = tmp_path / "source.txt"
        src_file.write_text("test")

        malicious_dst = tmp_path / ".." / "malicious.txt"

        with pytest.raises(PathTraversalError):
            SecureFileOperations.secure_copy(src_file, malicious_dst, tmp_path)

    def test_secure_temp_file(self):
        """Test secure temporary file creation."""
        temp_file = SecureFileOperations.secure_temp_file(suffix=".txt", prefix="test_")

        try:
            assert temp_file.name.endswith(".txt")
            assert "test_" in temp_file.name

            # Check file permissions (owner read/write only)
            file_stat = os.stat(temp_file.name)
            assert file_stat.st_mode & 0o777 == 0o600
        finally:
            temp_file.close()
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    def test_secure_temp_dir(self):
        """Test secure temporary directory creation."""
        temp_dir = SecureFileOperations.secure_temp_dir(suffix="_test", prefix="test_")

        try:
            assert temp_dir.name.endswith("_test")
            assert "test_" in temp_dir.name

            # Check directory permissions (owner read/write/execute only)
            dir_stat = os.stat(temp_dir.name)
            assert dir_stat.st_mode & 0o777 == 0o700
        finally:
            temp_dir.cleanup()

    def test_secure_temp_file_with_custom_dir(self, tmp_path):
        """Test secure temporary file with custom directory."""
        temp_file = SecureFileOperations.secure_temp_file(dir=tmp_path)

        try:
            assert Path(temp_file.name).parent == tmp_path
        finally:
            temp_file.close()
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
