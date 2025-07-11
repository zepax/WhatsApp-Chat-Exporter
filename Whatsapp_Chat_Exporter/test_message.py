import datetime
from mimetypes import MimeTypes

import Whatsapp_Chat_Exporter.android_handler as android_handler
from Whatsapp_Chat_Exporter.data_model import ChatCollection, ChatStore, Message
from Whatsapp_Chat_Exporter.utility import Device


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


def test_get_last_message():
    chat = ChatStore(Device.ANDROID)
    msg1 = Message(
        from_me=1,
        timestamp=1,
        time=1,
        key_id=1,
        received_timestamp=1,
        read_timestamp=1,
    )
    msg2 = Message(
        from_me=0,
        timestamp=2,
        time=2,
        key_id=2,
        received_timestamp=2,
        read_timestamp=2,
    )
    chat.add_message("1", msg1)
    chat.add_message("2", msg2)

    assert chat.get_last_message() is msg2
