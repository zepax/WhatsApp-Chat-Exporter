"""
Query optimization utilities to eliminate N+1 problems and improve database performance.
"""

import sqlite3
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict

from .logging_config import get_logger, get_performance_logger
from .database_optimizer import optimized_db_connection, BatchQueryExecutor

logger = get_logger(__name__)
perf_logger = get_performance_logger()


class ChatDataCache:
    """Optimized cache for chat data to eliminate N+1 queries."""
    
    def __init__(self):
        """Initialize the cache."""
        self._chat_names: Dict[str, str] = {}
        self._chat_subjects: Dict[str, str] = {}
        self._chat_metadata: Dict[str, Dict[str, Any]] = {}
        self._loaded_contacts: Set[str] = set()
        
    def preload_chat_data(self, db_path: str, jid_list: List[str], platform: str = "android") -> None:
        """
        Preload chat data for a list of JIDs to avoid N+1 queries.
        
        Args:
            db_path: Database path
            jid_list: List of JIDs to preload
            platform: Platform type ('android' or 'ios')
        """
        if not jid_list:
            return
            
        logger.info(f"Preloading chat data for {len(jid_list)} chats")
        
        with optimized_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            if platform == "android":
                self._preload_android_chat_data(cursor, jid_list)
            elif platform == "ios":
                self._preload_ios_chat_data(cursor, jid_list)
                
        perf_logger.info(
            "Chat data preloaded",
            extra={
                "jid_count": len(jid_list),
                "platform": platform,
                "cached_names": len(self._chat_names),
                "cached_subjects": len(self._chat_subjects)
            }
        )
    
    def _preload_android_chat_data(self, cursor: sqlite3.Cursor, jid_list: List[str]) -> None:
        """Preload Android chat data."""
        # Create placeholders for IN clause
        placeholders = ','.join('?' * len(jid_list))
        
        # Load contact names and display names
        contact_query = f"""
            SELECT jid, COALESCE(display_name, wa_name) as display_name, status
            FROM wa_contacts 
            WHERE jid IN ({placeholders})
        """
        cursor.execute(contact_query, jid_list)
        
        for row in cursor.fetchall():
            jid = row['jid']
            self._chat_names[jid] = row['display_name'] or jid
            if row['status']:
                self._chat_metadata[jid] = {'status': row['status']}
        
        # Load chat subjects from chat table
        chat_query = f"""
            SELECT jid.raw_string, chat.subject
            FROM chat
            INNER JOIN jid ON chat.jid_row_id = jid._id
            WHERE jid.raw_string IN ({placeholders})
        """
        try:
            cursor.execute(chat_query, jid_list)
            for row in cursor.fetchall():
                jid = row['raw_string'] 
                if row['subject']:
                    self._chat_subjects[jid] = row['subject']
        except sqlite3.OperationalError:
            # Fallback for older schema
            pass
    
    def _preload_ios_chat_data(self, cursor: sqlite3.Cursor, jid_list: List[str]) -> None:
        """Preload iOS chat data."""
        placeholders = ','.join('?' * len(jid_list))
        
        # Load contact data from iOS schema
        contact_query = f"""
            SELECT DISTINCT 
                ZWACHATSESSION.ZCONTACTJID,
                ZWACHATSESSION.ZPARTNERNAME,
                ZWAPROFILEPUSHNAME.ZPUSHNAME
            FROM ZWACHATSESSION
            LEFT JOIN ZWAPROFILEPUSHNAME 
                ON ZWACHATSESSION.ZCONTACTJID = ZWAPROFILEPUSHNAME.ZJID
            WHERE ZWACHATSESSION.ZCONTACTJID IN ({placeholders})
        """
        cursor.execute(contact_query, jid_list)
        
        for row in cursor.fetchall():
            jid = row['ZCONTACTJID']
            name = (row['ZPARTNERNAME'] or 
                   row['ZPUSHNAME'] or 
                   jid.split('@')[0] if '@' in jid else jid)
            self._chat_names[jid] = name
    
    def get_chat_name(self, jid: str) -> Optional[str]:
        """Get cached chat name."""
        return self._chat_names.get(jid)
    
    def get_chat_subject(self, jid: str) -> Optional[str]:
        """Get cached chat subject."""
        return self._chat_subjects.get(jid)
    
    def get_chat_metadata(self, jid: str) -> Dict[str, Any]:
        """Get cached chat metadata."""
        return self._chat_metadata.get(jid, {})
    
    def clear(self) -> None:
        """Clear all cached data."""
        self._chat_names.clear()
        self._chat_subjects.clear()
        self._chat_metadata.clear()
        self._loaded_contacts.clear()


