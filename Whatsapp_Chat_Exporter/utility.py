import sqlite3
import jinja2
import json
import os
import unicodedata
import re
import math
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from bleach import clean as sanitize
from markupsafe import Markup
from datetime import datetime, timedelta
from enum import IntEnum
from Whatsapp_Chat_Exporter.data_model import ChatStore
from typing import Dict, List, Optional, Tuple
from rich.progress import track
import logging

logger = logging.getLogger(__name__)
try:
    from enum import StrEnum, IntEnum
except ImportError:
    # < Python 3.11
    # This should be removed when the support for Python 3.10 ends.
    from enum import Enum
    class StrEnum(str, Enum):
        pass

    class IntEnum(int, Enum):
        pass

MAX_SIZE = 4 * 1024 * 1024  # Default 4MB
ROW_SIZE = 0x3D0
CURRENT_TZ_OFFSET = (
    datetime.now().astimezone().utcoffset().total_seconds() / 3600
)


def convert_time_unit(time_second: int) -> str:
    """Converts a time duration in seconds to a human-readable string.

    Args:
        time_second: The time duration in seconds.

    Returns:
        str: A human-readable string representing the time duration.
    """
    time = str(timedelta(seconds=time_second))
    if "day" not in time:
        if time_second < 1:
            time = "less than a second"
        elif time_second == 1:
            time = "a second"
        elif time_second < 60:
            time = time[5:][1 if time_second < 10 else 0:] + " seconds"
        elif time_second == 60:
            time = "a minute"
        elif time_second < 3600:
            time = time[2:] + " minutes"
        elif time_second == 3600:
            time = "an hour"
        else:
            time += " hour"
    return time


def bytes_to_readable(size_bytes: int) -> str:
    """Converts a file size in bytes to a human-readable string with units.

    From https://stackoverflow.com/a/14822210/9478891
    Authors: james-sapam & other contributors
    Licensed under CC BY-SA 3.0
    See git commit logs for changes, if any.

    Args:
        size_bytes: The file size in bytes.

    Returns:
        A human-readable string representing the file size.
    """
    if size_bytes == 0:
       return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def readable_to_bytes(size_str: str) -> int:
    """Converts a human-readable file size string to bytes.

    Args:
        size_str: The human-readable file size string (e.g., "1024KB", "1MB", "2GB").

    Returns:
        The file size in bytes.

    Raises:
        ValueError: If the input string is invalid.
    """
    SIZE_UNITS = {
        'B': 1,
        'KB': 1024,
        'MB': 1024**2,
        'GB': 1024**3,
        'TB': 1024**4,
        'PB': 1024**5,
        'EB': 1024**6,
        'ZB': 1024**7, 
        'YB': 1024**8
    }
    size_str = size_str.upper().strip()
    number, unit = size_str[:-2].strip(), size_str[-2:].strip()
    if unit not in SIZE_UNITS or not number.isnumeric():
        raise ValueError("Invalid input for size_str. Example: 1024GB")
    return int(number) * SIZE_UNITS[unit]


def extract_archive(path: str) -> str:
    """Extract a ZIP or TAR archive to a temporary directory.

    Args:
        path: Path to the archive file.

    Returns:
        Path to the extracted directory.

    Raises:
        ValueError: If the file format is not supported.
    """
    tmp_dir = tempfile.mkdtemp(prefix="wce_")

    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            zf.extractall(tmp_dir)
    else:
        try:
            with tarfile.open(path) as tf:
                members = []
                for member in tf.getmembers():
                    target = os.path.normpath(os.path.join(tmp_dir, member.name))
                    if not target.startswith(os.path.abspath(tmp_dir) + os.sep):
                        shutil.rmtree(tmp_dir)
                        raise ValueError(
                            f"Unsafe path detected in archive: {member.name}"
                        )
                    members.append(member)
                tf.extractall(tmp_dir, members=members)
        except tarfile.TarError as exc:
            shutil.rmtree(tmp_dir)
            raise ValueError("Unsupported archive format") from exc

    return tmp_dir


