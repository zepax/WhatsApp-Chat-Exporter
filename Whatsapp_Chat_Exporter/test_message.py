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
from pathlib import Path
from mimetypes import MimeTypes
import builtins
import os

from Whatsapp_Chat_Exporter.data_model import ChatCollection, ChatStore
from Whatsapp_Chat_Exporter.utility import Device
import Whatsapp_Chat_Exporter.android_handler as android_handler


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

