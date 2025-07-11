#!/usr/bin/python3

import logging
import os
import shutil
import sys
from glob import glob
from mimetypes import MimeTypes
from pathlib import Path

from markupsafe import escape as htmle
from rich.progress import track

from Whatsapp_Chat_Exporter.data_model import ChatStore, Message
from Whatsapp_Chat_Exporter.utility import (
    APPLE_TIME,
    CURRENT_TZ_OFFSET,
    Device,
    bytes_to_readable,
    convert_time_unit,
    get_chat_condition,
    slugify,
    is_group_jid,
)

logger = logging.getLogger(__name__)


def _check_table_exists(db, table_name):
    """Check if a table exists in the database."""
    cursor = db.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    )
    return cursor.fetchone() is not None


def _get_available_tables(db):
    """Get a list of all available tables in the database."""
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return [row[0] for row in cursor.fetchall()]


def _get_table_columns(db, table_name):
    """Get a list of columns for a specific table."""
    cursor = db.cursor()
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cursor.fetchall()]  # row[1] is the column name
    except Exception as e:
        logger.warning(f"Could not get columns for table {table_name}: {e}")
        return []


def _check_column_exists(db, table_name, column_name):
    """Check if a column exists in a table."""
    columns = _get_table_columns(db, table_name)
    return column_name in columns


def contacts(db, data):
    """Process WhatsApp contacts with status information."""

    # Handle both string path and connection object
    if isinstance(db, str):
        import sqlite3

        with sqlite3.connect(db) as db_conn:
            db_conn.row_factory = sqlite3.Row
            return contacts(db_conn, data)

    # Check if contacts table exists
    has_addressbook_contact = _check_table_exists(db, "ZWAADDRESSBOOKCONTACT")

    logger.info(f"Contacts table - ZWAADDRESSBOOKCONTACT: {has_addressbook_contact}")

    # If no contacts table, skip processing
    if not has_addressbook_contact:
        logger.info(
            "No ZWAADDRESSBOOKCONTACT table found, skipping contacts processing"
        )
        return

    c = db.cursor()
    c.execute(
        """SELECT count() FROM ZWAADDRESSBOOKCONTACT WHERE ZABOUTTEXT IS NOT NULL"""
    )
    total_row_number = c.fetchone()[0]
    logger.info("Pre-processing contacts...(%s)", total_row_number)

    if total_row_number == 0:
        logger.info("No contacts with status found")
        return

    c.execute(
        """SELECT ZWHATSAPPID, ZABOUTTEXT FROM ZWAADDRESSBOOKCONTACT WHERE ZABOUTTEXT IS NOT NULL"""
    )
    content = c.fetchone()
    while content is not None:
        zwhatsapp_id = content["ZWHATSAPPID"]
        if zwhatsapp_id and not zwhatsapp_id.endswith("@s.whatsapp.net"):
            zwhatsapp_id += "@s.whatsapp.net"

        if zwhatsapp_id:  # Only add if valid ID
            current_chat = ChatStore(Device.IOS, is_group=is_group_jid(zwhatsapp_id))
            current_chat.status = content["ZABOUTTEXT"]
            data.add_chat(zwhatsapp_id, current_chat)
        content = c.fetchone()


def process_contact_avatars(current_chat, media_folder, contact_id):
    """Process and assign avatar images for a contact."""
    path = f'{media_folder}/Media/Profile/{contact_id.split("@")[0]}'
    avatars = glob(f"{path}*")

    if 0 < len(avatars) <= 1:
        current_chat.their_avatar = avatars[0]
    else:
        for avatar in avatars:
            if avatar.endswith(".thumb") and current_chat.their_avatar_thumb is None:
                current_chat.their_avatar_thumb = avatar
            elif avatar.endswith(".jpg") and current_chat.their_avatar is None:
                current_chat.their_avatar = avatar


def get_contact_name(content):
    """Determine the appropriate contact name based on push name and partner name."""
    try:
        partner_name = content["ZPARTNERNAME"] if "ZPARTNERNAME" in content else None
        push_name = content["ZPUSHNAME"] if "ZPUSHNAME" in content else None
    except (KeyError, TypeError):
        return "Unknown Contact"

    # Handle None values safely
    if not partner_name:
        return push_name or "Unknown Contact"

    if not push_name:
        return partner_name

    # Check if partner name looks like a phone number
    is_phone = partner_name.replace("+", "").replace(" ", "").replace("-", "").isdigit()

    if push_name and not is_phone:
        return partner_name
    else:
        return push_name


