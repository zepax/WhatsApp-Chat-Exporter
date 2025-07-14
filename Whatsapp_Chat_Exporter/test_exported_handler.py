import builtins

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
    chat_file.write_text("01/01/2024, 10:00 - Alice: ../outside.txt (file attached)")

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


def test_attached_file_found_in_media_dir(tmp_path):
    base = tmp_path / "chat"
    base.mkdir()
    media = base / "Media"
    media.mkdir()
    file_path = media / "photo.jpg"
    file_path.write_text("data")

    chat_file = base / "chat.txt"
    chat_file.write_text("01/01/2024, 10:00 - Alice: photo.jpg (file attached)")

    data = ChatCollection()
    exported_handler.messages(
        str(chat_file),
        data,
        assume_first_as_me=False,
        prompt_user=False,
    )

    chat = data["ExportedChat"]
    msg = chat.get_message(0)
    assert msg.data == str(file_path)
