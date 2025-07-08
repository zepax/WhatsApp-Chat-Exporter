<<<<<<< HEAD
"""Data normalization utilities for WhatsApp chats."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Iterator, Optional

from pydantic import BaseModel

from Whatsapp_Chat_Exporter.data_model import ChatCollection, Message


class NormalizedMessage(BaseModel):
    """Normalized representation of a WhatsApp message."""

    chat_id: str
    sender: Optional[str]
    timestamp: datetime
    message_type: str
    content: Optional[str] = None
    media_path: Optional[str] = None
    mime_type: Optional[str] = None
    delivered: Optional[datetime] = None
    read: Optional[datetime] = None
    from_me: bool


def _to_datetime(ts: Optional[int | str], tz_offset: int) -> Optional[datetime]:
    if ts is None:
        return None
    tz = timezone(timedelta(hours=tz_offset))
    if isinstance(ts, str):
        try:
            return datetime.strptime(ts, "%Y/%m/%d %H:%M").replace(tzinfo=tz)
        except ValueError:
            return None
    seconds = ts if ts < 1_000_000_000_0 else ts / 1000
    return datetime.fromtimestamp(seconds, tz)


def _message_type(msg: Message) -> str:
    if msg.meta:
        return "meta"
    if msg.media:
        return "media"
    return "text"


def normalize_collection(
    collection: ChatCollection, tz_offset: int = 0
) -> Iterator[NormalizedMessage]:
    """Yield normalized messages from a :class:`ChatCollection`.

    Args:
        collection: Parsed chat collection.
        tz_offset: Hours offset from UTC for timestamps.

    Yields:
        :class:`NormalizedMessage` objects.
    """

    for chat_id, chat in collection.items():
        for message in chat.values():
            yield NormalizedMessage(
                chat_id=chat_id,
                sender=message.sender if not message.from_me else None,
                timestamp=_to_datetime(message.timestamp, tz_offset),
                message_type=_message_type(message),
                content=message.data,
                media_path=message.data if message.media else None,
                mime_type=message.mime,
                delivered=_to_datetime(message.received_timestamp, tz_offset),
                read=_to_datetime(message.read_timestamp, tz_offset),
                from_me=message.from_me,
            )
=======
"""Data normalization utilities for WhatsApp chats."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Iterator, Optional

from pydantic import BaseModel

from Whatsapp_Chat_Exporter.data_model import ChatCollection, Message


class NormalizedMessage(BaseModel):
    """Normalized representation of a WhatsApp message."""

    chat_id: str
    sender: Optional[str]
    timestamp: datetime
    message_type: str
    content: Optional[str] = None
    media_path: Optional[str] = None
    mime_type: Optional[str] = None
    delivered: Optional[datetime] = None
    read: Optional[datetime] = None
    from_me: bool


def _to_datetime(ts: Optional[int | str], tz_offset: int) -> Optional[datetime]:
    if ts is None:
        return None
    tz = timezone(timedelta(hours=tz_offset))
    if isinstance(ts, str):
        try:
            return datetime.strptime(ts, "%Y/%m/%d %H:%M").replace(tzinfo=tz)
        except ValueError:
            return None
    seconds = ts if ts < 1_000_000_000_0 else ts / 1000
    return datetime.fromtimestamp(seconds, tz)


def _message_type(msg: Message) -> str:
    if msg.meta:
        return "meta"
    if msg.media:
        return "media"
    return "text"


def normalize_collection(
    collection: ChatCollection, tz_offset: int = 0
) -> Iterator[NormalizedMessage]:
    """Yield normalized messages from a :class:`ChatCollection`.

    Args:
        collection: Parsed chat collection.
        tz_offset: Hours offset from UTC for timestamps.

    Yields:
        :class:`NormalizedMessage` objects.
    """

    for chat_id, chat in collection.items():
        for message in chat.values():
            yield NormalizedMessage(
                chat_id=chat_id,
                sender=message.sender if not message.from_me else None,
                timestamp=_to_datetime(message.timestamp, tz_offset),
                message_type=_message_type(message),
                content=message.data,
                media_path=message.data if message.media else None,
                mime_type=message.mime,
                delivered=_to_datetime(message.received_timestamp, tz_offset),
                read=_to_datetime(message.read_timestamp, tz_offset),
                from_me=message.from_me,
            )
>>>>>>> 0b087d242fb332e1e94c87caa74b2b5dc3ef79a0