def messages(
    db, data, media_folder, timezone_offset, filter_date, filter_chat, filter_empty
):
    """Process WhatsApp messages and contacts from the database."""
    c = db.cursor()
    cursor2 = db.cursor()

    # Check what tables are available
    available_tables = _get_available_tables(db)
    logger.info(f"Available tables: {available_tables}")

    has_chat_session = _check_table_exists(db, "ZWACHATSESSION")
    has_profile_pushname = _check_table_exists(db, "ZWAPROFILEPUSHNAME")
    has_group_member = _check_table_exists(db, "ZWAGROUPMEMBER")

    logger.info(
        f"Table availability - ZWACHATSESSION: {has_chat_session}, ZWAPROFILEPUSHNAME: {has_profile_pushname}, ZWAGROUPMEMBER: {has_group_member}"
    )

    # Build the chat filter conditions
    chat_filter_include = get_chat_condition(
        filter_chat[0],
        True,
        (
            ["ZWACHATSESSION.ZCONTACTJID", "ZMEMBERJID"]
            if has_chat_session
            else ["ZWAMESSAGE.ZCONTACTJID"]
        ),
        "ZGROUPINFO",
        "ios",
    )
    chat_filter_exclude = get_chat_condition(
        filter_chat[1],
        False,
        (
            ["ZWACHATSESSION.ZCONTACTJID", "ZMEMBERJID"]
            if has_chat_session
            else ["ZWAMESSAGE.ZCONTACTJID"]
        ),
        "ZGROUPINFO",
        "ios",
    )
    date_filter = f"AND ZMESSAGEDATE {filter_date}" if filter_date is not None else ""

    # Process contacts first - use simplified query if tables missing
    if has_chat_session:
        # Full query with all tables
        contact_query = f"""
            SELECT count() 
            FROM (SELECT DISTINCT ZCONTACTJID,
                ZPARTNERNAME,
                {"ZWAPROFILEPUSHNAME.ZPUSHNAME" if has_profile_pushname else "NULL as ZPUSHNAME"}
            FROM ZWACHATSESSION
                INNER JOIN ZWAMESSAGE
                    ON ZWAMESSAGE.ZCHATSESSION = ZWACHATSESSION.Z_PK
                {"LEFT JOIN ZWAPROFILEPUSHNAME ON ZWACHATSESSION.ZCONTACTJID = ZWAPROFILEPUSHNAME.ZJID" if has_profile_pushname else ""}
                {"LEFT JOIN ZWAGROUPMEMBER ON ZWAMESSAGE.ZGROUPMEMBER = ZWAGROUPMEMBER.Z_PK" if has_group_member else ""}
            WHERE 1=1
                {chat_filter_include}
                {chat_filter_exclude}
            GROUP BY ZCONTACTJID)
        """

        contacts_query = f"""
            SELECT DISTINCT ZCONTACTJID,
                ZPARTNERNAME,
                {"ZWAPROFILEPUSHNAME.ZPUSHNAME" if has_profile_pushname else "NULL as ZPUSHNAME"}
            FROM ZWACHATSESSION
                INNER JOIN ZWAMESSAGE
                    ON ZWAMESSAGE.ZCHATSESSION = ZWACHATSESSION.Z_PK
                {"LEFT JOIN ZWAPROFILEPUSHNAME ON ZWACHATSESSION.ZCONTACTJID = ZWAPROFILEPUSHNAME.ZJID" if has_profile_pushname else ""}
                {"LEFT JOIN ZWAGROUPMEMBER ON ZWAMESSAGE.ZGROUPMEMBER = ZWAGROUPMEMBER.Z_PK" if has_group_member else ""}
            WHERE 1=1
                {chat_filter_include}
                {chat_filter_exclude}
            GROUP BY ZCONTACTJID
        """
    else:
        # Simplified query using only ZWAMESSAGE table
        contact_query = f"""
            SELECT count() 
            FROM (SELECT DISTINCT ZCONTACTJID,
                ZPARTNERNAME,
                ZPUSHNAME
            FROM ZWAMESSAGE
            WHERE 1=1
                {chat_filter_include}
                {chat_filter_exclude}
            GROUP BY ZCONTACTJID)
        """

        contacts_query = f"""
            SELECT DISTINCT ZCONTACTJID,
                ZPARTNERNAME,
                ZPUSHNAME
            FROM ZWAMESSAGE
            WHERE 1=1
                {chat_filter_include}
                {chat_filter_exclude}
            GROUP BY ZCONTACTJID
        """

    c.execute(contact_query)
    total_row_number = c.fetchone()[0]
    logger.info("Processing contacts...(%s)", total_row_number)

    c.execute(contacts_query)

    # Process each contact
    content = c.fetchone()
    while content is not None:
        contact_name = get_contact_name(content)
        contact_id = content["ZCONTACTJID"]

        # Add or update chat
        if contact_id not in data:
            current_chat = data.add_chat(
                contact_id,
                ChatStore(
                    Device.IOS,
                    contact_name,
                    media_folder,
                    is_group=is_group_jid(contact_id),
                ),
            )
        else:
            current_chat = data.get_chat(contact_id)
            current_chat.name = contact_name
            current_chat.slug = slugify(contact_name, True)
            current_chat.my_avatar = os.path.join(
                media_folder, "Media/Profile/Photo.jpg"
            )
        # Process avatar images
        process_contact_avatars(current_chat, media_folder, contact_id)
        content = c.fetchone()

    # Get message count - use simplified query if tables missing
    if has_chat_session:
        message_count_query = f"""
            SELECT count()
            FROM ZWAMESSAGE
                INNER JOIN ZWACHATSESSION
                    ON ZWAMESSAGE.ZCHATSESSION = ZWACHATSESSION.Z_PK
                {"LEFT JOIN ZWAGROUPMEMBER ON ZWAMESSAGE.ZGROUPMEMBER = ZWAGROUPMEMBER.Z_PK" if has_group_member else ""}
            WHERE 1=1
                {date_filter}
                {chat_filter_include}
                {chat_filter_exclude}
        """
    else:
        message_count_query = f"""
            SELECT count()
            FROM ZWAMESSAGE
            WHERE 1=1
                {date_filter}
                {chat_filter_include}
                {chat_filter_exclude}
        """

    c.execute(message_count_query)
    total_row_number = c.fetchone()[0]

    # Fetch messages - use simplified query if tables missing
    if has_chat_session:
        messages_query = f"""
            SELECT ZCONTACTJID,
                ZWAMESSAGE.Z_PK,
                ZISFROMME,
                ZMESSAGEDATE,
                ZTEXT,
                ZMESSAGETYPE,
                {"ZWAGROUPMEMBER.ZMEMBERJID" if has_group_member else "NULL as ZMEMBERJID"},
                ZMETADATA,
                ZSTANZAID,
                ZGROUPINFO,
                ZSENTDATE
            FROM ZWAMESSAGE
                {"LEFT JOIN ZWAGROUPMEMBER ON ZWAMESSAGE.ZGROUPMEMBER = ZWAGROUPMEMBER.Z_PK" if has_group_member else ""}
                LEFT JOIN ZWAMEDIAITEM
                    ON ZWAMESSAGE.Z_PK = ZWAMEDIAITEM.ZMESSAGE
                INNER JOIN ZWACHATSESSION
                    ON ZWAMESSAGE.ZCHATSESSION = ZWACHATSESSION.Z_PK
            WHERE 1=1   
                {date_filter}
            {chat_filter_include}
            {chat_filter_exclude}
        ORDER BY ZMESSAGEDATE ASC
        """
    else:
        # Simplified query using only ZWAMESSAGE table
        messages_query = f"""
            SELECT ZCONTACTJID,
                Z_PK,
                ZISFROMME,
                ZMESSAGEDATE,
                ZTEXT,
                ZMESSAGETYPE,
                NULL as ZMEMBERJID,
                NULL as ZMETADATA,
                NULL as ZSTANZAID,
                NULL as ZGROUPINFO,
                NULL as ZSENTDATE
            FROM ZWAMESSAGE
            WHERE 1=1   
                {date_filter}
                {chat_filter_include}
                {chat_filter_exclude}
            ORDER BY ZMESSAGEDATE ASC
        """

    c.execute(messages_query)

    # Process each message
    content = c.fetchone()
    for _ in track(range(total_row_number), description="Processing messages"):
        if content is None:
            break
        contact_id = content["ZCONTACTJID"]
        message_pk = content["Z_PK"]
        is_group_message = (
            content["ZGROUPINFO"] is not None
            if content["ZGROUPINFO"] is not None
            else False
        )

        # Ensure chat exists
        if contact_id not in data:
            current_chat = data.add_chat(
                contact_id,
                ChatStore(Device.IOS, is_group=is_group_jid(contact_id)),
            )
            process_contact_avatars(current_chat, media_folder, contact_id)
        else:
            current_chat = data.get_chat(contact_id)

        # Create message object
        ts = APPLE_TIME + content["ZMESSAGEDATE"]
        # Safe conversion of ZSTANZAID to key_id
        key_id = 0
        if content["ZSTANZAID"]:
            try:
                # Try to extract first 17 characters and convert to hex
                stanza_id = str(content["ZSTANZAID"])[:17]
                # Remove any non-hex characters
                hex_only = "".join(
                    c for c in stanza_id if c in "0123456789abcdefABCDEF"
                )
                if hex_only:
                    key_id = int(hex_only[:16], 16)  # Use max 16 chars for safety
                else:
                    key_id = hash(str(content["ZSTANZAID"]))  # Fallback to hash
            except (ValueError, TypeError):
                key_id = (
                    hash(str(content["ZSTANZAID"]))
                    if content["ZSTANZAID"]
                    else message_pk
                )

        message = Message(
            from_me=content["ZISFROMME"],
            timestamp=ts,
            time=ts,
            key_id=key_id,
            timezone_offset=int(
                timezone_offset if timezone_offset else CURRENT_TZ_OFFSET
            ),
            message_type=content["ZMESSAGETYPE"] if content["ZMESSAGETYPE"] else 0,
            received_timestamp=int(
                APPLE_TIME + content["ZSENTDATE"] if content["ZSENTDATE"] else ts
            ),
            # iOS database does not store read timestamps
            read_timestamp=int(ts),
        )

        # Process message data
        invalid = process_message_data(
            message, content, is_group_message, data, cursor2
        )

        # Add valid messages to chat
        if not invalid:
            current_chat.add_message(message_pk, message)

        content = c.fetchone()


