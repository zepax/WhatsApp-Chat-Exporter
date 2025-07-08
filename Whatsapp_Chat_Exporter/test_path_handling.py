import os
from mimetypes import MimeTypes

from Whatsapp_Chat_Exporter import ios_handler
from Whatsapp_Chat_Exporter.data_model import ChatCollection, ChatStore, Message
from Whatsapp_Chat_Exporter.utility import Device


def _make_msg() -> Message:
    return Message(
        from_me=1,
        timestamp=1,
        time=1,
        key_id=1,
        received_timestamp=1,
        read_timestamp=1,
    )


def test_ios_media_relative_path(tmp_path):
    media_dir = tmp_path / "media"
    message_dir = media_dir / "Message"
    file_rel = os.path.join("sub", "img.jpg")
    file_path = message_dir / file_rel
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("x")

    data = ChatCollection()
    chat = ChatStore(Device.IOS)
    chat.add_message("1", _make_msg())
    data.add_chat("123@c.us", chat)

    content = {
        "ZMEDIALOCALPATH": file_rel,
        "ZCONTACTJID": "123@c.us",
        "ZMESSAGE": "1",
        "ZVCARDSTRING": None,
        "ZTITLE": None,
    }

    mime = MimeTypes()
    ios_handler.process_media_item(content, data, str(media_dir), mime, False)

    expected = os.path.relpath(str(file_path), file_path.anchor)
    assert chat.get_message("1").data == expected
import os
from mimetypes import MimeTypes

from Whatsapp_Chat_Exporter import ios_handler
from Whatsapp_Chat_Exporter.data_model import ChatCollection, ChatStore, Message
from Whatsapp_Chat_Exporter.utility import Device


def _make_msg() -> Message:
    return Message(
        from_me=1,
        timestamp=1,
        time=1,
        key_id=1,
        received_timestamp=1,
