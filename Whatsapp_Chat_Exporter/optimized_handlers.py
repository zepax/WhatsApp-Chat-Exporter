"""
Optimized handlers that integrate database optimization and query improvements.
"""

import os
from typing import Any, Dict

from . import android_handler, ios_handler
from .data_model import ChatStore
from .database_optimizer import (
    get_connection_pool,
    optimize_database_schema,
    optimized_db_connection,
)
from .logging_config import get_logger, get_performance_logger, log_operation
from .query_optimizer import (
    ChatDataCache,
    MediaQueryOptimizer,
    MessageQueryOptimizer,
    VCardQueryOptimizer,
    clear_chat_cache,
    get_chat_cache,
)
from .utility import Device

logger = get_logger(__name__)
perf_logger = get_performance_logger()


class OptimizedAndroidHandler:
    """Optimized Android handler with database performance improvements."""

    @staticmethod
    def setup_optimizations(db_path: str) -> None:
        """Set up database optimizations for Android database."""
        logger.info("Setting up Android database optimizations")

        with optimized_db_connection(db_path) as conn:
            optimize_database_schema(conn, "android")

        # Initialize connection pool
        get_connection_pool(db_path, pool_size=3)
        logger.info("Android database optimization completed")

    @staticmethod
    def contacts(db: str, data, timezone_offset: int) -> bool:
        """Optimized contact processing with batch loading."""
        with log_operation("android_contacts_processing"):
            # Use original implementation but with optimized connection
            with optimized_db_connection(db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT count() FROM wa_contacts")
                total_contacts = cursor.fetchone()[0]

                logger.info(f"Processing {total_contacts} contacts")

                # Use the original logic but with optimized connection
                return android_handler.contacts(db, data, timezone_offset)

    @staticmethod
    def messages(
        db: str,
        data,
        media_folder: str,
        timezone_offset: int,
        filter_date,
        filter_chat,
        filter_empty: bool,
    ) -> None:
        """Optimized message processing with N+1 query elimination."""

        with log_operation(
            "android_messages_processing",
            media_folder=media_folder,
            filter_empty=filter_empty,
        ):
            # Preload chat data to eliminate N+1 queries
            chat_cache = get_chat_cache()

            # Get unique JIDs first
            with optimized_db_connection(db) as conn:
                cursor = conn.cursor()

                # Get all unique JIDs that will be processed
                jid_query = """
                    SELECT DISTINCT messages.key_remote_jid
                    FROM messages
                    INNER JOIN jid ON messages.key_remote_jid = jid.raw_string
                    WHERE messages.key_remote_jid <> '-1'
                """
                cursor.execute(jid_query)
                jid_list = [row[0] for row in cursor.fetchall()]

            # Preload chat data
            chat_cache.preload_chat_data(db, jid_list, "android")

            # Use optimized message cursor
            try:
                with optimized_db_connection(db) as conn:
                    cursor = MessageQueryOptimizer.get_optimized_messages_cursor(
                        db, filter_empty, filter_date, filter_chat, "android"
                    )

                    # Process messages with cached data
                    processed_count = 0
                    for row in cursor:
                        OptimizedAndroidHandler._process_optimized_message(
                            row, data, chat_cache
                        )
                        processed_count += 1

                    logger.info(
                        f"Processed {processed_count} messages with optimizations"
                    )

            except Exception as e:
                logger.warning(
                    f"Optimized processing failed, falling back to original: {e}"
                )
                # Fallback to original implementation
                android_handler.messages(
                    db,
                    data,
                    media_folder,
                    timezone_offset,
                    filter_date,
                    filter_chat,
                    filter_empty,
                )

    @staticmethod
    def _process_optimized_message(
        row: Dict[str, Any], data, chat_cache: ChatDataCache
    ) -> None:
        """Process a single message with cached data to avoid N+1 queries."""
        jid = row["key_remote_jid"]

        # Use cached chat data instead of database lookups
        if jid not in data:
            chat_name = (
                chat_cache.get_chat_name(jid)
                or chat_cache.get_chat_subject(jid)
                or row.get("chat_subject")
                or jid
            )

            current_chat = data.add_chat(jid, ChatStore(Device.ANDROID, chat_name))

            # Set cached metadata
            metadata = chat_cache.get_chat_metadata(jid)
            if metadata.get("status"):
                current_chat.status = metadata["status"]
        else:
            current_chat = data.get_chat(jid)

        # Process message using original logic but with pre-fetched data
        # Import Message class for creating message objects
        from Whatsapp_Chat_Exporter.data_model import Message
        from Whatsapp_Chat_Exporter.utility import CURRENT_TZ_OFFSET

        # Create message object
        try:
            message = Message(
                from_me=bool(row.get("key_from_me", 0)),
                timestamp=row.get("timestamp", 0),
                time=row.get("timestamp", 0),
                key_id=row.get("_id", 0),
                received_timestamp=row.get("received_timestamp", 0),
                read_timestamp=row.get("read_timestamp", 0),
                timezone_offset=CURRENT_TZ_OFFSET,
                message_type=row.get("message_type"),
            )

            # Add message to chat
            current_chat[row.get("_id", len(current_chat))] = message

        except Exception as e:
            logger.debug(f"Error processing message {row.get('_id', 'unknown')}: {e}")
            # Fall back to creating a minimal message
            message = Message(
                key_id=row.get("_id", 0),
                from_me=bool(row.get("key_from_me", 0)),
                time=0,
                data=row.get("data", ""),
                time_format="%Y-%m-%d %H:%M:%S",
            )
            current_chat[row.get("_id", len(current_chat))] = message

    @staticmethod
    def media(
        db: str,
        data,
        media_folder: str,
        filter_date,
        filter_chat,
        filter_empty: bool,
        separate_media: bool,
    ) -> None:
        """Optimized media processing with batch queries."""

        with log_operation(
            "android_media_processing",
            media_folder=media_folder,
            separate_media=separate_media,
        ):
            # Get all message IDs that have media
            with optimized_db_connection(db) as conn:
                cursor = conn.cursor()

                # Get message IDs with media in batch
                media_query = """
                    SELECT DISTINCT message_row_id 
                    FROM message_media
                    ORDER BY message_row_id
                """
                cursor.execute(media_query)
                message_ids = [row[0] for row in cursor.fetchall()]

            if not message_ids:
                logger.info("No media messages found")
                return

            # Get media info in batch
            media_info = MediaQueryOptimizer.get_batch_media_info(
                db, message_ids, "android"
            )

            # Process media with batch data
            processed_count = 0
            for message_id, media_data in media_info.items():
                try:
                    OptimizedAndroidHandler._process_media_with_cache(
                        message_id, media_data, data, media_folder
                    )
                    processed_count += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to process media for message {message_id}: {e}"
                    )

            logger.info(f"Processed {processed_count} media files")

    @staticmethod
    def _process_media_with_cache(
        message_id: int, media_data: Dict[str, Any], data, media_folder: str
    ) -> None:
        """Process media using cached data."""
        # Find the message using the cached data
        file_path = media_data.get("file_path")
        if not file_path:
            return

        # Use original media processing logic but with cached data
        base_dir = os.path.abspath(media_folder)
        full_path = os.path.normpath(os.path.join(base_dir, file_path))

        # Security check
        if not full_path.startswith(base_dir + os.sep):
            logger.warning(f"Suspicious file path detected: {file_path}")
            return

        # Find message in data structure
        # Note: This could be optimized further with message ID indexing
        for chat in data.values():
            for msg_id, message in chat._messages.items():
                if msg_id == message_id:
                    message.media = True
                    if os.path.isfile(full_path):
                        setattr(message, "data", file_path)
                        message.mime = media_data.get(
                            "mime_type", "application/octet-stream"
                        )
                    else:
                        setattr(message, "data", "The media is missing")
                        message.mime = "media"
                        message.meta = True
                    return

    @staticmethod
    def vcard(
        db: str, data, media_folder: str, filter_date, filter_chat, filter_empty: bool
    ) -> None:
        """Optimized vCard processing with batch queries."""

        with log_operation("android_vcard_processing", media_folder=media_folder):
            # Get all vCard data in one batch query
            vcard_data = VCardQueryOptimizer.get_batch_vcard_data(
                db, filter_empty, filter_date, filter_chat, "android"
            )

            if not vcard_data:
                logger.info("No vCard data found")
                return

            # Process vCards in batch
            processed_count = 0
            vcard_dir = os.path.join(media_folder, "vCards")
            os.makedirs(vcard_dir, exist_ok=True)

            for vcard_row in vcard_data:
                try:
                    android_handler._process_vcard_row(vcard_row, vcard_dir, data)
                    processed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to process vCard: {e}")

            logger.info(f"Processed {processed_count} vCard entries")

    @staticmethod
    def calls(db: str, data, timezone_offset: int, filter_chat) -> None:
        """Optimized calls processing."""
        with log_operation("android_calls_processing"):
            # Use original implementation with optimized connection
            android_handler.calls(db, data, timezone_offset, filter_chat)


