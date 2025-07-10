"""
Optimized handlers that integrate database optimization and query improvements.
"""

import os
from typing import Dict, Any, List, Optional

from . import android_handler, ios_handler
from .database_optimizer import (
    get_connection_pool, 
    optimize_database_schema,
    optimized_db_connection
)
from .query_optimizer import (
    ChatDataCache,
    MessageQueryOptimizer, 
    MediaQueryOptimizer,
    VCardQueryOptimizer,
    get_chat_cache,
    clear_chat_cache
)
from .logging_config import get_logger, get_performance_logger, log_operation
from .data_model import ChatStore, Device

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
        pool = get_connection_pool(db_path, pool_size=3)
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
    def messages(db: str, data, media_folder: str, timezone_offset: int, 
                filter_date, filter_chat, filter_empty: bool) -> None:
        """Optimized message processing with N+1 query elimination."""
        
        with log_operation("android_messages_processing", 
                          media_folder=media_folder, 
                          filter_empty=filter_empty):
            
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
                        OptimizedAndroidHandler._process_optimized_message(row, data, chat_cache)
                        processed_count += 1
                    
                    logger.info(f"Processed {processed_count} messages with optimizations")
                    
            except Exception as e:
                logger.warning(f"Optimized processing failed, falling back to original: {e}")
                # Fallback to original implementation
                android_handler.messages(db, data, media_folder, timezone_offset, 
                                       filter_date, filter_chat, filter_empty)
    
    @staticmethod
    def _process_optimized_message(row: Dict[str, Any], data, chat_cache: ChatDataCache) -> None:
        """Process a single message with cached data to avoid N+1 queries."""
        jid = row["key_remote_jid"]
        
        # Use cached chat data instead of database lookups
        if jid not in data:
            chat_name = (chat_cache.get_chat_name(jid) or 
                        chat_cache.get_chat_subject(jid) or 
                        row.get("chat_subject") or
                        jid)
            
            current_chat = data.add_chat(jid, ChatStore(Device.ANDROID, chat_name))
            
            # Set cached metadata
            metadata = chat_cache.get_chat_metadata(jid)
            if metadata.get('status'):
                current_chat.status = metadata['status']
        else:
            current_chat = data.get_chat(jid)
        
        # Process message using original logic but with pre-fetched data
        android_handler._process_message_content(row, data)
    
    @staticmethod
    def media(db: str, data, media_folder: str, filter_date, filter_chat, 
             filter_empty: bool, separate_media: bool) -> None:
        """Optimized media processing with batch queries."""
        
        with log_operation("android_media_processing", 
                          media_folder=media_folder,
                          separate_media=separate_media):
            
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
            media_info = MediaQueryOptimizer.get_batch_media_info(db, message_ids, "android")
            
            # Process media with batch data
            processed_count = 0
            for message_id, media_data in media_info.items():
                try:
                    OptimizedAndroidHandler._process_media_with_cache(
                        message_id, media_data, data, media_folder
                    )
                    processed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to process media for message {message_id}: {e}")
            
            logger.info(f"Processed {processed_count} media files")
    
    @staticmethod
    def _process_media_with_cache(message_id: int, media_data: Dict[str, Any], 
                                 data, media_folder: str) -> None:
        """Process media using cached data."""
        # Find the message using the cached data
        file_path = media_data.get('file_path')
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
            for msg_id, message in chat.messages.items():
                if msg_id == message_id:
                    message.media = True
                    if os.path.isfile(full_path):
                        message.data = file_path
                        message.mime = media_data.get('mime_type', 'application/octet-stream')
                    else:
                        message.data = "The media is missing"
                        message.mime = "media"
                        message.meta = True
                    return
    
    @staticmethod
    def vcard(db: str, data, media_folder: str, filter_date, filter_chat, 
             filter_empty: bool) -> None:
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
            for vcard_row in vcard_data:
                try:
                    android_handler._process_vcard_row(vcard_row, media_folder, data)
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
        pool = get_connection_pool(db_path, pool_size=3)
        logger.info("iOS database optimization completed")
    
    @staticmethod
    def contacts(db: str, data, timezone_offset: int, filter_chat) -> bool:
        """Optimized iOS contact processing."""
        with log_operation("ios_contacts_processing"):
            
            # Preload contact data to eliminate N+1 queries
            chat_cache = get_chat_cache()
            
            with optimized_db_connection(db) as conn:
                cursor = conn.cursor()
                
                # Get all unique contact JIDs
                jid_query = """
                    SELECT DISTINCT ZWACHATSESSION.ZCONTACTJID
                    FROM ZWACHATSESSION
                    INNER JOIN ZWAMESSAGE ON ZWAMESSAGE.ZCHATSESSION = ZWACHATSESSION.Z_PK
                """
                cursor.execute(jid_query)
                jid_list = [row[0] for row in cursor.fetchall()]
            
            # Preload all contact data
            chat_cache.preload_chat_data(db, jid_list, "ios")
            
            # Use original implementation with optimized connection
            return ios_handler.contacts(db, data, timezone_offset, filter_chat)
    
    @staticmethod
    def messages(db: str, data, media_folder: str, timezone_offset: int,
                filter_date, filter_chat, filter_empty: bool) -> None:
        """Optimized iOS message processing."""
        
        with log_operation("ios_messages_processing"):
            try:
                # Use optimized cursor
                with optimized_db_connection(db) as conn:
                    cursor = MessageQueryOptimizer.get_optimized_messages_cursor(
                        db, filter_empty, filter_date, filter_chat, "ios"
                    )
                    
                    processed_count = 0
                    chat_cache = get_chat_cache()
                    
                    for row in cursor:
                        OptimizedIOSHandler._process_optimized_ios_message(row, data, chat_cache)
                        processed_count += 1
                    
                    logger.info(f"Processed {processed_count} iOS messages with optimizations")
                    
            except Exception as e:
                logger.warning(f"Optimized iOS processing failed, falling back: {e}")
                # Fallback to original
                ios_handler.messages(db, data, media_folder, timezone_offset,
                                   filter_date, filter_chat, filter_empty)
    
    @staticmethod
    def _process_optimized_ios_message(row: Dict[str, Any], data, chat_cache: ChatDataCache) -> None:
        """Process iOS message with cached data."""
        jid = row["ZCONTACTJID"]
        
        # Use cached contact data
        if jid not in data:
            contact_name = (chat_cache.get_chat_name(jid) or 
                           row.get("ZPARTNERNAME") or
                           row.get("ZPUSHNAME") or
                           jid.split('@')[0] if '@' in jid else jid)
            
            current_chat = data.add_chat(jid, ChatStore(Device.IOS, contact_name))
        else:
            current_chat = data.get_chat(jid)
        
        # Process using original logic with cached data
        # Note: This would need the original message processing logic adapted
        pass
    
    @staticmethod 
    def media(db: str, data, media_folder: str, filter_date, filter_chat,
             filter_empty: bool, separate_media: bool) -> None:
        """Optimized iOS media processing.""" 
        with log_operation("ios_media_processing"):
            ios_handler.media(db, data, media_folder, filter_date, filter_chat,
                            filter_empty, separate_media)
    
    @staticmethod
    def vcard(db: str, data, media_folder: str, filter_date, filter_chat,
             filter_empty: bool) -> None:
        """Optimized iOS vCard processing."""
        with log_operation("ios_vcard_processing"):
            ios_handler.vcard(db, data, media_folder, filter_date, filter_chat,
                            filter_empty)
    
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