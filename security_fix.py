"""
Security fixes for SQL injection vulnerabilities in utility.py

This file contains the corrected version of the get_chat_condition function
that uses parameterized queries to prevent SQL injection attacks.
"""

import re
from typing import Optional, List


def get_chat_condition_secure(filter: Optional[List[str]], include: bool, columns: List[str], jid: Optional[str] = None, platform: Optional[str] = None) -> tuple[str, list]:
    """Generates a SQL condition for filtering chats based on inclusion or exclusion criteria.
    
    SECURITY FIX: This version uses parameterized queries to prevent SQL injection.

    Args:
        filter: A list of phone numbers to include or exclude.
        include: True to include chats that match the filter, False to exclude them.
        columns: A list of column names to check against the filter.
        jid: The JID column name (used for group identification).
        platform: The platform ("android" or "ios") for platform-specific JID queries.

    Returns:
        A tuple of (SQL condition string, list of parameters).

    Raises:
        ValueError: If the column count is invalid or an unsupported platform is provided.
    """
    if filter is not None:
        # Validate column names to prevent SQL injection
        for column in columns:
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$', column):
                raise ValueError(f"Invalid column name: {column}")
        
        # Validate jid column name
        if jid is not None and not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$', jid):
            raise ValueError(f"Invalid JID column name: {jid}")
        
        conditions = []
        parameters = []
        
        if len(columns) < 2 and jid is not None:
            raise ValueError("There must be at least two elements in argument columns if jid is not None")
        if jid is not None:
            if platform == "android":
                is_group = f"{jid}.type == 1"
            elif platform == "ios":
                is_group = f"{jid} IS NOT NULL"
            else:
                raise ValueError("Only android and ios are supported for argument platform if jid is not None")
        
        for index, chat in enumerate(filter):
            # Sanitize chat filter input
            if not isinstance(chat, str):
                raise ValueError("Chat filter must be a string")
            
            # Validate chat input to prevent SQL injection
            if len(chat) > 100:  # Reasonable limit for phone numbers/usernames
                raise ValueError("Chat identifier too long")
            
            if include:
                conditions.append(f"{' OR' if index > 0 else ''} {columns[0]} LIKE ?")
                parameters.append(f"%{chat}%")
                if len(columns) > 1:
                    conditions.append(f" OR ({columns[1]} LIKE ? AND {is_group})")
                    parameters.append(f"%{chat}%")
            else:
                conditions.append(f"{' AND' if index > 0 else ''} {columns[0]} NOT LIKE ?")
                parameters.append(f"%{chat}%")
                if len(columns) > 1:
                    conditions.append(f" AND ({columns[1]} NOT LIKE ? AND {is_group})")
                    parameters.append(f"%{chat}%")
        
        return f"AND ({' '.join(conditions)})", parameters
    else:
        return "", []


def get_cond_for_empty_secure(enable: bool, jid_field: str, broadcast_field: str) -> str:
    """Generates a SQL condition for filtering empty chats.
    
    SECURITY FIX: This version validates field names to prevent SQL injection.

    Args:
        enable: True to include non-empty chats, False to include empty chats.
        jid_field: The name of the JID field in the SQL query.
        broadcast_field: The column name of the broadcast field in the SQL query.

    Returns:
        A SQL condition string.
    """
    # Validate field names to prevent SQL injection
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$', jid_field):
        raise ValueError(f"Invalid JID field name: {jid_field}")
    
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$', broadcast_field):
        raise ValueError(f"Invalid broadcast field name: {broadcast_field}")
    
    return f"AND (chat.hidden=0 OR {jid_field}='status@broadcast' OR {broadcast_field}>0)" if enable else ""