def sanitize_except(html: str) -> Markup:
    """Sanitizes HTML, only allowing <br> tag.

    Args:
        html: The HTML string to sanitize.

    Returns:
        A Markup object containing the sanitized HTML.
    """
    return Markup(sanitize(html, tags=["br"]))


def determine_day(last: int, current: int) -> Optional[datetime.date]:
    """Determines if the day has changed between two timestamps. Exposed to Jinja's environment.

    Args:
        last: The timestamp of the previous message.
        current: The timestamp of the current message.

    Returns:
        The date of the current message if it's a different day than the last message, otherwise None.
    """
    last = datetime.fromtimestamp(last).date()
    current = datetime.fromtimestamp(current).date()
    if last == current:
        return None
    else:
        return current


def check_update(allow_network: bool = False):
    """Check PyPI for a newer version if network access is allowed."""
    if not allow_network:
        logger.info("Network access disabled; skipping update check.")
        return 0
    import urllib.request
    import json
    import importlib
    from sys import platform

    PACKAGE_JSON = "https://pypi.org/pypi/whatsapp-chat-exporter/json"
    try:
        raw = urllib.request.urlopen(PACKAGE_JSON)
    except Exception:
        logger.warning("Failed to check for updates.")
        return 1
    else:
        with raw:
            package_info = json.load(raw)
            latest_version = tuple(map(int, package_info["info"]["version"].split(".")))
            __version__ = importlib.metadata.version("whatsapp_chat_exporter")
            current_version = tuple(map(int, __version__.split(".")))
            if current_version < latest_version:
                logger.info("===============Update===============")
                logger.info("A newer version of WhatsApp Chat Exporter is available.")
                logger.info("Current version: %s", __version__)
                logger.info("Latest version: %s", package_info["info"]["version"])
                if platform == "win32":
                    logger.info(
                        "Update with: pip install --upgrade whatsapp-chat-exporter"
                    )
                else:
                    logger.info(
                        "Update with: pip3 install --upgrade whatsapp-chat-exporter"
                    )
                logger.info("====================================")
            else:
                logger.info("You are using the latest version of WhatsApp Chat Exporter.")
    return 0


def rendering(
        output_file_name,
        template,
        name,
        msgs,
        contact,
        w3css,
        chat,
        headline,
        next=False,
        previous=False
    ):
    if chat.their_avatar_thumb is None and chat.their_avatar is not None:
        their_avatar_thumb = chat.their_avatar
    else:
        their_avatar_thumb = chat.their_avatar_thumb
    if "??" not in headline:
        raise ValueError("Headline must contain '??' to replace with name")
    headline = headline.replace("??", name)
    with open(output_file_name, "w", encoding="utf-8") as f:
        f.write(
            template.render(
                name=name,
                msgs=msgs,
                my_avatar=chat.my_avatar,
                their_avatar=chat.their_avatar,
                their_avatar_thumb=their_avatar_thumb,
                w3css=w3css,
                next=next,
                previous=previous,
                status=chat.status,
                media_base=chat.media_base,
                headline=headline
            )
        )


class Device(StrEnum):
    IOS = "ios"
    ANDROID = "android"
    EXPORTED = "exported"


