import json
from types import SimpleNamespace
from Whatsapp_Chat_Exporter.__main__ import export_summary
from Whatsapp_Chat_Exporter.data_model import ChatCollection, ChatStore, Message
from Whatsapp_Chat_Exporter.utility import Device


def test_export_summary(tmp_path):
    collection = ChatCollection()
    chat = ChatStore(Device.ANDROID, name="Alice")
    msg = Message(
        from_me=1,
        timestamp=1,
        time=1,
        key_id=1,
        received_timestamp=1,
        read_timestamp=1,
    )
    chat.add_message("1", msg)
    collection.add_chat("alice", chat)

    args = SimpleNamespace(summary=str(tmp_path / "summary.json"))
    export_summary(args, collection)

    with open(args.summary) as f:
        data = json.load(f)

    assert data["total_chats"] == 1
    assert data["chats"]["alice"]["message_count"] == 1
