import pytest

from Whatsapp_Chat_Exporter.data_model import ChatCollection, ChatStore, Message
from Whatsapp_Chat_Exporter.utility import Device
from Whatsapp_Chat_Exporter.normalizer import (
    DeliveryStatus,
    MessageType,
    normalize_chats,
)


def create_sample_collection():
    collection = ChatCollection()
    chat = ChatStore(Device.ANDROID, "Alice")
    msg1 = Message(
        from_me=0,
        timestamp=1600000000,
        time=1600000000,
        key_id=1,
        received_timestamp=1600000010,
        read_timestamp=1600000020,
        message_type=0,
    )
    msg1.data = "hi"

    msg2 = Message(
        from_me=1,
        timestamp=1600000100,
        time=1600000100,
        key_id=2,
        received_timestamp=1600000110,
        read_timestamp=None,
        message_type=1,
    )
    msg2.media = True
    msg2.mime = "image/jpeg"
    msg2.data = "/path/img.jpg"

    msg3 = Message(
        from_me=0,
        timestamp=1600000200,
        time=1600000200,
        key_id=3,
        received_timestamp=None,
        read_timestamp=None,
        message_type=0,
    )
    msg3.data = "bye"

    chat.add_message("1", msg1)
    chat.add_message("2", msg2)
    chat.add_message("3", msg3)
    collection.add_chat("123@s.whatsapp.net", chat)
    return collection


def test_normalize_chats():
    col = create_sample_collection()
    result = normalize_chats(col)
    assert len(result) == 3

    m1, m2, m3 = result
    assert m1.status == DeliveryStatus.READ
    assert m1.message_type == MessageType.TEXT

    assert m2.status == DeliveryStatus.DELIVERED
    assert m2.message_type == MessageType.IMAGE

    assert m3.status == DeliveryStatus.SENT
    assert m3.message_type == MessageType.TEXT