def process_message_data(message, content, is_group_message, data, cursor2):
    """Process and set message data from content row."""
    # Handle group sender info
    if is_group_message and content["ZISFROMME"] == 0:
        name = None
        if content["ZMEMBERJID"] is not None:
            if content["ZMEMBERJID"] in data:
                name = data.get_chat(content["ZMEMBERJID"]).name
            if "@" in content["ZMEMBERJID"]:
                fallback = content["ZMEMBERJID"].split("@")[0]
            else:
                fallback = None
        else:
            fallback = None
        message.sender = name or fallback
    else:
        message.sender = None

    # Handle metadata messages
    if content["ZMESSAGETYPE"] == 6:
        return process_metadata_message(message, content, is_group_message)

    # Handle quoted replies - currently disabled
    if False and (
        content["ZMETADATA"] is not None
        and content["ZMETADATA"].startswith(b"\x2a\x14")
    ):
        quoted = content["ZMETADATA"][2:19]
        message.reply = quoted.decode()
        cursor2.execute(
            f"""SELECT ZTEXT
                            FROM ZWAMESSAGE
                            WHERE ZSTANZAID LIKE '{message.reply}%'"""
        )
        quoted_content = cursor2.fetchone()
        if quoted_content and "ZTEXT" in quoted_content:
            message.quoted_data = quoted_content["ZTEXT"]
        else:
            message.quoted_data = None

    # Handle stickers
    if content["ZMESSAGETYPE"] == 15:
        message.sticker = True

    # Process message text
    process_message_text(message, content)

    return False  # Message is valid


def process_metadata_message(message, content, is_group_message):
    """Process metadata messages (action_type 6)."""
    if is_group_message:
        # Group
        if content["ZTEXT"] is not None:
            # Changed name
            try:
                int(content["ZTEXT"])
            except ValueError:
                msg = f"The group name changed to {content['ZTEXT']}"
                message.data = msg
                message.meta = True
                return False  # Valid message
            else:
                return True  # Invalid message
        else:
            message.data = None
            return False
    else:
        message.data = None
        return False


def process_message_text(message, content):
    """Process and format message text content."""
    if content["ZISFROMME"] == 1:
        if content["ZMESSAGETYPE"] == 14:
            msg = "Message deleted"
            message.meta = True
        else:
            msg = content["ZTEXT"]
            if msg is not None:
                msg = msg.replace("\r\n", "<br>").replace("\n", "<br>")
    else:
        if content["ZMESSAGETYPE"] == 14:
            msg = "Message deleted"
            message.meta = True
        else:
            msg = content["ZTEXT"]
            if msg is not None:
                msg = msg.replace("\r\n", "<br>").replace("\n", "<br>")

    message.data = msg