def import_from_json(json_file: str, data: Dict[str, ChatStore]):
    """Imports chat data from a JSON file into the data dictionary.

    Args:
        json_file: The path to the JSON file.
        data: The dictionary to store the imported chat data.
    """
    from Whatsapp_Chat_Exporter.data_model import ChatStore, Message
    with open(json_file, "r", encoding="utf-8") as f:
        temp_data = json.load(f)
    total_row_number = len(temp_data)
    for index, (jid, chat_data) in track(
        enumerate(temp_data.items(), 1),
        total=total_row_number,
        description="Importing chats from JSON",
        transient=True,
        disable=not sys.stdout.isatty(),
    ):
        chat = ChatStore(chat_data.get("type"), chat_data.get("name"))
        chat.my_avatar = chat_data.get("my_avatar")
        chat.their_avatar = chat_data.get("their_avatar")
        chat.their_avatar_thumb = chat_data.get("their_avatar_thumb")
        chat.status = chat_data.get("status")
        for id, msg in chat_data.get("messages").items():
            message = Message(
                from_me=msg["from_me"],
                timestamp=msg["timestamp"],
                time=msg["time"],
                key_id=msg["key_id"],
                received_timestamp=msg.get("received_timestamp"),
                read_timestamp=msg.get("read_timestamp")
            )
            message.media = msg.get("media")
            message.meta = msg.get("meta")
            message.data = msg.get("data")
            message.sender = msg.get("sender")
            message.safe = msg.get("safe")
            message.mime = msg.get("mime")
            message.reply = msg.get("reply")
            message.quoted_data = msg.get("quoted_data")
            message.caption = msg.get("caption")
            message.thumb = msg.get("thumb")
            message.sticker = msg.get("sticker")
            chat.add_message(id, message)
        data[jid] = chat


def sanitize_filename(file_name: str) -> str:
    """Sanitizes a filename by removing invalid and unsafe characters.

    Args:
        file_name: The filename to sanitize.

    Returns:
        The sanitized filename.
    """
    return "".join(x for x in file_name if x.isalnum() or x in "- ")


def get_file_name(contact: str, chat: ChatStore) -> Tuple[str, str]:
    """Generates a sanitized filename and contact name for a chat.

    Args:
        contact: The contact identifier (e.g., a phone number or group ID).
        chat: The ChatStore object for the chat.

    Returns:
        A tuple containing the sanitized filename and the contact name.

    Raises:
        ValueError: If the contact format is unexpected.
    """
    if "@" not in contact and contact not in ("000000000000000", "000000000000001", "ExportedChat"):
        raise ValueError("Unexpected contact format: " + contact)
    phone_number = contact.split('@')[0]
    if "-" in contact and chat.name is not None:
        file_name = ""
    else:
        file_name = phone_number

    if chat.name is not None:
        if file_name != "":
            file_name += "-"
        file_name += chat.name.replace("/", "-").replace("\\", "-")
        name = chat.name
    else:
        name = phone_number

    return sanitize_filename(file_name), name


def get_cond_for_empty(enable: bool, jid_field: str, broadcast_field: str) -> str:
    """Generates a SQL condition for filtering empty chats.

    Args:
        enable: True to include non-empty chats, False to include empty chats.
        jid_field: The name of the JID field in the SQL query.
        broadcast_field: The column name of the broadcast field in the SQL query.

    Returns:
        A SQL condition string.
    """
    return f"AND (chat.hidden=0 OR {jid_field}='status@broadcast' OR {broadcast_field}>0)" if enable else ""


def get_chat_condition(filter: Optional[List[str]], include: bool, columns: List[str], jid: Optional[str] = None, platform: Optional[str] = None) -> str:
    """Generates a SQL condition for filtering chats based on inclusion or exclusion criteria.

    Args:
        filter: A list of phone numbers to include or exclude.
        include: True to include chats that match the filter, False to exclude them.
        columns: A list of column names to check against the filter.
        jid: The JID column name (used for group identification).
        platform: The platform ("android" or "ios") for platform-specific JID queries.

    Returns:
        A SQL condition string.

    Raises:
        ValueError: If the column count is invalid or an unsupported platform is provided.
    """
    if filter is not None:
        conditions = []
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
            if include:
                conditions.append(f"{' OR' if index > 0 else ''} {columns[0]} LIKE '%{chat}%'")
                if len(columns) > 1:
                    conditions.append(f" OR ({columns[1]} LIKE '%{chat}%' AND {is_group})")
            else:
                conditions.append(f"{' AND' if index > 0 else ''} {columns[0]} NOT LIKE '%{chat}%'")
                if len(columns) > 1:
                    conditions.append(f" AND ({columns[1]} NOT LIKE '%{chat}%' AND {is_group})")
        return f"AND ({' '.join(conditions)})"
    else:
        return ""


