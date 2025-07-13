from __future__ import annotations

from typing import Set, Tuple

from .data_model import ChatCollection


class ChatCleaner:
    """Utility for removing unwanted messages from chats."""

    @staticmethod
    def clean(
        collection: ChatCollection,
        remove_empty: bool = True,
        deduplicate: bool = True,
    ) -> None:
        """Clean chats in place.

        Args:
            collection: Parsed chats.
            remove_empty: Drop messages without text or media.
            deduplicate: Drop duplicate messages based on timestamp and content.
        """
        for chat_id, chat in list(collection.items()):
            seen: Set[Tuple[int, str | None, str | None, bool]] = set()
            for msg_id in list(chat.keys()):
                msg = chat.get_message(msg_id)
                if msg is None:
                    continue
                unique = (msg.timestamp, msg.sender, msg.data, msg.from_me)
                if deduplicate and unique in seen:
                    chat.delete_message(msg_id)
                    continue
                seen.add(unique)
                if remove_empty and not msg.data and not msg.media and not msg.meta:
                    chat.delete_message(msg_id)
            if remove_empty and len(chat) == 0:
                collection.remove_chat(chat_id)