class MessageQueryOptimizer:
    """Optimized message queries to reduce database roundtrips."""
    
    @staticmethod
    def get_optimized_messages_cursor(db_path: str, filter_empty, filter_date, filter_chat, 
                                    platform: str = "android") -> sqlite3.Cursor:
        """
        Get an optimized cursor for message retrieval with minimal queries.
        
        Args:
            db_path: Database path
            filter_empty: Empty message filter
            filter_date: Date filter
            filter_chat: Chat filter
            platform: Platform type
            
        Returns:
            Optimized cursor with pre-joined data
        """
        with optimized_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            if platform == "android":
                return MessageQueryOptimizer._get_android_optimized_cursor(
                    cursor, filter_empty, filter_date, filter_chat
                )
            elif platform == "ios":
                return MessageQueryOptimizer._get_ios_optimized_cursor(
                    cursor, filter_empty, filter_date, filter_chat
                )
    
    @staticmethod
    def _get_android_optimized_cursor(cursor: sqlite3.Cursor, filter_empty, filter_date, filter_chat):
        """Get optimized Android message cursor with all required joins."""
        from .android_handler import get_chat_condition, get_cond_for_empty
        
        # Build filters
        empty_filter = get_cond_for_empty(
            filter_empty, "messages.key_remote_jid", "messages.needs_push"
        )
        date_filter = f"AND messages.timestamp {filter_date}" if filter_date else ""
        include_filter = get_chat_condition(
            filter_chat[0], True, 
            ["messages.key_remote_jid", "messages.remote_resource"],
            "jid_global", "android"
        )
        exclude_filter = get_chat_condition(
            filter_chat[1], False,
            ["messages.key_remote_jid", "messages.remote_resource"], 
            "jid_global", "android"
        )
        
        # Optimized query with all necessary joins to minimize later lookups
        query = f"""
            SELECT 
                messages.key_remote_jid,
                messages._id,
                messages.key_from_me,
                messages.timestamp,
                messages.data,
                messages.status,
                messages.edit_version,
                messages.thumb_image,
                messages.remote_resource,
                CAST(messages.media_wa_type as INTEGER) as media_wa_type,
                messages.latitude,
                messages.longitude,
                messages_quotes.key_id as quoted,
                messages.key_id,
                messages_quotes.data as quoted_data,
                messages.media_caption,
                missed_call_logs.video_call,
                chat.subject as chat_subject,
                message_system.action_type,
                message_system_group.is_me_joined,
                jid_old.raw_string as old_jid,
                jid_new.raw_string as new_jid,
                jid_global.type as jid_type,
                COALESCE(receipt_user.receipt_timestamp, messages.received_timestamp) as received_timestamp,
                COALESCE(receipt_user.read_timestamp, receipt_user.played_timestamp, messages.read_device_timestamp) as read_timestamp,
                -- Preload contact information to avoid N+1
                wa_contacts.display_name,
                wa_contacts.wa_name,
                wa_contacts.status as contact_status,
                -- Group sender information
                group_sender.raw_string as group_sender_jid,
                group_contact.display_name as group_sender_name
            FROM messages
                LEFT JOIN messages_quotes ON messages.quoted_row_id = messages_quotes._id
                LEFT JOIN missed_call_logs ON messages._id = missed_call_logs.message_row_id
                INNER JOIN jid jid_global ON messages.key_remote_jid = jid_global.raw_string
                LEFT JOIN chat ON chat.jid_row_id = jid_global._id
                LEFT JOIN message_system ON message_system.message_row_id = messages._id
                LEFT JOIN message_system_group ON message_system_group.message_row_id = messages._id
                LEFT JOIN message_system_number_change ON message_system_number_change.message_row_id = messages._id
                LEFT JOIN jid jid_old ON jid_old._id = message_system_number_change.old_jid_row_id
                LEFT JOIN jid jid_new ON jid_new._id = message_system_number_change.new_jid_row_id
                LEFT JOIN receipt_user ON receipt_user.message_row_id = messages._id
                -- Join contact information to eliminate N+1 lookups
                LEFT JOIN wa_contacts ON wa_contacts.jid = messages.key_remote_jid
                -- Join group sender information
                LEFT JOIN jid group_sender ON group_sender._id = (
                    SELECT sender_jid_row_id FROM message WHERE message._id = messages._id LIMIT 1
                )
                LEFT JOIN wa_contacts group_contact ON group_contact.jid = group_sender.raw_string
            WHERE messages.key_remote_jid <> '-1'
                {empty_filter}
                {date_filter}
                {include_filter}
                {exclude_filter}
            GROUP BY messages._id
            ORDER BY messages.timestamp ASC
        """
        
        cursor.execute(query)
        return cursor
    
    @staticmethod
    def _get_ios_optimized_cursor(cursor: sqlite3.Cursor, filter_empty, filter_date, filter_chat):
        """Get optimized iOS message cursor with all required joins."""
        from .ios_handler import get_chat_condition
        
        # Build filters  
        chat_filter_include = get_chat_condition(
            filter_chat[0], True, ["ZWACHATSESSION.ZCONTACTJID"], "ios"
        )
        chat_filter_exclude = get_chat_condition(
            filter_chat[1], False, ["ZWACHATSESSION.ZCONTACTJID"], "ios" 
        )
        date_filter = f"AND ZWAMESSAGE.ZMESSAGEDATE {filter_date}" if filter_date else ""
        
        # Optimized iOS query with preloaded contact data
        query = f"""
            SELECT 
                ZWAMESSAGE.Z_PK,
                ZWAMESSAGE.ZISFROMME,
                ZWAMESSAGE.ZMESSAGEDATE,
                ZWAMESSAGE.ZTEXT,
                ZWAMESSAGE.ZMEDIAITEM,
                ZWAMESSAGE.ZGROUPMEMBER,
                ZWAMESSAGE.ZCHATSESSION,
                ZWACHATSESSION.ZCONTACTJID,
                -- Preload contact information
                ZWACHATSESSION.ZPARTNERNAME,
                ZWAPROFILEPUSHNAME.ZPUSHNAME,
                -- Group member information
                group_member.ZMEMBERJID as group_member_jid,
                group_contact.ZPARTNERNAME as group_member_name,
                group_contact_push.ZPUSHNAME as group_member_pushname
            FROM ZWAMESSAGE
                INNER JOIN ZWACHATSESSION ON ZWAMESSAGE.ZCHATSESSION = ZWACHATSESSION.Z_PK
                LEFT JOIN ZWAPROFILEPUSHNAME ON ZWACHATSESSION.ZCONTACTJID = ZWAPROFILEPUSHNAME.ZJID
                -- Join group member data to eliminate N+1
                LEFT JOIN ZWAGROUPMEMBER group_member ON ZWAMESSAGE.ZGROUPMEMBER = group_member.Z_PK
                LEFT JOIN ZWACHATSESSION group_chat ON group_member.ZMEMBERJID = group_chat.ZCONTACTJID
                LEFT JOIN ZWAPROFILEPUSHNAME group_contact_push ON group_member.ZMEMBERJID = group_contact_push.ZJID
                LEFT JOIN ZWACHATSESSION group_contact ON group_member.ZMEMBERJID = group_contact.ZCONTACTJID
            WHERE 1=1
                {chat_filter_include}
                {chat_filter_exclude}
                {date_filter}
            ORDER BY ZWAMESSAGE.ZMESSAGEDATE ASC
        """
        
        cursor.execute(query)
        return cursor


