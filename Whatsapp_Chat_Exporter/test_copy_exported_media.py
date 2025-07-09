import os

from Whatsapp_Chat_Exporter.__main__ import copy_exported_media
from Whatsapp_Chat_Exporter.data_model import ChatCollection, ChatStore, Message
from Whatsapp_Chat_Exporter.utility import Device


def _create_msg(path: str) -> Message:
    msg = Message(
        from_me=1,
        timestamp=1,
        time=1,
        key_id=1,
        received_timestamp=1,
        read_timestamp=1,
    )
    msg.media = True
    msg.data = path
    return msg


def test_copy_exported_media_traversal(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    good = src / "good.txt"
    good.write_text("ok")

    outside = tmp_path / "outside.txt"
    outside.write_text("bad")

    abs_file = tmp_path / "abs.txt"
    abs_file.write_text("abs")

    chat = ChatStore(Device.ANDROID)
    chat.add_message("1", _create_msg(str(good)))
    chat.add_message("2", _create_msg(str(outside)))
    chat.add_message("3", _create_msg(str(abs_file)))

    collection = ChatCollection()
    collection.add_chat("ExportedChat", chat)

    chat_file = src / "chat.txt"
    chat_file.write_text("dummy")

    out_dir = tmp_path / "out"
    out_dir.mkdir()

    copy_exported_media(str(chat_file), collection, str(out_dir))

    copied = out_dir / "media" / "good.txt"
    assert copied.is_file()
    assert chat.get_message("1").data == os.path.relpath(copied, out_dir)

    assert not (out_dir / "media" / "outside.txt").exists()
    assert not (out_dir / "media" / "abs.txt").exists()
    assert chat.get_message("2").data == str(outside)
    assert chat.get_message("3").data == str(abs_file)