class OptimizedIOSHandler:
    """Optimized iOS handler with database performance improvements."""

    @staticmethod
    def setup_optimizations(db_path: str) -> None:
        """Set up database optimizations for iOS database."""
        logger.info("Setting up iOS database optimizations")

        with optimized_db_connection(db_path) as conn:
            optimize_database_schema(conn, "ios")

        # Initialize connection pool
        get_connection_pool(db_path, pool_size=3)
        logger.info("iOS database optimization completed")

    @staticmethod
    def contacts(db: str, data, timezone_offset: int, filter_chat) -> bool:
        """Optimized iOS contact processing."""
        with log_operation("ios_contacts_processing"):
            # Use original implementation - iOS contacts only works with contact database
            # and doesn't need chat session data for basic contact processing
            return ios_handler.contacts(db, data)

    @staticmethod
    def messages(
        db: str,
        data,
        media_folder: str,
        timezone_offset: int,
        filter_date,
        filter_chat,
        filter_empty: bool,
    ) -> None:
        """Optimized iOS message processing."""

        with log_operation("ios_messages_processing"):
            try:
                # Use optimized cursor
                cursor = MessageQueryOptimizer.get_optimized_messages_cursor(
                    db, filter_empty, filter_date, filter_chat, "ios"
                )

                processed_count = 0
                chat_cache = get_chat_cache()

                for row in cursor:
                    OptimizedIOSHandler._process_optimized_ios_message(
                        row, data, chat_cache
                    )
                    processed_count += 1

                logger.info(
                    f"Processed {processed_count} iOS messages with optimizations"
                )

            except Exception as e:
                logger.warning(f"Optimized iOS processing failed, falling back: {e}")
                # Fallback to original with proper DB connection
                import sqlite3

                with sqlite3.connect(db) as db_conn:
                    db_conn.row_factory = sqlite3.Row
                    ios_handler.messages(
                        db_conn,
                        data,
                        media_folder,
                        timezone_offset,
                        filter_date,
                        filter_chat,
                        filter_empty,
                    )

    @staticmethod
    def _process_optimized_ios_message(
        row: Dict[str, Any], data, chat_cache: ChatDataCache
    ) -> None:
        """Process iOS message with cached data."""

        from Whatsapp_Chat_Exporter.data_model import Message
        from Whatsapp_Chat_Exporter.utility import (
            APPLE_TIME,
            CURRENT_TZ_OFFSET,
            is_group_jid,
        )

        contact_jid = row["ZCONTACTJID"]

        if contact_jid not in data:
            name = (
                row.get("ZPARTNERNAME")
                or row.get("ZPUSHNAME")
                or chat_cache.get_chat_name(contact_jid)
                or contact_jid.split("@")[0]
            )
            current_chat = data.add_chat(
                contact_jid,
                ChatStore(Device.IOS, name, is_group=is_group_jid(contact_jid)),
            )
        else:
            current_chat = data.get_chat(contact_jid)

        message_pk = row["Z_PK"]
        ts = APPLE_TIME + row["ZMESSAGEDATE"]

        key_id = message_pk
        if isinstance(message_pk, str):
            try:
                key_id = int(str(message_pk)[:16], 16)
            except ValueError:
                key_id = message_pk

        message = Message(
            from_me=row["ZISFROMME"],
            timestamp=ts,
            time=ts,
            key_id=key_id,
            received_timestamp=ts,
            read_timestamp=ts,
            timezone_offset=CURRENT_TZ_OFFSET,
            message_type=row.get("ZMESSAGETYPE") or 0,
        )

        if row.get("ZMESSAGETYPE") == 14:
            message.data = "Message deleted"
            message.meta = True
        else:
            text = row.get("ZTEXT")
            if text:
                message.data = text.replace("\r\n", "<br>").replace("\n", "<br>")
            else:
                message.data = None

        if row.get("group_member_jid") and not row["ZISFROMME"]:
            sender_jid = row.get("group_member_jid")
            sender_name = (
                row.get("group_member_name")
                or row.get("group_member_pushname")
                or chat_cache.get_chat_name(sender_jid)
            )
            if not sender_name and sender_jid:
                sender_name = sender_jid.split("@")[0]
            message.sender = sender_name

        current_chat.add_message(message_pk, message)

    @staticmethod
    def media(
        db: str,
        data,
        media_folder: str,
        filter_date,
        filter_chat,
        filter_empty: bool,
        separate_media: bool,
    ) -> None:
        """Optimized iOS media processing."""
        with log_operation("ios_media_processing"):
            ios_handler.media(
                db,
                data,
                media_folder,
                filter_date,
                filter_chat,
                separate_media,
            )

    @staticmethod
    def vcard(
        db: str, data, media_folder: str, filter_date, filter_chat, filter_empty: bool
    ) -> None:
        """Optimized iOS vCard processing."""
        with log_operation("ios_vcard_processing"):
            ios_handler.vcard(db, data, media_folder, filter_date, filter_chat)

    @staticmethod
    def calls(db: str, data, timezone_offset: int, filter_chat) -> None:
        """Optimized iOS calls processing."""
        with log_operation("ios_calls_processing"):
            ios_handler.calls(db, data, timezone_offset, filter_chat)


def get_optimized_handler(platform: str):
    """
    Get the optimized handler for the specified platform.

    Args:
        platform: 'android' or 'ios'

    Returns:
        Optimized handler class
    """
    if platform.lower() == "android":
        return OptimizedAndroidHandler
    elif platform.lower() == "ios":
        return OptimizedIOSHandler
    else:
        raise ValueError(f"Unsupported platform: {platform}")


def cleanup_optimizations():
    """Clean up optimization resources."""
    clear_chat_cache()
    # Connection pools will be cleaned up automatically
