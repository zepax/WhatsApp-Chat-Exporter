from Whatsapp_Chat_Exporter.data_model import ChatCollection, ChatStore, Message
from Whatsapp_Chat_Exporter.utility import Device
from Whatsapp_Chat_Exporter.normalizer import normalize_collection


def test_normalize_collection():
    collection = ChatCollection()
    chat = ChatStore(Device.ANDROID, name="Alice")
    msg = Message(
        from_me=1,
        timestamp=1_660_000_000,
        time=1_660_000_000,
        key_id=1,
        received_timestamp=1_660_000_001,
        read_timestamp=1_660_000_002,
        timezone_offset=0,
    )
    msg.data = "hello"
    chat.add_message("1", msg)
    collection.add_chat("123@c.us", chat)

    normalized = list(normalize_collection(collection))
    assert len(normalized) == 1
    n = normalized[0]
    assert n.chat_id == "123@c.us"
    assert n.content == "hello"
    assert n.from_me is True
    assert n.timestamp.tzinfo is not None
