from Whatsapp_Chat_Exporter.chat_cleaner import ChatCleaner
from Whatsapp_Chat_Exporter.data_model import ChatCollection, ChatStore, Message
from Whatsapp_Chat_Exporter.utility import Device


def _make_message(text: str | None, ts: int = 1) -> Message:
    msg = Message(
        from_me=1,
        timestamp=ts,
        time=ts,
        key_id=ts,
        received_timestamp=ts,
        read_timestamp=ts,
    )
    msg.data = text
    if text is None:
        msg.media = False
    return msg


def test_clean_removes_empty_messages():
    collection = ChatCollection()
    chat = ChatStore(Device.ANDROID)
    chat.add_message("1", _make_message(None))
    chat.add_message("2", _make_message("hi"))
    collection.add_chat("c", chat)

    ChatCleaner.clean(collection)

    assert list(chat.keys()) == ["2"]


def test_clean_deduplicates():
    collection = ChatCollection()
    chat = ChatStore(Device.ANDROID)
    chat.add_message("1", _make_message("hi", 1))
    chat.add_message("2", _make_message("hi", 1))
    collection.add_chat("c", chat)

    ChatCleaner.clean(collection)

    assert len(chat) == 1


def test_clean_removes_empty_chats():
    collection = ChatCollection()
    chat = ChatStore(Device.ANDROID)
    chat.add_message("1", _make_message(None))
    collection.add_chat("c", chat)

    ChatCleaner.clean(collection)

    assert len(collection) == 0
