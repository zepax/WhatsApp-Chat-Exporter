import os
import shutil

from Whatsapp_Chat_Exporter.__main__ import copy_exported_media
from Whatsapp_Chat_Exporter.data_model import ChatCollection, ChatStore, Message
from Whatsapp_Chat_Exporter.utility import Device
from Whatsapp_Chat_Exporter import exported_handler


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


def test_copy_exported_media_traversal(tmp_path, monkeypatch):
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

    captured = {}

    def fake_copy_parallel(pairs, workers=4):
        captured["pairs"] = pairs
        captured["workers"] = workers
        for s, d in pairs:
            shutil.copy2(s, d)

    monkeypatch.setattr(
        "Whatsapp_Chat_Exporter.__main__.copy_parallel",
        fake_copy_parallel,
    )

    copy_exported_media(str(chat_file), collection, str(out_dir), workers=2)

    copied = out_dir / "media" / "good.txt"
    assert copied.is_file()
    assert chat.get_message("1").data == os.path.relpath(copied, out_dir)
    assert captured["pairs"] == [(str(good), str(copied))]
    assert captured["workers"] == 2

    assert not (out_dir / "media" / "outside.txt").exists()
    assert not (out_dir / "media" / "abs.txt").exists()
    assert chat.get_message("2").data == str(outside)
    assert chat.get_message("3").data == str(abs_file)


def test_find_media_file_cache(tmp_path, monkeypatch):
    base = tmp_path / "chat"
    media = base / "Media"
    media.mkdir(parents=True)
    file_path = media / "pic.jpg"
    file_path.write_text("data")

    exported_handler._build_media_cache(str(base))

    def fail_walk(_):
        raise AssertionError("os.walk should not be called")

    monkeypatch.setattr(exported_handler.os, "walk", fail_walk)

    found = exported_handler._find_media_file(str(base), "pic.jpg")
    missing = exported_handler._find_media_file(str(base), "nope.jpg")

    assert found == str(file_path)
    assert missing is None