class MediaQueryOptimizer:
    """Optimized media queries to reduce file system and database access."""
    
    @staticmethod
    def get_batch_media_info(db_path: str, message_ids: List[int], platform: str = "android") -> Dict[int, Dict[str, Any]]:
        """
        Get media information for multiple messages in a single query.
        
        Args:
            db_path: Database path
            message_ids: List of message IDs
            platform: Platform type
            
        Returns:
            Dictionary mapping message ID to media info
        """
        if not message_ids:
            return {}
            
        media_info = {}
        
        with optimized_db_connection(db_path) as conn:
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(message_ids))
            
            if platform == "android":
                query = f"""
                    SELECT 
                        message_row_id,
                        file_path,
                        media_size,
                        mime_type,
                        media_name,
                        media_caption
                    FROM message_media
                    WHERE message_row_id IN ({placeholders})
                """
                cursor.execute(query, message_ids)
                
                for row in cursor.fetchall():
                    media_info[row['message_row_id']] = {
                        'file_path': row['file_path'],
                        'media_size': row['media_size'],
                        'mime_type': row['mime_type'],
                        'media_name': row['media_name'],
                        'media_caption': row['media_caption']
                    }
            
            elif platform == "ios":
                query = f"""
                    SELECT 
                        ZWAMESSAGE.Z_PK as message_id,
                        ZWAMEDIAITEM.ZMEDIALOCALPATH,
                        ZWAMEDIAITEM.ZMEDIAKEY,
                        ZWAMEDIAITEM.ZFILESIZE,
                        ZWAMEDIAITEM.ZTITLE
                    FROM ZWAMESSAGE
                    INNER JOIN ZWAMEDIAITEM ON ZWAMESSAGE.ZMEDIAITEM = ZWAMEDIAITEM.Z_PK
                    WHERE ZWAMESSAGE.Z_PK IN ({placeholders})
                """
                cursor.execute(query, message_ids)
                
                for row in cursor.fetchall():
                    media_info[row['message_id']] = {
                        'file_path': row['ZMEDIALOCALPATH'],
                        'media_key': row['ZMEDIAKEY'],
                        'file_size': row['ZFILESIZE'],
                        'title': row['ZTITLE']
                    }
        
        perf_logger.info(
            "Batch media info retrieved",
            extra={
                "message_count": len(message_ids),
                "media_found": len(media_info),
                "platform": platform
            }
        )
        
        return media_info


