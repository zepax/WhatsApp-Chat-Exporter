import datetime
from Whatsapp_Chat_Exporter.data_model import Message


def test_message_date_attribute():
    ts = 1_660_000_000
    msg = Message(
        from_me=1,
        timestamp=ts,
        time=ts,
        key_id=1,
        received_timestamp=ts + 1,
        read_timestamp=ts + 2,
        timezone_offset=0,
    )
    expected = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    assert msg.date == expected


from types import SimpleNamespace
import sqlite3
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from mimetypes import MimeTypes
import builtins
import os

from Whatsapp_Chat_Exporter.data_model import ChatCollection, ChatStore
from Whatsapp_Chat_Exporter.utility import Device
import Whatsapp_Chat_Exporter.android_handler as android_handler
import Whatsapp_Chat_Exporter.ios_handler as ios_handler


def test_slug_cached(monkeypatch, tmp_path):
    data = ChatCollection()
    chat = ChatStore(Device.ANDROID)
    ts = 1_660_000_000
    msg = Message(
        from_me=1,
        timestamp=ts,
        time=ts,
        key_id=1,
        received_timestamp=ts + 1,
        read_timestamp=ts + 2,
        timezone_offset=0,
    )
    chat.add_message("1", msg)
    data.add_chat("123@c.us", chat)

    media_dir = tmp_path
    (media_dir / "thumbnails").mkdir()
    file_path = media_dir / "img.jpg"
    file_path.write_bytes(b"a")

    content = {
        "file_path": "img.jpg",
        "message_row_id": "1",
        "key_remote_jid": "123@c.us",
        "mime_type": None,
        "file_hash": b"hash",
        "thumbnail": None,
    }

    calls = []

    def fake_slugify(value, allow_unicode):
        calls.append(value)
        return "slugged"

    monkeypatch.setattr(android_handler, "slugify", fake_slugify)

    mime = MimeTypes()
    android_handler._process_single_media(data, content, str(media_dir), mime, True)
    android_handler._process_single_media(data, content, str(media_dir), mime, True)

    assert chat.slug == "slugged"
    assert len(calls) == 1


def test_android_media_traversal_rejected(tmp_path):
    data = ChatCollection()
    chat = ChatStore(Device.ANDROID)
    ts = 1_660_000_000
    msg = Message(
        from_me=1,
        timestamp=ts,
        time=ts,
        key_id=1,
        received_timestamp=ts + 1,
        read_timestamp=ts + 2,
        timezone_offset=0,
    )
    chat.add_message("1", msg)
    data.add_chat("123@c.us", chat)

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "thumbnails").mkdir()
    outside = tmp_path / "outside.jpg"
    outside.write_bytes(b"a")

    content = {
        "file_path": "../outside.jpg",
        "message_row_id": "1",
        "key_remote_jid": "123@c.us",
        "mime_type": None,
        "file_hash": b"hash",
        "thumbnail": None,
    }

    mime = MimeTypes()
    android_handler._process_single_media(data, content, str(media_dir), mime, False)

    msg = chat.get_message("1")
    assert msg.data == "The media is missing"
    assert msg.meta


def test_ios_media_traversal_rejected(tmp_path):
    data = ChatCollection()
    chat = ChatStore(Device.IOS)
    ts = 1_660_000_000
    msg = Message(
        from_me=1,
        timestamp=ts,
        time=ts,
        key_id=1,
        received_timestamp=ts + 1,
        read_timestamp=ts + 2,
        timezone_offset=0,
    )
    chat.add_message("1", msg)
    data.add_chat("123@c.us", chat)

    media_dir = tmp_path / "Media"
    msg_dir = media_dir / "Message"
    msg_dir.mkdir(parents=True)
    outside = tmp_path / "outside.mov"
    outside.write_bytes(b"a")


def test_fetch_row_safely_success():
    """Test that _fetch_row_safely returns data on successful fetch."""
    mock_cursor = Mock()
    mock_cursor.fetchone.return_value = {"id": 1, "data": "test"}
    
    result = android_handler._fetch_row_safely(mock_cursor)
    
    assert result == {"id": 1, "data": "test"}
    mock_cursor.fetchone.assert_called_once()


def test_fetch_row_safely_retry_then_success():
    """Test that _fetch_row_safely retries on OperationalError and eventually succeeds."""
    mock_cursor = Mock()
    mock_cursor.fetchone.side_effect = [
        sqlite3.OperationalError("Database locked"),
        {"id": 1, "data": "test"}
    ]
    
    with patch('time.sleep'):  # Mock sleep to speed up test
        result = android_handler._fetch_row_safely(mock_cursor)
    
    assert result == {"id": 1, "data": "test"}
    assert mock_cursor.fetchone.call_count == 2


def test_fetch_row_safely_max_retries_exceeded():
    """Test that _fetch_row_safely raises exception after max retries."""
    mock_cursor = Mock()
    mock_cursor.fetchone.side_effect = sqlite3.OperationalError("Database corrupted")
    
    with patch('time.sleep'):  # Mock sleep to speed up test
        with pytest.raises(sqlite3.OperationalError) as exc_info:
            android_handler._fetch_row_safely(mock_cursor, max_retries=2)
    
    assert "Failed to fetch row after 2 attempts" in str(exc_info.value)
    assert mock_cursor.fetchone.call_count == 2


def test_fetch_row_safely_returns_none():
    """Test that _fetch_row_safely returns None when no more rows."""
    mock_cursor = Mock()
    mock_cursor.fetchone.return_value = None
    
    result = android_handler._fetch_row_safely(mock_cursor)
    
    assert result is None
    mock_cursor.fetchone.assert_called_once()