def media(db, data, media_folder, filter_date, filter_chat, separate_media=False):
    """Process media files from WhatsApp messages."""

    # Handle both string path and connection object
    if isinstance(db, str):
        import sqlite3

        with sqlite3.connect(db) as db_conn:
            db_conn.row_factory = sqlite3.Row
            return media(
                db_conn, data, media_folder, filter_date, filter_chat, separate_media
            )

    # Check what tables are available
    has_media_item = _check_table_exists(db, "ZWAMEDIAITEM")
    has_chat_session = _check_table_exists(db, "ZWACHATSESSION")
    has_group_member = _check_table_exists(db, "ZWAGROUPMEMBER")

    logger.info(
        f"Media tables - ZWAMEDIAITEM: {has_media_item}, ZWACHATSESSION: {has_chat_session}, ZWAGROUPMEMBER: {has_group_member}"
    )

    # If no media table, skip processing
    if not has_media_item:
        logger.info("No ZWAMEDIAITEM table found, skipping media processing")
        return

    c = db.cursor()

    # Build filter conditions
    if has_chat_session:
        chat_filter_include = get_chat_condition(
            filter_chat[0],
            True,
            ["ZWACHATSESSION.ZCONTACTJID", "ZMEMBERJID"],
            "ZGROUPINFO",
            "ios",
        )
        chat_filter_exclude = get_chat_condition(
            filter_chat[1],
            False,
            ["ZWACHATSESSION.ZCONTACTJID", "ZMEMBERJID"],
            "ZGROUPINFO",
            "ios",
        )
    else:
        chat_filter_include = get_chat_condition(
            filter_chat[0],
            True,
            ["ZWAMESSAGE.ZCONTACTJID"],
            "ZGROUPINFO",
            "ios",
        )
        chat_filter_exclude = get_chat_condition(
            filter_chat[1],
            False,
            ["ZWAMESSAGE.ZCONTACTJID"],
            "ZGROUPINFO",
            "ios",
        )

    date_filter = f"AND ZMESSAGEDATE {filter_date}" if filter_date is not None else ""

    # Get media count - use simplified query if tables missing
    if has_chat_session:
        media_count_query = f"""
            SELECT count()
            FROM ZWAMEDIAITEM
                INNER JOIN ZWAMESSAGE
                    ON ZWAMEDIAITEM.ZMESSAGE = ZWAMESSAGE.Z_PK
                INNER JOIN ZWACHATSESSION
                    ON ZWAMESSAGE.ZCHATSESSION = ZWACHATSESSION.Z_PK
                {"LEFT JOIN ZWAGROUPMEMBER ON ZWAMESSAGE.ZGROUPMEMBER = ZWAGROUPMEMBER.Z_PK" if has_group_member else ""}
            WHERE 1=1
                {date_filter}
                {chat_filter_include}
                {chat_filter_exclude}
        """
    else:
        media_count_query = f"""
            SELECT count()
            FROM ZWAMEDIAITEM
                INNER JOIN ZWAMESSAGE
                    ON ZWAMEDIAITEM.ZMESSAGE = ZWAMESSAGE.Z_PK
            WHERE 1=1
                {date_filter}
                {chat_filter_include}
                {chat_filter_exclude}
        """

    c.execute(media_count_query)
    total_row_number = c.fetchone()[0]

    if total_row_number == 0:
        logger.info("No media items found")
        return

    # Fetch media items - use simplified query if tables missing
    if has_chat_session:
        media_query = f"""
            SELECT ZCONTACTJID,
                ZMESSAGE,
                ZMEDIALOCALPATH,
                ZMEDIAURL,
                ZVCARDSTRING,
                ZMEDIAKEY,
                ZTITLE
            FROM ZWAMEDIAITEM
                INNER JOIN ZWAMESSAGE
                    ON ZWAMEDIAITEM.ZMESSAGE = ZWAMESSAGE.Z_PK
                INNER JOIN ZWACHATSESSION
                    ON ZWAMESSAGE.ZCHATSESSION = ZWACHATSESSION.Z_PK
                {"LEFT JOIN ZWAGROUPMEMBER ON ZWAMESSAGE.ZGROUPMEMBER = ZWAGROUPMEMBER.Z_PK" if has_group_member else ""}
            WHERE ZMEDIALOCALPATH IS NOT NULL
                {date_filter}
                {chat_filter_include}
                {chat_filter_exclude}
            ORDER BY ZCONTACTJID ASC
        """
    else:
        media_query = f"""
            SELECT ZWAMESSAGE.ZCONTACTJID,
                ZWAMEDIAITEM.ZMESSAGE,
                ZWAMEDIAITEM.ZMEDIALOCALPATH,
                ZWAMEDIAITEM.ZMEDIAURL,
                ZWAMEDIAITEM.ZVCARDSTRING,
                ZWAMEDIAITEM.ZMEDIAKEY,
                ZWAMEDIAITEM.ZTITLE
            FROM ZWAMEDIAITEM
                INNER JOIN ZWAMESSAGE
                    ON ZWAMEDIAITEM.ZMESSAGE = ZWAMESSAGE.Z_PK
            WHERE ZWAMEDIAITEM.ZMEDIALOCALPATH IS NOT NULL
                {date_filter}
                {chat_filter_include}
                {chat_filter_exclude}
            ORDER BY ZWAMESSAGE.ZCONTACTJID ASC
        """

    c.execute(media_query)

    # Process each media item
    mime = MimeTypes()
    content = c.fetchone()
    for _ in track(range(total_row_number), description="Processing media"):
        if content is None:
            break
        process_media_item(content, data, media_folder, mime, separate_media)
        content = c.fetchone()