class VCardQueryOptimizer:
    """Optimized vCard processing to minimize file I/O."""
    
    @staticmethod
    def get_batch_vcard_data(db_path: str, filter_empty, filter_date, filter_chat, 
                           platform: str = "android") -> List[Dict[str, Any]]:
        """
        Get all vCard data in a single optimized query.
        
        Args:
            db_path: Database path  
            filter_empty: Empty filter
            filter_date: Date filter
            filter_chat: Chat filter
            platform: Platform type
            
        Returns:
            List of vCard records with all necessary data
        """
        with optimized_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            if platform == "android":
                return VCardQueryOptimizer._get_android_vcard_batch(
                    cursor, filter_empty, filter_date, filter_chat
                )
            elif platform == "ios":
                return VCardQueryOptimizer._get_ios_vcard_batch(
                    cursor, filter_empty, filter_date, filter_chat
                )
        
        return []
    
    @staticmethod
    def _get_android_vcard_batch(cursor: sqlite3.Cursor, filter_empty, filter_date, filter_chat):
        """Get Android vCard data in batch."""
        from .android_handler import get_chat_condition, get_cond_for_empty
        
        chat_filter_include = get_chat_condition(
            filter_chat[0], True, ["key_remote_jid", "jid_group.raw_string"], "jid", "android"
        )
        chat_filter_exclude = get_chat_condition(
            filter_chat[1], False, ["key_remote_jid", "jid_group.raw_string"], "jid", "android"
        )
        date_filter = f"AND message.timestamp {filter_date}" if filter_date else ""
        empty_filter = get_cond_for_empty(filter_empty, "key_remote_jid", "broadcast")
        
        query = f"""
            SELECT 
                message_vcard.message_row_id,
                jid.raw_string as key_remote_jid,
                message_vcard.vcard,
                message.text_data as media_name,
                -- Include message data to avoid N+1
                message.timestamp,
                message.key_from_me
            FROM message_vcard
                INNER JOIN message ON message_vcard.message_row_id = message._id
                LEFT JOIN chat ON chat._id = message.chat_row_id
                INNER JOIN jid ON jid._id = chat.jid_row_id
                LEFT JOIN jid jid_group ON jid_group._id = message.sender_jid_row_id
            WHERE 1=1
                {empty_filter}
                {date_filter}
                {chat_filter_include}
                {chat_filter_exclude}
            ORDER BY message.chat_row_id ASC
        """
        
        cursor.execute(query)
        return cursor.fetchall()
    
    @staticmethod
    def _get_ios_vcard_batch(cursor: sqlite3.Cursor, filter_empty, filter_date, filter_chat):
        """Get iOS vCard data in batch.""" 
        from .ios_handler import get_chat_condition
        
        chat_filter_include = get_chat_condition(
            filter_chat[0], True, ["ZWACHATSESSION.ZCONTACTJID"], "ios"
        )
        chat_filter_exclude = get_chat_condition(
            filter_chat[1], False, ["ZWACHATSESSION.ZCONTACTJID"], "ios"
        )
        date_filter = f"AND ZWAMESSAGE.ZMESSAGEDATE {filter_date}" if filter_date else ""
        
        query = f"""
            SELECT 
                ZWAMESSAGE.Z_PK as message_row_id,
                ZWACHATSESSION.ZCONTACTJID as key_remote_jid,
                ZWAMESSAGE.ZTEXT as vcard,
                ZWAMESSAGE.ZTEXT as media_name,
                ZWAMESSAGE.ZMESSAGEDATE as timestamp,
                ZWAMESSAGE.ZISFROMME as key_from_me
            FROM ZWAMESSAGE
                INNER JOIN ZWACHATSESSION ON ZWAMESSAGE.ZCHATSESSION = ZWACHATSESSION.Z_PK
            WHERE ZWAMESSAGE.ZTEXT LIKE 'BEGIN:VCARD%'
                {chat_filter_include}
                {chat_filter_exclude}
                {date_filter}
            ORDER BY ZWAMESSAGE.ZCHATSESSION ASC
        """
        
        cursor.execute(query)
        return cursor.fetchall()


# Global cache instance
_chat_cache: Optional[ChatDataCache] = None


def get_chat_cache() -> ChatDataCache:
    """Get the global chat data cache."""
    global _chat_cache
    if _chat_cache is None:
        _chat_cache = ChatDataCache()
    return _chat_cache


def clear_chat_cache() -> None:
    """Clear the global chat data cache."""
    global _chat_cache
    if _chat_cache:
        _chat_cache.clear()