# Android Specific
CRYPT14_OFFSETS = (
    {"iv": 67, "db": 191},
    {"iv": 67, "db": 190},
    {"iv": 66, "db": 99},
    {"iv": 67, "db": 193},
    {"iv": 67, "db": 194},
    {"iv": 67, "db": 158},
)


class Crypt(IntEnum):
    CRYPT15 = 15
    CRYPT14 = 14
    CRYPT12 = 12


class DbType(StrEnum):
    MESSAGE = "message"
    CONTACT = "contact"


def _extract_participant(data: Optional[str]) -> Optional[str]:
    """Return participant identifier from metadata."""

    if not data:
        return None
    cleaned = re.sub(r'["\n]', ' ', str(data))
    for token in re.split(r'[ ,;]+', cleaned):
        token = token.strip()
        if not token:
            continue
        if "@" in token:
            return token.split("@")[0]
        return token
    return None


def determine_metadata(content: sqlite3.Row, init_msg: Optional[str]) -> Optional[str]:
    """Return a user friendly description for a group/system message."""

    msg = init_msg or ""
    if content["is_me_joined"] == 1:
        return f"You were added into the group by {msg}"

    action = content["action_type"]

    if action == 1:
        return msg + f" changed the group name to \"{content['data']}\""
    if action in (10, 28):
        try:
            old = content["old_jid"].split("@")[0]
            new = content["new_jid"].split("@")[0]
        except (AttributeError, IndexError):
            return None
        return f"{old} changed their number to {new}"
    if action == 27:
        details = (content["data"] or "Unknown").replace("\n", "<br>")
        return msg + " changed the group description to:<br>" + details
    if action in (18, 57):
        return (
            f"The security code between you and {msg} changed"
            if msg != "You" else "The security code in this chat changed"
        )
    if action in (13, 15, 46, 67, 69):
        return None

    static_actions = {
        4: lambda c, m: (
            f"{_extract_participant(c['data']) or m} was added to the group"
        ),
        5: " left the group",
        6: " changed the group icon",
        7: "You were removed",
        8: (
            "WhatsApp Internal Error Occurred: "
            "you cannot send message to this group"
        ),
        9: " created a broadcast channel",
        11: lambda c, m: m + f' created a group with name: "{c["data"]}"',
        12: lambda c, m: m + f" added {_extract_participant(c['data']) or 'someone'}",
        14: lambda c, m: m + f" removed {_extract_participant(c['data']) or 'someone'}",
        19: "This chat is now end-to-end encrypted",
        20: lambda c, m: (
            f"{_extract_participant(c['data']) or m or 'Someone'} joined this "
            "group by using an invite link"
        ),
        47: "The contact is an official business account",
        50: "The contact's account type changed from business to standard",
        56: "Messgae timer was enabled/updated/disabled",
        58: "You blocked this contact",
    }

    handler = static_actions.get(action)
    if handler is None:
        return None
    if callable(handler):
        return handler(content, msg)
    return msg + handler if handler.startswith(" ") else handler


def get_status_location(
    output_folder: str, offline_static: str, allow_download: bool = False
) -> str:
    """
    Gets the location of the W3.CSS file, either from web or local storage.

    Args:
        output_folder (str): The folder where offline static files will be stored.
        offline_static (str): The subfolder name for static files. If falsy, returns web URL.

    Returns:
        str: The path or URL to the W3.CSS file.
    """
    w3css = "https://www.w3schools.com/w3css/4/w3.css"
    if not offline_static:
        return w3css
    static_folder = os.path.join(output_folder, offline_static)
    w3css_path = os.path.join(static_folder, "w3.css")
    if os.path.isfile(w3css_path):
        return os.path.join(offline_static, "w3.css")
    if not allow_download:
        return w3css
    import urllib.request
    if not os.path.isdir(static_folder):
        os.mkdir(static_folder)
    if not os.path.isfile(w3css_path):
        with urllib.request.urlopen(w3css) as resp:
            with open(w3css_path, "wb") as f:
                f.write(resp.read())
    w3css = os.path.join(offline_static, "w3.css")
    return w3css