def process_media_item(
    content,
    data,
    media_folder,
    mime,
    separate_media,
):
    """Process a single media item."""
    # Validate content and required fields
    try:
        contact_jid = content["ZCONTACTJID"] if "ZCONTACTJID" in content else None
        message_id = content["ZMESSAGE"] if "ZMESSAGE" in content else None
        media_path = (
            content["ZMEDIALOCALPATH"] if "ZMEDIALOCALPATH" in content else None
        )
    except (KeyError, TypeError):
        logger.warning("Invalid content structure in media processing")
        return

    if not contact_jid or not message_id:
        logger.debug("Missing required fields in media content")
        return

    if not media_path:
        logger.debug("No local media path found")
        return

    base_dir = os.path.abspath(os.path.join(media_folder, "Message"))
    file_path = os.path.normpath(os.path.join(base_dir, media_path))

    # Validate chat and message exist
    current_chat = data.get_chat(contact_jid)
    if not current_chat:
        logger.debug(f"Chat not found for contact: {contact_jid}")
        return

    message = current_chat.get_message(message_id)
    if not message:
        logger.debug(f"Message not found: {message_id} in chat {contact_jid}")
        return

    message.media = True

    if current_chat.media_base == "":
        current_chat.media_base = media_folder + "/"

    if not file_path.startswith(base_dir + os.sep):
        message.data = "The media is missing"
        message.mime = "media"
        message.meta = True
        return

    if os.path.isfile(file_path):
        message.data = os.path.relpath(file_path, Path(file_path).anchor)

        # Set MIME type
        if content["ZVCARDSTRING"] is None:
            guess = mime.guess_type(file_path)[0]
            message.mime = guess if guess is not None else "application/octet-stream"
        else:
            message.mime = content["ZVCARDSTRING"]

        # Handle separate media option
        if separate_media:
            if not current_chat.slug:
                current_chat.slug = slugify(
                    current_chat.name
                    or message.sender
                    or content["ZCONTACTJID"].split("@")[0],
                    True,
                )
            chat_display_name = current_chat.slug
            current_filename = os.path.basename(file_path)
            new_folder = os.path.join(media_folder, "separated", chat_display_name)
            Path(new_folder).mkdir(parents=True, exist_ok=True)
            new_path = os.path.join(new_folder, current_filename)
            shutil.copy2(file_path, new_path)
            message.data = os.path.relpath(new_path, Path(new_path).anchor)
    else:
        # Handle missing media
        message.data = "The media is missing"
        message.mime = "media"
        message.meta = True

    # Add caption if available
    if content["ZTITLE"] is not None:
        message.caption = content["ZTITLE"]


