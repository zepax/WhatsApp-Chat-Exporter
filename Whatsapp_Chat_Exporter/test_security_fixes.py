"""
Tests for security fixes to ensure SQL injection and path traversal vulnerabilities are properly addressed.
"""

import tempfile
from pathlib import Path

import pytest

from Whatsapp_Chat_Exporter import ios_media_handler
from Whatsapp_Chat_Exporter.security_utils import (
    PathTraversalError,
    SecurePathValidator,
)
from Whatsapp_Chat_Exporter.utility import WhatsAppIdentifier, get_chat_condition


class TestSQLInjectionFixes:
    """Test SQL injection prevention in chat filters."""

    def test_get_chat_condition_rejects_sql_injection(self):
        """Test that get_chat_condition rejects SQL injection attempts."""
        # Test basic SQL injection attempt
        with pytest.raises(ValueError, match="Chat filter must contain digits only"):
            get_chat_condition(
                ["1' OR '1'='1"], True, ["jid", "name"], "jid", "android"
            )

    def test_get_chat_condition_rejects_non_numeric(self):
        """Test that get_chat_condition rejects non-numeric input."""
        with pytest.raises(ValueError, match="Chat filter must contain digits only"):
            get_chat_condition(["abc123"], True, ["jid", "name"], "jid", "android")

    def test_get_chat_condition_accepts_valid_numeric(self):
        """Test that get_chat_condition accepts valid numeric input."""
        # This should not raise an exception
        result = get_chat_condition(
            ["1234567890"], True, ["jid", "name"], "jid", "android"
        )
        assert "1234567890" in result
        assert "LIKE" in result

    def test_get_chat_condition_handles_empty_filter(self):
        """Test that get_chat_condition handles empty/None filters correctly."""
        result = get_chat_condition(None, True, ["jid", "name"], "jid", "android")
        assert result == ""

    def test_get_chat_condition_rejects_special_characters(self):
        """Test that get_chat_condition rejects special SQL characters."""
        dangerous_inputs = [
            "123';DROP TABLE users;--",
            "123/*comment*/",
            "123--comment",
            "123'",
            '123"',
        ]

        for dangerous_input in dangerous_inputs:
            with pytest.raises(
                ValueError, match="Chat filter must contain digits only"
            ):
                get_chat_condition(
                    [dangerous_input], True, ["jid", "name"], "jid", "android"
                )


class TestPathTraversalFixes:
    """Test path traversal prevention."""

    def test_secure_path_validator_rejects_traversal(self):
        """Test that SecurePathValidator rejects path traversal attempts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)

            # Test various path traversal attempts
            dangerous_paths = [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32",
                "./test/../../../etc/passwd",
                "test/../../etc/passwd",
            ]

            for dangerous_path in dangerous_paths:
                with pytest.raises((PathTraversalError, ValueError)):
                    SecurePathValidator.validate_path(dangerous_path, base_path)

    def test_secure_path_validator_allows_safe_paths(self):
        """Test that SecurePathValidator allows safe paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)

            # Create a test file
            test_file = base_path / "test.txt"
            test_file.write_text("test content")

            # This should not raise an exception
            validated_path = SecurePathValidator.validate_path(
                str(test_file), base_path
            )
            assert validated_path.exists()
            assert validated_path.is_relative_to(base_path)

    def test_secure_path_validator_handles_absolute_paths(self):
        """Test that SecurePathValidator properly handles absolute paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")

            # Absolute path should work without base_dir
            validated_path = SecurePathValidator.validate_path(str(test_file))
            assert validated_path.exists()

    def test_secure_path_validator_rejects_empty_path(self):
        """Test that SecurePathValidator rejects empty paths."""
        with pytest.raises(ValueError, match="Path cannot be empty"):
            SecurePathValidator.validate_path("")

        with pytest.raises(ValueError, match="Path cannot be empty"):
            SecurePathValidator.validate_path(None)


class TestInputValidation:
    """Test enhanced input validation."""

    def test_chat_filter_validation_patterns(self):
        """Test that chat filter validation catches dangerous patterns."""
        # This test simulates the validation that would happen in validate_chat_filters
        dangerous_patterns = [
            "'",
            '"',
            "--",
            "/*",
            "*/",
            ";",
            "DROP",
            "DELETE",
            "UPDATE",
            "INSERT",
        ]

        test_inputs = [
            "123'456",
            '123"456',
            "123--comment",
            "123/*comment*/",
            "123;DROP TABLE",
            "123 DROP users",
            "123 DELETE FROM",
            "123 UPDATE SET",
            "123 INSERT INTO",
        ]

        for test_input in test_inputs:
            test_input_upper = test_input.upper()
            contains_dangerous = any(
                pattern in test_input_upper for pattern in dangerous_patterns
            )
            assert (
                contains_dangerous
            ), f"Should detect dangerous pattern in: {test_input}"

    def test_numeric_only_validation(self):
        """Test that numeric-only validation works correctly."""
        valid_inputs = ["123456789", "0", "987654321"]
        invalid_inputs = ["abc", "123abc", "12.34", "12-34", "+123"]

        for valid_input in valid_inputs:
            assert valid_input.isnumeric(), f"Should be valid: {valid_input}"

        for invalid_input in invalid_inputs:
            assert not invalid_input.isnumeric(), f"Should be invalid: {invalid_input}"


# Tests from the iOS backup validation branch
def test_get_chat_condition_rejects_invalid():
    with pytest.raises(ValueError):
        get_chat_condition(["1' OR '1'='1"], True, ["jid", "name"], "jid", "android")


def test_copy_whatsapp_db_missing(tmp_path):
    extractor = ios_media_handler.BackupExtractor(
        str(tmp_path), WhatsAppIdentifier, 1024
    )
    with pytest.raises(ios_media_handler.IOSMediaError) as exc:
        extractor._copy_whatsapp_databases()
    assert exc.value.code == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
