from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable, List, Optional

from Whatsapp_Chat_Exporter.data_model import ChatCollection, Message


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    STICKER = "sticker"
    SYSTEM = "system"
    OTHER = "other"


class DeliveryStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"


@dataclass
class NormalizedMessage:
    chat_id: str
    message_id: str
    sender: Optional[str]
    timestamp: str
    content: Optional[str]
    message_type: MessageType
    status: DeliveryStatus
    media_path: Optional[str]
    received_at: Optional[str]
    read_at: Optional[str]


def _infer_message_type(msg: Message) -> MessageType:
    if msg.meta:
        return MessageType.SYSTEM
    if msg.sticker:
        return MessageType.STICKER
    if msg.mime:
        if msg.mime.startswith("image/"):
            return MessageType.IMAGE
        if msg.mime.startswith("video/"):
            return MessageType.VIDEO
        if msg.mime.startswith("audio/"):
            return MessageType.AUDIO
    return MessageType.TEXT if not msg.media else MessageType.OTHER


def _infer_status(msg: Message) -> DeliveryStatus:
    if msg.read_timestamp is not None:
        return DeliveryStatus.READ
    if msg.received_timestamp is not None:
        return DeliveryStatus.DELIVERED
    return DeliveryStatus.SENT


def normalize_chats(collection: ChatCollection) -> List[NormalizedMessage]:
    """Convert ChatCollection data to a list of NormalizedMessage objects."""
    normalized: List[NormalizedMessage] = []
    for chat_id, chat in collection.items():
        for msg_id, msg in chat.items():
            ts = datetime.fromtimestamp(msg.timestamp, tz=timezone.utc).isoformat()
            norm = NormalizedMessage(
                chat_id=chat_id,
                message_id=str(msg_id),
                sender=msg.sender if not msg.from_me else "me",
                timestamp=ts,
                content=msg.caption if msg.media else msg.data,
                message_type=_infer_message_type(msg),
                status=_infer_status(msg),
                media_path=msg.data if msg.media else None,
                received_at=msg.received_timestamp,
                read_at=msg.read_timestamp,
            )
            normalized.append(norm)
    return normalized