def vcard(db, data, media_folder, filter_date, filter_chat):
    """Process vCard contacts from WhatsApp messages."""

    # Handle both string path and connection object
    if isinstance(db, str):
        import sqlite3

        with sqlite3.connect(db) as db_conn:
            db_conn.row_factory = sqlite3.Row
            return vcard(db_conn, data, media_folder, filter_date, filter_chat)

    # Check what tables are available
    has_vcard_mention = _check_table_exists(db, "ZWAVCARDMENTION")
    has_media_item = _check_table_exists(db, "ZWAMEDIAITEM")
    has_chat_session = _check_table_exists(db, "ZWACHATSESSION")
    has_group_member = _check_table_exists(db, "ZWAGROUPMEMBER")

    logger.info(
        f"vCard tables - ZWAVCARDMENTION: {has_vcard_mention}, ZWAMEDIAITEM: {has_media_item}, ZWACHATSESSION: {has_chat_session}, ZWAGROUPMEMBER: {has_group_member}"
    )

    # If no vCard tables, skip processing
    if not has_vcard_mention or not has_media_item:
        logger.info(
            "No ZWAVCARDMENTION or ZWAMEDIAITEM table found, skipping vCard processing"
        )
        return

    # Check columns in vCard table to understand structure
    vcard_columns = _get_table_columns(db, "ZWAVCARDMENTION")
    logger.info(f"ZWAVCARDMENTION columns: {vcard_columns}")

    # Determine which columns are available for vCard processing
    has_vcard_name = "ZVCARDNAME" in vcard_columns
    has_vcard_string = "ZVCARDSTRING" in vcard_columns

    # Check if ZWAMEDIAITEM has vCard data
    media_columns = _get_table_columns(db, "ZWAMEDIAITEM")
    has_media_vcard_string = "ZVCARDSTRING" in media_columns

    # If neither table has the vCard data we need, skip processing
    if not (has_vcard_string or has_media_vcard_string):
        logger.info(
            "No vCard string columns found in any table, skipping vCard processing"
        )
        return

    c = db.cursor()

    # Build filter conditions - use simplified conditions if tables missing
    if has_chat_session:
        chat_filter_include = get_chat_condition(
            filter_chat[0],
            True,
            ["ZWACHATSESSION.ZCONTACTJID", "ZMEMBERJID"],
            "ZGROUPINFO",
            "ios",
        )
        chat_filter_exclude = get_chat_condition(
            filter_chat[1],
            False,
            ["ZWACHATSESSION.ZCONTACTJID", "ZMEMBERJID"],
            "ZGROUPINFO",
            "ios",
        )
    else:
        chat_filter_include = get_chat_condition(
            filter_chat[0], True, ["ZWAMESSAGE.ZCONTACTJID"], "ZGROUPINFO", "ios"
        )
        chat_filter_exclude = get_chat_condition(
            filter_chat[1], False, ["ZWAMESSAGE.ZCONTACTJID"], "ZGROUPINFO", "ios"
        )

    date_filter = (
        f"AND ZWAMESSAGE.ZMESSAGEDATE {filter_date}" if filter_date is not None else ""
    )

    # Build dynamic column selection based on available columns
    vcard_name_col = (
        "ZWAVCARDMENTION.ZVCARDNAME"
        if has_vcard_name
        else "'Unknown vCard' as ZVCARDNAME"
    )

    # Prefer vCard string from mention table, fallback to media table
    if has_vcard_string:
        vcard_string_col = "ZWAVCARDMENTION.ZVCARDSTRING"
    elif has_media_vcard_string:
        vcard_string_col = "ZWAMEDIAITEM.ZVCARDSTRING"
    else:
        vcard_string_col = "NULL as ZVCARDSTRING"

    # Fetch vCard mentions - use simplified query if tables missing
    if has_chat_session:
        vcard_query = f"""
            SELECT DISTINCT ZWAVCARDMENTION.ZMEDIAITEM,
                ZWAMEDIAITEM.ZMESSAGE,
                ZWACHATSESSION.ZCONTACTJID,
                {vcard_name_col},
                {vcard_string_col}
            FROM ZWAVCARDMENTION
                INNER JOIN ZWAMEDIAITEM
                    ON ZWAVCARDMENTION.ZMEDIAITEM = ZWAMEDIAITEM.Z_PK
                INNER JOIN ZWAMESSAGE
                    ON ZWAMEDIAITEM.ZMESSAGE = ZWAMESSAGE.Z_PK
                INNER JOIN ZWACHATSESSION
                    ON ZWAMESSAGE.ZCHATSESSION = ZWACHATSESSION.Z_PK
                {"LEFT JOIN ZWAGROUPMEMBER ON ZWAMESSAGE.ZGROUPMEMBER = ZWAGROUPMEMBER.Z_PK" if has_group_member else ""}
            WHERE 1=1
                {date_filter}
                {chat_filter_include}
                {chat_filter_exclude}
        """
    else:
        vcard_query = f"""
            SELECT DISTINCT ZWAVCARDMENTION.ZMEDIAITEM,
                ZWAMEDIAITEM.ZMESSAGE,
                ZWAMESSAGE.ZCONTACTJID,
                {vcard_name_col},
                {vcard_string_col}
            FROM ZWAVCARDMENTION
                INNER JOIN ZWAMEDIAITEM
                    ON ZWAVCARDMENTION.ZMEDIAITEM = ZWAMEDIAITEM.Z_PK
                INNER JOIN ZWAMESSAGE
                    ON ZWAMEDIAITEM.ZMESSAGE = ZWAMESSAGE.Z_PK
            WHERE 1=1
                {date_filter}
                {chat_filter_include}
                {chat_filter_exclude}
        """

    try:
        c.execute(vcard_query)
        contents = c.fetchall()
    except Exception as e:
        logger.warning(f"Failed to execute vCard query: {e}")

        # Try a simpler fallback query using only ZWAMEDIAITEM
        if has_media_vcard_string:
            logger.info("Attempting fallback vCard query using ZWAMEDIAITEM only")
            try:
                if has_chat_session:
                    fallback_query = f"""
                        SELECT DISTINCT ZWAMEDIAITEM.Z_PK as ZMEDIAITEM,
                            ZWAMEDIAITEM.ZMESSAGE,
                            ZWACHATSESSION.ZCONTACTJID,
                            'vCard' as ZVCARDNAME,
                            ZWAMEDIAITEM.ZVCARDSTRING
                        FROM ZWAMEDIAITEM
                            INNER JOIN ZWAMESSAGE
                                ON ZWAMEDIAITEM.ZMESSAGE = ZWAMESSAGE.Z_PK
                            INNER JOIN ZWACHATSESSION
                                ON ZWAMESSAGE.ZCHATSESSION = ZWACHATSESSION.Z_PK
                        WHERE ZWAMEDIAITEM.ZVCARDSTRING IS NOT NULL
                            {date_filter}
                            {chat_filter_include}
                            {chat_filter_exclude}
                    """
                else:
                    fallback_query = f"""
                        SELECT DISTINCT ZWAMEDIAITEM.Z_PK as ZMEDIAITEM,
                            ZWAMEDIAITEM.ZMESSAGE,
                            ZWAMESSAGE.ZCONTACTJID,
                            'vCard' as ZVCARDNAME,
                            ZWAMEDIAITEM.ZVCARDSTRING
                        FROM ZWAMEDIAITEM
                            INNER JOIN ZWAMESSAGE
                                ON ZWAMEDIAITEM.ZMESSAGE = ZWAMESSAGE.Z_PK
                        WHERE ZWAMEDIAITEM.ZVCARDSTRING IS NOT NULL
                            {date_filter}
                            {chat_filter_include}
                            {chat_filter_exclude}
                    """
                c.execute(fallback_query)
                contents = c.fetchall()
                logger.info("Fallback vCard query succeeded")
            except Exception as fallback_error:
                logger.warning(f"Fallback vCard query also failed: {fallback_error}")
                logger.info("Skipping vCard processing completely")
                return
        else:
            logger.info("No fallback options available, skipping vCard processing")
            return

    if not contents:
        logger.info("No vCard data found in database")
        return

    # Create vCards directory
    path = f"{media_folder}/Message/vCards"
    Path(path).mkdir(parents=True, exist_ok=True)

    # Process each vCard with progress bar
    processed_count = 0
    skipped_count = 0

    for content in track(
        contents,
        description="Processing vCards",
        transient=True,
        disable=not sys.stdout.isatty(),
    ):
        result = process_vcard_item(content, path, data)
        if result is True:  # Successfully processed
            processed_count += 1
        else:  # Failed or skipped
            skipped_count += 1

    # Provide summary instead of individual warnings
    if skipped_count > 0:
        logger.info(
            f"vCard processing complete: {processed_count} processed, {skipped_count} skipped (missing data)"
        )
    elif processed_count > 0:
        logger.info(f"vCard processing complete: {processed_count} processed")
    else:
        logger.info("vCard processing complete: no vCards found")


