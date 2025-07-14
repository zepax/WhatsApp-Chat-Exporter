#!/usr/bin/python3

import os
import sys
from datetime import datetime
from mimetypes import MimeTypes

from rich.progress import track
from Whatsapp_Chat_Exporter.data_model import ChatStore, Message
from Whatsapp_Chat_Exporter.utility import Device

# Cache mapping base directory to a filename->path map
_MEDIA_CACHE: dict[str, dict[str, str]] = {}


def _build_media_cache(base_dir: str) -> None:
    """Populate the media cache for ``base_dir`` once."""
    abs_base = os.path.abspath(base_dir)
    if abs_base in _MEDIA_CACHE:
        return

    mapping: dict[str, str] = {}
    for root, _, files in os.walk(abs_base):
        for file in files:
            candidate = os.path.join(root, file)
            candidate_abs = os.path.abspath(candidate)
            if candidate_abs.startswith(abs_base + os.sep):
                mapping[file] = candidate_abs

    _MEDIA_CACHE[abs_base] = mapping


def _find_media_file(base_dir: str, filename: str) -> str | None:
    """Search recursively for a media file within ``base_dir``.

    Args:
        base_dir: Root directory of the exported chat.
        filename: Name of the file to locate.

    Returns:
        Absolute path to the file if found, otherwise ``None``.
    """
    abs_base = os.path.abspath(base_dir)
    cache = _MEDIA_CACHE.get(abs_base)
    if cache is not None:
        path = cache.get(filename)
        if path is not None and os.path.isfile(path):
            return path
        return None

    for root, _, files in os.walk(abs_base):
        if filename in files:
            candidate = os.path.join(root, filename)
            candidate_abs = os.path.abspath(candidate)
            if candidate_abs.startswith(abs_base + os.sep):
                _MEDIA_CACHE[abs_base] = {filename: candidate_abs}
                return candidate_abs
    return None


# Reuse a single MimeTypes instance to avoid repeated initialisation
MIME = MimeTypes()


def messages(path, data, assume_first_as_me=False, prompt_user=False):
    """
    Extracts messages from an exported WhatsApp chat file.

    Args:
        path: Path to the exported chat file
        data: Data container object to store the parsed chat
        assume_first_as_me: If True, assume the first message is sent from the user
        prompt_user: Whether to interactively confirm the user's name

    Returns:
        Updated data container with extracted messages
    """
    # Create a new chat in the data container
    chat = data.add_chat("ExportedChat", ChatStore(Device.EXPORTED))
    _build_media_cache(os.path.dirname(os.path.abspath(path)))
    you = ""  # Will store the username of the current user
    user_identification_done = (
        False  # Flag to track if user identification has been done
    )

    # Process the file while also counting the total lines for progress
    with open(path, "r", encoding="utf8") as file:
        total_row_number = sum(1 for _ in file)
        file.seek(0)
        for index, line in track(
            enumerate(file),
            total=total_row_number,
            description="Processing messages & media",
            transient=True,
            disable=not sys.stdout.isatty(),
        ):
            you, user_identification_done = process_line(
                line,
                index,
                chat,
                path,
                you,
                assume_first_as_me,
                user_identification_done,
                prompt_user,
            )

    return data


def process_line(
    line,
    index,
    chat,
    file_path,
    you,
    assume_first_as_me,
    user_identification_done,
    prompt_user,
):
    """
    Process a single line from the chat file

    Returns:
        Tuple of (updated_you_value, updated_user_identification_done_flag)
    """
    parts = line.split(" - ", 1)

    # Check if this is a new message (has timestamp format)
    if len(parts) > 1:
        time = parts[0]
        you, user_identification_done = process_new_message(
            time,
            parts[1],
            index,
            chat,
            you,
            file_path,
            assume_first_as_me,
            user_identification_done,
            prompt_user,
        )
    else:
        # This is a continuation of the previous message
        process_message_continuation(line, index, chat)

    return you, user_identification_done


def process_new_message(
    time,
    content,
    index,
    chat,
    you,
    file_path,
    assume_first_as_me,
    user_identification_done,
    prompt_user,
):
    """
    Process a line that contains a new message

    Returns:
        Tuple of (updated_you_value, updated_user_identification_done_flag)
    """
    # Create a new message
    msg = Message(
        from_me=False,  # Will be updated later if needed
        timestamp=datetime.strptime(time, "%d/%m/%Y, %H:%M").timestamp(),
        time=time.split(", ")[1].strip(),
        key_id=index,
        received_timestamp=None,
        read_timestamp=None,
    )

    # Check if this is a system message (no name:message format)
    if ":" not in content:
        msg.data = content
        msg.meta = True
    else:
        # Process user message
        name, message = content.strip().split(":", 1)

        # Handle user identification
        if you == "":
            if chat.name is None:
                # First sender identification
                if not user_identification_done:
                    if assume_first_as_me:
                        you = name
                    elif prompt_user:
                        you = prompt_for_user_identification(name)
                    else:
                        you = ""
                    user_identification_done = True
            else:
                # If we know the chat name, anyone else must be "you"
                if name != chat.name:
                    you = name

        # Set the chat name if needed
        if chat.name is None and name != you:
            chat.name = name

        # Determine if this message is from the current user
        msg.from_me = name == you

        # Process message content
        process_message_content(msg, message, file_path)

    chat.add_message(index, msg)
    return you, user_identification_done


def process_message_content(msg, message, file_path):
    """Process and set the content of a message based on its type"""
    if "<Media omitted>" in message:
        msg.data = "The media is omitted in the chat"
        msg.mime = "media"
        msg.meta = True
    elif "(file attached)" in message:
        process_attached_file(msg, message, file_path)
    else:
        msg.data = message.replace("\r\n", "<br>").replace("\n", "<br>")


def process_attached_file(msg, message, file_path):
    """Process an attached file in a message."""
    msg.media = True

    # Extract file path and check if it exists
    file_name = message.split("(file attached)")[0].strip()
    base_dir = os.path.abspath(os.path.dirname(file_path))
    attached_file_path = os.path.normpath(os.path.join(base_dir, file_name))

    if attached_file_path.startswith(base_dir + os.sep) and os.path.isfile(
        attached_file_path
    ):
        msg.data = attached_file_path
        guess = MIME.guess_type(attached_file_path)[0]
        msg.mime = guess if guess is not None else "application/octet-stream"
        return

    if os.path.basename(file_name) == file_name:
        found = _find_media_file(base_dir, file_name)
        if found is not None:
            msg.data = found
            guess = MIME.guess_type(found)[0]
            msg.mime = guess if guess is not None else "application/octet-stream"
            return

    msg.data = "The media is missing"
    msg.mime = "media"
    msg.meta = True


def process_message_continuation(line, index, chat):
    """Process a line that continues a previous message"""
    # Find the previous message
    lookback = index - 1
    keys = chat.keys()
    while lookback not in keys:
        lookback -= 1

    msg = chat.get_message(lookback)

    # Add the continuation line to the message
    if msg.media:
        msg.caption = line.strip()
    else:
        msg.data += "<br>" + line.strip()


def prompt_for_user_identification(name):
    """Ask the user if the given name is their username"""
    while True:
        ans = input(f"Is '{name}' you? (Y/N) ").strip().lower()
        if ans == "y":
            return name
        if ans == "n":
            return ""
