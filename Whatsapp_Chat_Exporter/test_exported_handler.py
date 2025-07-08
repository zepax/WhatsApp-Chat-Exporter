<<<<<<< HEAD
import builtins
from pathlib import Path
from Whatsapp_Chat_Exporter import exported_handler
from Whatsapp_Chat_Exporter.data_model import ChatCollection


def test_messages_no_prompt(tmp_path, monkeypatch):
    chat_file = tmp_path / "chat.txt"
    chat_file.write_text(
        "01/01/2024, 10:00 - Alice: Hello\n01/01/2024, 10:01 - Bob: Hi"
    )
    data = ChatCollection()
    called = False

    def fake_input(prompt):
        nonlocal called
        called = True
        return "n"

    monkeypatch.setattr(builtins, "input", fake_input)
    exported_handler.messages(
        str(chat_file),
        data,
        assume_first_as_me=False,
        prompt_user=False,
    )
    assert not called
    assert "ExportedChat" in data
    chat = data["ExportedChat"]
    assert len(chat) == 2


def test_copy_exported_media(tmp_path):
    chat_dir = tmp_path / "chat"
    chat_dir.mkdir()
    chat_file = chat_dir / "chat.txt"
    chat_file.write_text(
        "01/01/2024, 10:00 - Alice: photo.jpg (file attached)\n"
        "01/01/2024, 10:01 - Bob: Hi"
    )
    photo = chat_dir / "photo.jpg"
    photo.write_bytes(b"img")
    (chat_dir / "unrelated.jpg").write_bytes(b"bad")

    data = ChatCollection()
    exported_handler.messages(str(chat_file), data, False, False)

    out_dir = tmp_path / "out"
    out_dir.mkdir()

    from Whatsapp_Chat_Exporter.__main__ import copy_exported_media

    copy_exported_media(str(chat_file), data, str(out_dir))

    copied = list((out_dir / "media").rglob("*"))
    assert (out_dir / "media" / "photo.jpg") in copied
    assert (out_dir / "media" / "unrelated.jpg") not in copied
    chat = data["ExportedChat"]
    first = next(iter(chat.values()))
    assert first.data == str(Path("media") / "photo.jpg")
=======
import builtins
from pathlib import Path
from Whatsapp_Chat_Exporter import exported_handler
from Whatsapp_Chat_Exporter.data_model import ChatCollection


def test_messages_no_prompt(tmp_path, monkeypatch):
    chat_file = tmp_path / "chat.txt"
    chat_file.write_text(
        "01/01/2024, 10:00 - Alice: Hello\n01/01/2024, 10:01 - Bob: Hi"
    )
    data = ChatCollection()
    called = False

    def fake_input(prompt):
        nonlocal called
        called = True
        return "n"

    monkeypatch.setattr(builtins, "input", fake_input)
    exported_handler.messages(
        str(chat_file),
        data,
        assume_first_as_me=False,
        prompt_user=False,
    )
    assert not called
    assert "ExportedChat" in data
    chat = data["ExportedChat"]
    assert len(chat) == 2

def test_attached_file_traversal_rejected(tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("oops")

    chat_file = tmp_path / "chat.txt"
    chat_file.write_text(
        "01/01/2024, 10:00 - Alice: ../outside.txt (file attached)"
    )

    data = ChatCollection()
    exported_handler.messages(
        str(chat_file),
        data,
        assume_first_as_me=False,
        prompt_user=False,
    )

    chat = data["ExportedChat"]
    msg = chat.get_message(0)
    assert msg.data == "The media is missing"
    assert msg.meta
>>>>>>> 0b087d242fb332e1e94c87caa74b2b5dc3ef79a0