def process_vcard_item(content, path, data):
    """Process a single vCard item."""
    # Validate required fields
    try:
        vcard_name = content["ZVCARDNAME"] if "ZVCARDNAME" in content else None
        vcard_string = content["ZVCARDSTRING"] if "ZVCARDSTRING" in content else None
        contact_jid = content["ZCONTACTJID"] if "ZCONTACTJID" in content else None
        message_id = content["ZMESSAGE"] if "ZMESSAGE" in content else None
    except (KeyError, TypeError):
        # Only log at debug level to reduce verbosity
        logger.debug("Invalid content structure in vCard processing")
        return

    if not vcard_name or not vcard_string:
        # Only log at debug level since this is common and expected
        logger.debug("Missing vCard name or string data - skipping record")
        return False

    if not contact_jid or not message_id:
        # Only log at debug level to reduce verbosity
        logger.debug("Missing contact or message reference in vCard")
        return False

    file_paths = []

    # Handle simple vCard names (fallback case)
    if vcard_name == "vCard" or not vcard_name or vcard_name == "Unknown vCard":
        vcard_names = ["Contact"]
    else:
        vcard_names = vcard_name.split("_$!<Name-Separator>!$_")

    # Handle simple vCard strings
    if "_$!<VCard-Separator>!$_" in vcard_string:
        vcard_strings = vcard_string.split("_$!<VCard-Separator>!$_")
    else:
        vcard_strings = [vcard_string]

    # If this is a list of contacts
    if len(vcard_names) > len(vcard_strings):
        vcard_names.pop(0)  # Dismiss the first element, which is the group name

    # Save each vCard file
    for name, vcard_string in zip(vcard_names, vcard_strings):
        file_name = "".join(x for x in name if x.isalnum())
        file_name = file_name.encode("utf-8")[:230].decode("utf-8", "ignore")
        file_path = os.path.join(path, f"{file_name}.vcf")
        file_paths.append(file_path)

        if not os.path.isfile(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(vcard_string)

    # Create vCard summary and update message
    vcard_summary = "This media include the following vCard file(s):<br>"
    vcard_summary += " | ".join(
        [
            f'<a href="{htmle(fp)}">{htmle(name)}</a>'
            for name, fp in zip(vcard_names, file_paths)
        ]
    )

    # Validate chat and message exist before updating
    chat = data.get_chat(contact_jid)
    if not chat:
        logger.debug(f"Chat not found for vCard: {contact_jid}")
        return False

    message = chat.get_message(message_id)
    if not message:
        logger.debug(f"Message not found for vCard: {message_id}")
        return False

    message.data = vcard_summary
    message.mime = "text/x-vcard"
    message.media = True
    message.meta = True
    message.safe = True

    return True  # Successfully processed


def calls(db, data, timezone_offset, filter_chat):
    """Process WhatsApp call records."""

    # Handle both string path and connection object
    if isinstance(db, str):
        import sqlite3

        with sqlite3.connect(db) as db_conn:
            db_conn.row_factory = sqlite3.Row
            return calls(db_conn, data, timezone_offset, filter_chat)

    # Check what tables are available
    has_call_event = _check_table_exists(db, "ZWACDCALLEVENT")
    has_aggregate_call_event = _check_table_exists(db, "ZWAAGGREGATECALLEVENT")

    logger.info(
        f"Call tables - ZWACDCALLEVENT: {has_call_event}, ZWAAGGREGATECALLEVENT: {has_aggregate_call_event}"
    )

    # If no call tables, skip processing
    if not has_call_event:
        logger.info("No ZWACDCALLEVENT table found, skipping calls processing")
        return

    c = db.cursor()

    # Build filter conditions
    chat_filter_include = get_chat_condition(
        filter_chat[0], True, ["ZGROUPCALLCREATORUSERJIDSTRING"], None, "ios"
    )
    chat_filter_exclude = get_chat_condition(
        filter_chat[1], False, ["ZGROUPCALLCREATORUSERJIDSTRING"], None, "ios"
    )

    # Get call count
    call_count_query = f"""
        SELECT count()
        FROM ZWACDCALLEVENT
        WHERE 1=1
            {chat_filter_include}
            {chat_filter_exclude}
    """
    c.execute(call_count_query)
    total_row_number = c.fetchone()[0]
    if total_row_number == 0:
        return

    # Fetch call records - use simplified query if aggregate table missing
    if has_aggregate_call_event:
        calls_query = f"""
            SELECT ZCALLIDSTRING,
                ZGROUPCALLCREATORUSERJIDSTRING,
                ZGROUPJIDSTRING,
                ZDATE,
                ZOUTCOME,
                ZBYTESRECEIVED + ZBYTESSENT AS bytes_transferred,
                ZDURATION,
                ZVIDEO,
                ZMISSED,
                ZINCOMING
            FROM ZWACDCALLEVENT
                INNER JOIN ZWAAGGREGATECALLEVENT
                    ON ZWACDCALLEVENT.Z1CALLEVENTS = ZWAAGGREGATECALLEVENT.Z_PK
            WHERE 1=1
                {chat_filter_include}
                {chat_filter_exclude}
        """
    else:
        calls_query = f"""
            SELECT ZCALLIDSTRING,
                ZGROUPCALLCREATORUSERJIDSTRING,
                ZGROUPJIDSTRING,
                ZDATE,
                ZOUTCOME,
                COALESCE(ZBYTESRECEIVED, 0) + COALESCE(ZBYTESSENT, 0) AS bytes_transferred,
                ZDURATION,
                ZVIDEO,
                ZMISSED,
                ZINCOMING
            FROM ZWACDCALLEVENT
            WHERE 1=1
                {chat_filter_include}
                {chat_filter_exclude}
        """
    c.execute(calls_query)

    # Create calls chat
    chat = ChatStore(Device.ANDROID, "WhatsApp Calls")

    # Process each call with progress bar
    content = c.fetchone()
    for _ in track(
        range(total_row_number),
        description="Processing calls",
        transient=True,
        disable=not sys.stdout.isatty(),
    ):
        if content is None:
            break
        process_call_record(content, chat, data, timezone_offset)
        content = c.fetchone()

    # Add calls chat to data
    data.add_chat("000000000000000", chat)


def process_call_record(content, chat, data, timezone_offset):
    """Process a single call record."""
    # Validate required fields
    try:
        date_field = content["ZDATE"] if "ZDATE" in content else None
    except (KeyError, TypeError):
        logger.warning("Invalid content structure in call processing")
        return

    if not date_field:
        logger.warning("Missing date in call record")
        return

    try:
        ts = APPLE_TIME + int(date_field)
    except (ValueError, TypeError):
        logger.warning(f"Invalid date value in call record: {date_field}")
        return

    call = Message(
        from_me=bool(content["ZINCOMING"] == 0 if "ZINCOMING" in content else False),
        timestamp=ts,
        time=ts,
        key_id=(
            hash(content["ZCALLIDSTRING"])
            if "ZCALLIDSTRING" in content and content["ZCALLIDSTRING"]
            else hash(str(ts))
        ),
        timezone_offset=int(timezone_offset if timezone_offset else CURRENT_TZ_OFFSET),
        message_type=0,
        received_timestamp=int(ts),
        read_timestamp=int(ts),
    )

    # Set sender info with safe handling
    _jid = (
        content["ZGROUPCALLCREATORUSERJIDSTRING"]
        if "ZGROUPCALLCREATORUSERJIDSTRING" in content
        else None
    )
    name = None
    if _jid and _jid in data:
        chat_ref = data.get_chat(_jid)
        if chat_ref:
            name = chat_ref.name

    if _jid and "@" in str(_jid):
        fallback = str(_jid).split("@")[0]
    else:
        fallback = "Unknown Caller"

    call.sender = name or fallback

    # Set call metadata
    call.meta = True
    formatted_data = format_call_data(call, content)
    setattr(call, "data", formatted_data)

    # Add call to chat
    chat.add_message(call.key_id, call)


def format_call_data(call, content):
    """Format call data message based on call attributes."""
    # Basic call info with safe field access
    is_group = (
        content["ZGROUPJIDSTRING"] is not None
        if "ZGROUPJIDSTRING" in content
        else False
    )
    is_video = content["ZVIDEO"] == 1 if "ZVIDEO" in content else False

    call_data = (
        f"A {'group ' if is_group else ''}"
        f"{'video' if is_video else 'voice'} "
        f"call {'to' if call.from_me else 'from'} "
        f"{call.sender} was "
    )

    # Call outcome with safe handling
    outcome = content["ZOUTCOME"] if "ZOUTCOME" in content else None
    if outcome in (1, 4):
        call_data += "not answered." if call.from_me else "missed."
    elif outcome == 2:
        call_data += "failed."
    elif outcome == 0:
        duration = content["ZDURATION"] if "ZDURATION" in content else 0
        bytes_transferred = (
            content["bytes_transferred"] if "bytes_transferred" in content else 0
        )

        try:
            call_time = (
                convert_time_unit(int(duration)) if duration else "unknown duration"
            )
            call_bytes = (
                bytes_to_readable(bytes_transferred) if bytes_transferred else "no data"
            )
            call_data += (
                f"initiated and lasted for {call_time} "
                f"with {call_bytes} transferred."
            )
        except (ValueError, TypeError):
            call_data += "initiated successfully."
    else:
        call_data += "in an unknown state."

    return call_data


def create_html(
    data,
    output_folder,
    template=None,
    embedded=False,
    offline_static=False,
    maximum_size=None,
    no_avatar=False,
    experimental=False,
    headline=None,
):
    """Generate HTML chat files from data for iOS platform."""
    # Import here to avoid circular imports
    from Whatsapp_Chat_Exporter.utility import (
        get_file_name,
        get_status_location,
        setup_template,
        is_group_jid,
    )

    template = setup_template(template, no_avatar, experimental)

    # Create output directory if it doesn't exist
    if not os.path.isdir(output_folder):
        os.mkdir(output_folder)

    groups_dir = os.path.join(output_folder, "groups")
    individuals_dir = os.path.join(output_folder, "individuals")
    os.makedirs(groups_dir, exist_ok=True)
    os.makedirs(individuals_dir, exist_ok=True)

    # Convert boolean to string for offline_static parameter
    offline_static_str = "offline" if offline_static else ""
    w3css = get_status_location(output_folder, offline_static_str, allow_download=False)

    for contact in track(
        data,
        description="Generating chats",
        transient=True,
        disable=not sys.stdout.isatty(),
    ):
        current_chat = data.get_chat(contact)
        if len(current_chat) == 0:
            # Skip empty chats
            continue

        safe_file_name, name = get_file_name(contact, current_chat)

        target_dir = groups_dir if is_group_jid(contact) else individuals_dir

        if maximum_size is not None:
            _generate_paginated_chat_ios(
                current_chat,
                safe_file_name,
                name,
                contact,
                target_dir,
                template,
                w3css,
                maximum_size,
                headline,
            )
        else:
            _generate_single_chat_ios(
                current_chat,
                safe_file_name,
                name,
                contact,
                target_dir,
                template,
                w3css,
                headline,
            )


def _generate_single_chat_ios(
    current_chat,
    safe_file_name,
    name,
    contact,
    output_folder,
    template,
    w3css,
    headline,
):
    """Generate a single HTML file for a chat - iOS optimized."""
    from Whatsapp_Chat_Exporter.utility import rendering

    output_file_name = f"{output_folder}/{safe_file_name}.html"
    rendering(
        output_file_name,
        template,
        name,
        current_chat.values(),
        contact,
        w3css,
        current_chat,
        headline,
        False,
    )


def _generate_paginated_chat_ios(
    current_chat,
    safe_file_name,
    name,
    contact,
    output_folder,
    template,
    w3css,
    maximum_size,
    headline,
):
    """Generate multiple HTML files for a chat when pagination is required - iOS optimized."""
    from Whatsapp_Chat_Exporter.utility import MAX_SIZE, ROW_SIZE, rendering

    current_size = 0
    current_page = 1
    render_box = []

    # Use default maximum size if set to 0
    if maximum_size == 0:
        maximum_size = MAX_SIZE

    last_msg = current_chat.get_last_message().key_id

    for message in current_chat.values():
        # Calculate message size
        if message.data is not None and not message.meta and not message.media:
            current_size += len(message.data) + ROW_SIZE
        else:
            current_size += ROW_SIZE + 100  # Assume media and meta HTML are 100 bytes

        if current_size > maximum_size:
            # Create a new page
            output_file_name = f"{output_folder}/{safe_file_name}-{current_page}.html"
            rendering(
                output_file_name,
                template,
                name,
                render_box,
                contact,
                w3css,
                current_chat,
                headline,
                next=f"{safe_file_name}-{current_page + 1}.html",
                previous=(
                    f"{safe_file_name}-{current_page - 1}.html"
                    if current_page > 1
                    else False
                ),
            )
            render_box = [message]
            current_size = 0
            current_page += 1
        else:
            render_box.append(message)
            if message.key_id == last_msg:
                # Last message, create final page
                if current_page == 1:
                    output_file_name = f"{output_folder}/{safe_file_name}.html"
                else:
                    output_file_name = (
                        f"{output_folder}/{safe_file_name}-{current_page}.html"
                    )
                rendering(
                    output_file_name,
                    template,
                    name,
                    render_box,
                    contact,
                    w3css,
                    current_chat,
                    headline,
                    False,
                    previous=f"{safe_file_name}-{current_page - 1}.html",
                )