def setup_template(template: Optional[str], no_avatar: bool, experimental: bool = False) -> jinja2.Template:
    """
    Sets up the Jinja2 template environment and loads the template.

    Args:
        template (Optional[str]): Path to custom template file. If None, uses default template.
        no_avatar (bool): Whether to disable avatar display in the template.
        experimental (bool, optional): Whether to use experimental template features. Defaults to False.

    Returns:
        jinja2.Template: The configured Jinja2 template object.
    """
    if template is None or experimental:
        template_dir = os.path.dirname(__file__)
        template_file = "whatsapp.html" if not experimental else template
    else:
        template_dir = os.path.dirname(template)
        template_file = os.path.basename(template)
    template_loader = jinja2.FileSystemLoader(searchpath=template_dir)
    template_env = jinja2.Environment(loader=template_loader, autoescape=True)
    template_env.globals.update(
        determine_day=determine_day,
        no_avatar=no_avatar
    )
    template_env.filters['sanitize_except'] = sanitize_except
    return template_env.get_template(template_file)

# iOS Specific
APPLE_TIME = 978307200


def slugify(value: str, allow_unicode: bool = False) -> str:
    """
    Convert text to ASCII-only slugs for URL-safe strings.
    Taken from https://github.com/django/django/blob/master/django/utils/text.py

    Args:
        value (str): The string to convert to a slug.
        allow_unicode (bool, optional): Whether to allow Unicode characters. Defaults to False.

    Returns:
        str: The slugified string with only alphanumerics, underscores, or hyphens.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


def copy_parallel(file_pairs: List[Tuple[str, str]], workers: int = 4) -> None:
    """Copy multiple files concurrently.

    Args:
        file_pairs: List of ``(src, dst)`` tuples.
        workers: Maximum number of concurrent threads.
    """
    with ThreadPoolExecutor(max_workers=workers) as executor:
        tasks = [executor.submit(shutil.copy2, src, dst) for src, dst in file_pairs]
        for task in tasks:
            task.result()


class WhatsAppIdentifier(StrEnum):
    MESSAGE = "7c7fba66680ef796b916b067077cc246adacf01d" # AppDomainGroup-group.net.whatsapp.WhatsApp.shared-ChatStorage.sqlite
    CONTACT = "b8548dc30aa1030df0ce18ef08b882cf7ab5212f" # AppDomainGroup-group.net.whatsapp.WhatsApp.shared-ContactsV2.sqlite
    CALL = "1b432994e958845fffe8e2f190f26d1511534088" # AppDomainGroup-group.net.whatsapp.WhatsApp.shared-CallHistory.sqlite
    DOMAIN = "AppDomainGroup-group.net.whatsapp.WhatsApp.shared"


class WhatsAppBusinessIdentifier(StrEnum):
    MESSAGE = "724bd3b98b18518b455a87c1f3ac3a0d189c4466" # AppDomainGroup-group.net.whatsapp.WhatsAppSMB.shared-ChatStorage.sqlite
    CONTACT = "d7246a707f51ddf8b17ee2dddabd9e0a4da5c552" # AppDomainGroup-group.net.whatsapp.WhatsAppSMB.shared-ContactsV2.sqlite
    CALL = "b463f7c4365eefc5a8723930d97928d4e907c603" # AppDomainGroup-group.net.whatsapp.WhatsAppSMB.shared-CallHistory.sqlite
    DOMAIN = "AppDomainGroup-group.net.whatsapp.WhatsAppSMB.shared" 

class JidType(IntEnum):
    PM = 0
    GROUP = 1
    SYSTEM_BROADCAST = 5
    STATUS = 11
