from types import SimpleNamespace

from Whatsapp_Chat_Exporter import android_handler
from Whatsapp_Chat_Exporter.__main__ import export_multiple_json
from Whatsapp_Chat_Exporter.data_model import ChatCollection, ChatStore, Message
from Whatsapp_Chat_Exporter.utility import Device


def _msg() -> Message:
    return Message(
        from_me=1,
        timestamp=1,
        time=1,
        key_id=1,
        received_timestamp=1,
        read_timestamp=1,
    )


def test_group_and_individual_dirs(tmp_path):
    data = ChatCollection()
    chat_ind = ChatStore(Device.ANDROID, name="Alice", is_group=False)
    chat_ind.add_message("1", _msg())
    data.add_chat("111@c.us", chat_ind)

    chat_grp = ChatStore(Device.ANDROID, name="Group", is_group=True)
    chat_grp.add_message("1", _msg())
    data.add_chat("111-222@g.us", chat_grp)

    android_handler.create_html(data, str(tmp_path), headline="Chat history with ??")

    assert (tmp_path / "individuals").is_dir()
    assert (tmp_path / "groups").is_dir()
    assert any(f.suffix == ".html" for f in (tmp_path / "individuals").iterdir())
    assert any(f.suffix == ".html" for f in (tmp_path / "groups").iterdir())

    args = SimpleNamespace(
        json=str(tmp_path / "json"), avoid_encoding_json=False, pretty_print_json=None
    )
    export_multiple_json(args, {jid: chat.to_json() for jid, chat in data.items()})

    assert (tmp_path / "json" / "individuals").is_dir()
    assert (tmp_path / "json" / "groups").is_dir()
