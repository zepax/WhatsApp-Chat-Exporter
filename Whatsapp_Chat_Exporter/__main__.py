#!/usr/bin/python3

import asyncio
import importlib.metadata
import json
import logging
import os
import shutil
import sqlite3
import string
import sys
import tarfile
import zipfile
from argparse import ArgumentParser
from datetime import datetime
from typing import Dict, List, Optional

import aiofiles
import psutil
from rich.progress import track

from Whatsapp_Chat_Exporter import (
    android_crypt,
    android_handler,
    exported_handler,
    ios_handler,
    ios_media_handler,
)
from Whatsapp_Chat_Exporter.data_model import ChatCollection, ChatStore
from Whatsapp_Chat_Exporter.utility import (
    APPLE_TIME,
    Crypt,
    DbType,
    bytes_to_readable,
    check_update,
    copy_parallel,
    extract_archive,
    import_from_json,
    readable_to_bytes,
    sanitize_filename,
)

from .logging_config import (
    get_logger,
    get_security_logger,
    log_operation,
    log_performance,
    setup_logging,
)
from .optimized_handlers import cleanup_optimizations
from .database_optimizer import optimized_db_connection

# Import security and logging utilities
from .security_utils import PathTraversalError, SecurePathValidator

logger = logging.getLogger(__name__)


def setup_basic_logging(verbose: bool = False) -> None:
    """Configure basic logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


# WhatsApp initial release timestamp (2009-01-01)
WHATSAPP_LAUNCH_TS = 1009843200

# Try to import vobject for contacts processing
try:
    import vobject  # noqa: F401
except ModuleNotFoundError:
    vcards_deps_installed = False
else:
    from Whatsapp_Chat_Exporter.vcards_contacts import ContactsFromVCards

    vcards_deps_installed = True


def report_resource_usage(stage: str) -> None:
    """Log memory and disk usage statistics."""
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage(".")
    logger.info(
        "[%s] Memory: %.1f%% used, Disk: %.1f%% used",
        stage,
        mem.percent,
        disk.percent,
    )


def _detect_platform_from_data(data: ChatCollection) -> str:
    """Detect the platform based on the data structure and content."""
    if not data:
        return "unknown"

    # Sample a few chats to detect platform characteristics
    sample_chats = list(data.values())[:5]  # Check first 5 chats

    ios_indicators = 0
    android_indicators = 0

    for chat in sample_chats:
        # Check device type if available
        if hasattr(chat, "device") and chat.device:
            if chat.device.lower() == "ios":
                ios_indicators += 10
            elif chat.device.lower() == "android":
                android_indicators += 10

        # Check for iOS-specific attributes
        if hasattr(chat, "media_base") and chat.media_base:
            if "Message/" in chat.media_base or "AppDomain" in chat.media_base:
                ios_indicators += 2
            elif "WhatsApp/" in chat.media_base:
                android_indicators += 2

        # Check message structure for platform-specific patterns
        sample_messages = list(chat.values())[:3]  # Check first 3 messages per chat
        for message in sample_messages:
            # iOS messages tend to have different timestamp patterns
            if hasattr(message, "timestamp") and message.timestamp:
                # iOS uses APPLE_TIME offset (978307200), Android doesn't
                if message.timestamp > 978307200 and message.timestamp < 2000000000:
                    ios_indicators += 1
                elif message.timestamp > 1000000000 and message.timestamp < 9999999999:
                    android_indicators += 1

    # Return the platform with higher confidence
    if ios_indicators > android_indicators:
        return "ios"
    elif android_indicators > ios_indicators:
        return "android"
    else:
        return "unknown"


def setup_argument_parser() -> ArgumentParser:
    """Set up and return the argument parser with all options."""
    try:
        importlib.metadata.version("whatsapp_chat_exporter")
    except importlib.metadata.PackageNotFoundError:
        pass

    parser = ArgumentParser(
        description="A customizable Android and iOS/iPadOS WhatsApp database parser that "
        "will give you the history of your WhatsApp conversations in HTML "
        "and JSON. Android Backup Crypt12, Crypt14 and Crypt15 supported.",
        epilog=f'WhatsApp Chat Exporter: {importlib.metadata.version("whatsapp_chat_exporter")} Licensed with MIT. See '
        "https://wts.knugi.dev/docs?dest=osl for all open source licenses.",
    )

    # Device type arguments
    device_group = parser.add_argument_group("Device Type")
    device_group.add_argument(
        "-a",
        "--android",
        dest="android",
        default=False,
        action="store_true",
        help="Define the target as Android",
    )
    device_group.add_argument(
        "-i",
        "--ios",
        dest="ios",
        default=False,
        action="store_true",
        help="Define the target as iPhone/iPad",
    )
    device_group.add_argument(
        "-e",
        "--exported",
        dest="exported",
        default=None,
        help="Define the target as exported chat file and specify the path to the file",
    )

    # Input file paths
    input_group = parser.add_argument_group("Input Files")
    input_group.add_argument(
        "-w",
        "--wa",
        dest="wa",
        default=None,
        help="Path to contact database (default: wa.db/ContactsV2.sqlite)",
    )
    input_group.add_argument(
        "-m",
        "--media",
        dest="media",
        default=None,
        help="Path to WhatsApp media folder (default: WhatsApp)",
    )
    input_group.add_argument(
        "-b",
        "--backup",
        dest="backup",
        default=None,
        help="Path to Android (must be used together with -k)/iOS WhatsApp backup",
    )
    input_group.add_argument(
        "-d",
        "--db",
        dest="db",
        default=None,
        help="Path to database file (default: msgstore.db/7c7fba66680ef796b916b067077cc246adacf01d)",
    )
    input_group.add_argument(
        "-k",
        "--key",
        dest="key",
        default=None,
        nargs="?",
        help="Path to key file. If this option is set for crypt15 backup but nothing is specified, you will be prompted to enter the key.",
    )
    input_group.add_argument(
        "--call-db",
        dest="call_db_ios",
        nargs="?",
        default=None,
        type=str,
        const="1b432994e958845fffe8e2f190f26d1511534088",
        help="Path to call database (default: 1b432994e958845fffe8e2f190f26d1511534088) iOS only",
    )
    input_group.add_argument(
        "--wab",
        "--wa-backup",
        dest="wab",
        default=None,
        help="Path to contact database in crypt15 format",
    )

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "-o",
        "--output",
        dest="output",
        default="result",
        help="Output to specific directory (default: result)",
    )
    output_group.add_argument(
        "-j",
        "--json",
        dest="json",
        nargs="?",
        default=None,
        type=str,
        const="result.json",
        help="Save the result to a single JSON file (default if present: result.json)",
    )
    output_group.add_argument(
        "--summary",
        dest="summary",
        default=None,
        help="Write a summary JSON file with chat counts",
    )
    output_group.add_argument(
        "--txt",
        dest="text_format",
        nargs="?",
        default=None,
        type=str,
        const="result",
        help="Export chats in text format similar to what WhatsApp officially provided (default if present: result/)",
    )
    output_group.add_argument(
        "--no-html",
        dest="no_html",
        default=False,
        action="store_true",
        help="Do not output html files",
    )

    output_group.add_argument(
        "--size",
        "--output-size",
        "--split",
        dest="size",
        nargs="?",
        const=0,
        default=None,
        help="Maximum (rough) size of a single output file in bytes, 0 for auto",
    )
    output_group.add_argument(
        "--separate-by-type",
        dest="separate_by_type",
        default=False,
        action="store_true",
        help="Organize output files into separate directories for groups and individuals",
    )

    # JSON formatting options
    json_group = parser.add_argument_group("JSON Options")
    json_group.add_argument(
        "--avoid-encoding-json",
        dest="avoid_encoding_json",
        default=False,
        action="store_true",
        help="Don't encode non-ascii characters in the output JSON files",
    )
    json_group.add_argument(
        "--pretty-print-json",
        dest="pretty_print_json",
        default=None,
        nargs="?",
        const=2,
        type=int,
        help="Pretty print the output JSON.",
    )
    json_group.add_argument(
        "--per-chat",
        dest="json_per_chat",
        default=False,
        action="store_true",
        help="Output the JSON file per chat",
    )
    json_group.add_argument(
        "--import",
        dest="import_json",
        default=False,
        action="store_true",
        help="Import JSON file and convert to HTML output",
    )
    json_group.add_argument(
        "--stream-json",
        dest="stream_json",
        default=False,
        action="store_true",
        help="Stream JSON output to reduce memory usage",
    )

    # HTML options
    html_group = parser.add_argument_group("HTML Options")
    html_group.add_argument(
        "-t",
        "--template",
        dest="template",
        default=None,
        help="HTML template to use. Options: 'basic' (simple), 'optimized' (default, with search), or path to custom template",
    )
    html_group.add_argument(
        "--embedded",
        dest="embedded",
        default=False,
        action="store_true",
        help="Embed media into HTML file (not yet implemented)",
    )
    html_group.add_argument(
        "--offline",
        dest="offline",
        default=None,
        help="Relative path to offline static files",
    )
    html_group.add_argument(
        "--no-avatar",
        dest="no_avatar",
        default=False,
        action="store_true",
        help="Do not render avatar in HTML output",
    )
    html_group.add_argument(
        "--experimental-new-theme",
        dest="whatsapp_theme",
        default=False,
        action="store_true",
        help="Use the newly designed WhatsApp-alike theme",
    )
    html_group.add_argument(
        "--headline",
        dest="headline",
        default="Chat history with ??",
        help="The custom headline for the HTML output. Use '??' as a placeholder for the chat name",
    )

    # Media handling
    media_group = parser.add_argument_group("Media Handling")
    media_group.add_argument(
        "-c",
        "--move-media",
        dest="move_media",
        default=False,
        action="store_true",
        help="Move the media directory to output directory if the flag is set, otherwise copy it",
    )
    media_group.add_argument(
        "--skip-media",
        dest="skip_media",
        action="store_true",
        help="Skip copying or moving the media directory",
    )
    media_group.add_argument(
        "--cleanup-temp",
        dest="cleanup_temp",
        action="store_true",
        help="Remove extracted temporary directories after use",
    )
    media_group.add_argument(
        "--create-separated-media",
        dest="separate_media",
        default=False,
        action="store_true",
        help="Create a copy of the media seperated per chat in <MEDIA>/separated/ directory",
    )

    # Filtering options
    filter_group = parser.add_argument_group("Filtering Options")
    filter_group.add_argument(
        "--time-offset",
        dest="timezone_offset",
        default=0,
        type=int,
        choices=range(-12, 15),
        metavar="{-12 to 14}",
        help="Offset in hours (-12 to 14) for time displayed in the output",
    )
    filter_group.add_argument(
        "--date",
        dest="filter_date",
        default=None,
        metavar="DATE",
        help="The date filter in specific format (inclusive)",
    )
    filter_group.add_argument(
        "--date-format",
        dest="filter_date_format",
        default="%Y-%m-%d %H:%M",
        metavar="FORMAT",
        help="The date format for the date filter",
    )
    filter_group.add_argument(
        "--include",
        dest="filter_chat_include",
        nargs="*",
        metavar="phone number",
        help="Include chats that match the supplied phone number",
    )
    filter_group.add_argument(
        "--exclude",
        dest="filter_chat_exclude",
        nargs="*",
        metavar="phone number",
        help="Exclude chats that match the supplied phone number",
    )
    filter_group.add_argument(
        "--dont-filter-empty",
        dest="filter_empty",
        default=True,
        action="store_false",
        help=(
            "By default, the exporter will not render chats with no valid message. "
            "Setting this flag will cause the exporter to render those. "
            "This is useful if chat(s) are missing from the output"
        ),
    )

    # Contact enrichment
    contact_group = parser.add_argument_group("Contact Enrichment")
    contact_group.add_argument(
        "--enrich-from-vcards",
        dest="enrich_from_vcards",
        default=None,
        help="Path to an exported vcf file from Google contacts export. Add names missing from WhatsApp's default database",
    )
    contact_group.add_argument(
        "--default-country-code",
        dest="default_country_code",
        default=None,
        help="Use with --enrich-from-vcards. When numbers in the vcf file does not have a country code, this will be used. 1 is for US, 66 for Thailand etc. Most likely use the number of your own country",
    )

    # Miscellaneous
    misc_group = parser.add_argument_group("Miscellaneous")
    misc_group.add_argument(
        "-s",
        "--showkey",
        dest="showkey",
        default=False,
        action="store_true",
        help="Show the HEX key used to decrypt the database",
    )
    misc_group.add_argument(
        "--check-update",
        dest="check_update",
        default=False,
        action="store_true",
        help="Check for updates (require Internet access)",
    )
    misc_group.add_argument(
        "--assume-first-as-me",
        dest="assume_first_as_me",
        default=False,
        action="store_true",
        help="Assume the first message in a chat as sent by me (must be used together with -e)",
    )
    misc_group.add_argument(
        "--prompt-user",
        dest="prompt_user",
        default=False,
        action="store_true",
        help="Interactively confirm which participant is me when parsing exported chats",
    )
    misc_group.add_argument(
        "--business",
        dest="business",
        default=False,
        action="store_true",
        help="Use Whatsapp Business default files (iOS only)",
    )
    misc_group.add_argument(
        "--decrypt-chunk-size",
        dest="decrypt_chunk_size",
        default=1 * 1024 * 1024,
        type=int,
        help="Specify the chunk size for decrypting iOS backup, which may affect the decryption speed.",
    )
    misc_group.add_argument(
        "--max-bruteforce-worker",
        dest="max_bruteforce_worker",
        default=10,
        type=int,
        help="Specify the maximum number of worker for bruteforce decryption.",
    )
    misc_group.add_argument(
        "--copy-workers",
        dest="copy_workers",
        default=4,
        type=int,
        help="Number of worker threads for copying exported media files.",
    )
    misc_group.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        default=False,
        action="store_true",
        help="Enable verbose logging",
    )

    return parser


def validate_args(parser: ArgumentParser, args) -> None:
    """Validate command line arguments and modify them if needed."""
    # Basic validation checks
    count = sum(
        [
            bool(args.android),
            bool(args.ios),
            bool(args.exported),
            bool(args.import_json),
        ]
    )
    if count != 1:
        parser.error(
            "You must specify exactly one mode: Android, iOS, exported chat, or import JSON."
        )
    if args.no_html and not args.json and not args.text_format:
        parser.error(
            "You must either specify a JSON output file, text file output directory or enable HTML output."
        )
    if args.import_json and (args.android or args.ios or args.exported or args.no_html):
        parser.error(
            "You can only use --import with -j and without --no-html, -a, -i, -e."
        )
    elif args.import_json and not os.path.isfile(args.json):
        parser.error("JSON file not found.")
    if args.android and args.business:
        parser.error("WhatsApp Business is only available on iOS for now.")
    if "??" not in args.headline:
        parser.error("--headline must contain '??' for replacement.")

    # JSON validation
    if (
        args.json_per_chat
        and args.json
        and (
            (args.json.endswith(".json") and os.path.isfile(args.json))
            or (not args.json.endswith(".json") and os.path.isfile(args.json))
        )
    ):
        parser.error(
            "When --per-chat is enabled, the destination of --json must be a directory."
        )

    # vCards validation
    if args.enrich_from_vcards is not None and args.default_country_code is None:
        parser.error(
            "When --enrich-from-vcards is provided, you must also set --default-country-code"
        )

    # Size validation
    if (
        args.size is not None
        and not isinstance(args.size, int)
        and not args.size.isnumeric()
    ):
        try:
            args.size = readable_to_bytes(args.size)
        except ValueError:
            parser.error(
                "The value for --split must be ended in pure bytes or with a proper unit (e.g., 1048576 or 1MB)"
            )

    # Date filter validation and processing
    if args.filter_date is not None:
        process_date_filter(parser, args)

    # Theme validation
    if args.whatsapp_theme:
        args.template = "whatsapp_new.html"

    # Chat filter validation
    if args.filter_chat_include is not None and args.filter_chat_exclude is not None:
        parser.error("Chat inclusion and exclusion filters cannot be used together.")

    validate_chat_filters(parser, args.filter_chat_include)
    validate_chat_filters(parser, args.filter_chat_exclude)

    def check_exists(path: Optional[str], description: str) -> None:
        if path is not None and not os.path.exists(path):
            parser.error(f"{description} not found at given path: {path}")

    check_exists(args.exported, "Exported chat file")
    check_exists(args.backup, "Backup file")
    check_exists(args.db, "Database file")
    check_exists(args.wa, "Contact database")
    check_exists(args.wab, "Contact backup")
    check_exists(args.call_db_ios, "Call database")

    if args.copy_workers < 1:
        parser.error("--copy-workers must be at least 1")

    if (
        args.backup
        and any(c in args.backup for c in ("crypt12", "crypt14", "crypt15"))
        and args.key is None
    ):
        parser.error("Encryption key needed for this backup; please provide --key")
    if (
        args.key
        and not all(char in string.hexdigits for char in args.key.replace(" ", ""))
        and not os.path.isfile(args.key)
    ):
        parser.error(f"Key file not found at given path: {args.key}")


def validate_chat_filters(
    parser: ArgumentParser, chat_filter: Optional[List[str]]
) -> None:
    """Validate chat filters to ensure they contain only phone numbers."""
    if chat_filter is not None:
        for chat in chat_filter:
            # Enhanced security validation
            if not chat.isnumeric():
                parser.error(
                    "Enter a phone number in the chat filter. See https://wts.knugi.dev/docs?dest=chat"
                )
            # Additional security: check for SQL injection patterns
            dangerous_patterns = [
                "'",
                '"',
                "--",
                "/*",
                "*/",
                ";",
                "DROP",
                "DELETE",
                "UPDATE",
                "INSERT",
            ]
            chat_upper = chat.upper()
            if any(pattern in chat_upper for pattern in dangerous_patterns):
                parser.error("Invalid characters detected in chat filter")


def process_date_filter(parser: ArgumentParser, args) -> None:
    """Process and validate date filter arguments."""
    if " - " in args.filter_date:
        start, end = args.filter_date.split(" - ")
        start = int(datetime.strptime(start, args.filter_date_format).timestamp())
        end = int(datetime.strptime(end, args.filter_date_format).timestamp())

        if start < WHATSAPP_LAUNCH_TS or end < WHATSAPP_LAUNCH_TS:
            parser.error("WhatsApp was first released in 2009...")
        if start > end:
            parser.error("The start date cannot be a moment after the end date.")

        if args.android:
            args.filter_date = f"BETWEEN {start}000 AND {end}000"
        elif args.ios:
            args.filter_date = f"BETWEEN {start - APPLE_TIME} AND {end - APPLE_TIME}"
    else:
        process_single_date_filter(parser, args)


def process_single_date_filter(parser: ArgumentParser, args) -> None:
    """Process single date comparison filters."""
    if len(args.filter_date) < 3:
        parser.error(
            "Unsupported date format. See https://wts.knugi.dev/docs?dest=date"
        )
    _timestamp = int(
        datetime.strptime(args.filter_date[2:], args.filter_date_format).timestamp()
    )

    if _timestamp < WHATSAPP_LAUNCH_TS:
        parser.error("WhatsApp was first released in 2009...")

    if args.filter_date[:2] == "> ":
        if args.android:
            args.filter_date = f">= {_timestamp}000"
        elif args.ios:
            args.filter_date = f">= {_timestamp - APPLE_TIME}"
    elif args.filter_date[:2] == "< ":
        if args.android:
            args.filter_date = f"<= {_timestamp}000"
        elif args.ios:
            args.filter_date = f"<= {_timestamp - APPLE_TIME}"
    else:
        parser.error(
            "Unsupported date format. See https://wts.knugi.dev/docs?dest=date"
        )


def setup_contact_store(args) -> Optional["ContactsFromVCards"]:
    """Set up and return a contact store if needed."""
    if args.enrich_from_vcards is not None:
        if not vcards_deps_installed:
            logger.error(
                "You don't have the dependency to enrich contacts with vCard.\n"
                "Read more on how to deal with enriching contacts:\n"
                "https://github.com/KnugiHK/Whatsapp-Chat-Exporter/blob/main/README.md#usage"
            )
            sys.exit(1)
        contact_store = ContactsFromVCards()
        contact_store.load_vcf_file(args.enrich_from_vcards, args.default_country_code)
        return contact_store
    return None


def decrypt_android_backup(args) -> int:
    """Decrypt Android backup files and return error code."""
    if args.key is None or args.backup is None:
        logger.error("You must specify the backup file with -b and a key with -k")
        return 1
    logger.info("Decryption key specified, decrypting WhatsApp backup...")

    # Determine crypt type
    if "crypt12" in args.backup:
        crypt = Crypt.CRYPT12
    elif "crypt14" in args.backup:
        crypt = Crypt.CRYPT14
    elif "crypt15" in args.backup:
        crypt = Crypt.CRYPT15
    else:
        logger.error(
            "Unknown backup format. The backup file must be crypt12, crypt14 or crypt15."
        )

        return 1

    # Get key with secure path validation
    try:
        key_path = SecurePathValidator.validate_path(args.key)
    except (ValueError, PathTraversalError) as e:
        logger.error("Invalid key path: %s", e)
        return 1

    if not key_path.is_file() and all(
        char in string.hexdigits for char in args.key.replace(" ", "")
    ):
        key = bytes.fromhex(args.key.replace(" ", ""))
    else:
        try:
            with open(key_path, "rb") as f:
                key = f.read()
        except FileNotFoundError:
            logger.error("Key file not found")
            return 1

    # Read backup with secure path validation
    try:
        backup_path = SecurePathValidator.validate_path(args.backup)
        with open(backup_path, "rb") as f:
            db = f.read()
    except (FileNotFoundError, ValueError, PathTraversalError):
        logger.error("Backup file not found or invalid path")
        return 1

    # Process WAB if provided
    error_wa = 0
    if args.wab:
        try:
            wab_path = SecurePathValidator.validate_path(args.wab)
            with open(wab_path, "rb") as f:
                wab = f.read()
        except (FileNotFoundError, ValueError, PathTraversalError):
            logger.error("WAB file not found or invalid path")
            return 1
        error_wa = android_crypt.decrypt_backup(
            wab,
            key,
            output=args.wa,
            crypt=crypt,
            show_crypt15=args.showkey,
            db_type=DbType.CONTACT,
            max_worker=args.max_bruteforce_worker,
        )

    # Decrypt message database
    error_message = android_crypt.decrypt_backup(
        db,
        key,
        output=args.db,
        crypt=crypt,
        show_crypt15=args.showkey,
        db_type=DbType.MESSAGE,
        max_worker=args.max_bruteforce_worker,
    )

    # Handle errors
    if error_wa != 0:
        return error_wa
    return error_message


def handle_decrypt_error(error: int) -> None:
    """Handle decryption errors with appropriate messages."""
    if error == 1:
        logger.error(
            "Dependencies of decrypt_backup and/or extract_encrypted_key are not present. For details, see README.md."
        )
        sys.exit(3)
    elif error == 2:
        logger.error(
            "Failed when decompressing the decrypted backup. Possibly incorrect offsets used in decryption."
        )
        sys.exit(4)
    else:
        logger.error("Unknown error occurred. %s", error)
        sys.exit(5)


def auto_detect_backup(args, temp_dirs) -> None:
    """Auto-detect backup type and adjust args accordingly."""
    if args.android or args.ios or args.exported or args.import_json:
        return
    if args.backup:
        path = args.backup
        if os.path.isfile(path) and (
            zipfile.is_zipfile(path) or tarfile.is_tarfile(path)
        ):
            path = extract_archive(path)
            temp_dirs.append(path)
        lower = os.path.basename(path).lower()
        if lower.endswith((".crypt12", ".crypt14", ".crypt15")):
            args.android = True
            args.backup = path
            return
        if os.path.isdir(path) and os.path.isfile(os.path.join(path, "Manifest.db")):
            args.ios = True
            args.backup = path
            return
        if lower.startswith("msgstore"):
            args.android = True
        elif lower.startswith("chatstorage"):
            args.ios = True
    elif args.db and not (args.android or args.ios):
        name = os.path.basename(args.db).lower()
        if "msgstore" in name:
            args.android = True
        elif "chatstorage" in name:
            args.ios = True


def process_contacts(args, data: ChatCollection, contact_store=None) -> None:
    contact_db = (
        args.wa if args.wa else "wa.db" if args.android else "ContactsV2.sqlite"
    )

    # For iOS, if contact database doesn't exist, use message database for contact names
    if (
        not os.path.isfile(contact_db)
        and not args.android
        and args.db
        and os.path.isfile(args.db)
    ):
        logger.info(
            f"Contact database {contact_db} not found, using message database {args.db} for contact names"
        )
        contact_db = args.db

    # Skip contact processing if using same database file as messages to avoid locks
    if os.path.isfile(contact_db) and contact_db != args.db:
        # Use original handlers to avoid database lock issues
        if args.android:
            import sqlite3

            with sqlite3.connect(contact_db) as cdb:
                cdb.row_factory = sqlite3.Row
                android_handler.contacts(cdb, data, args.timezone_offset)
        else:
            import sqlite3

            with sqlite3.connect(contact_db) as cdb:
                cdb.row_factory = sqlite3.Row
                ios_handler.contacts(cdb, data)
    else:
        logger.info("Skipping contact processing to avoid database conflicts")


def process_messages(args, data: ChatCollection) -> None:
    """Process messages, media and vcards from the database."""
    msg_db = (
        args.db
        if args.db
        else "msgstore.db" if args.android else args.identifiers.MESSAGE
    )

    if not os.path.isfile(msg_db):
        logger.error(
            "The message database does not exist. You may specify the path to database file with option -d or check your provided path."
        )
        sys.exit(6)

    filter_chat = (args.filter_chat_include, args.filter_chat_exclude)

    # Use original handlers to avoid database lock issues
    logger.info(
        f"Processing messages with original {'android' if args.android else 'ios'} handler"
    )

    if args.android:
        with optimized_db_connection(msg_db) as cdb:
            cdb.row_factory = sqlite3.Row
            android_handler.messages(
                cdb,
                data,
                args.media,
                args.timezone_offset,
                args.filter_date,
                filter_chat,
                args.filter_empty,
            )
            android_handler.media(
                cdb,
                data,
                args.media,
                args.filter_date,
                filter_chat,
                args.filter_empty,
                args.separate_media,
            )
            android_handler.vcard(
                cdb, data, args.media, args.filter_date, filter_chat, args.filter_empty
            )
            android_handler.calls(cdb, data, args.timezone_offset, filter_chat)
    else:
        with optimized_db_connection(msg_db) as cdb:
            cdb.row_factory = sqlite3.Row
            ios_handler.messages(
                cdb,
                data,
                args.media,
                args.timezone_offset,
                args.filter_date,
                filter_chat,
                args.filter_empty,
            )
            ios_handler.media(
                cdb,
                data,
                args.media,
                args.filter_date,
                filter_chat,
                args.separate_media,
            )
            ios_handler.vcard(cdb, data, args.media, args.filter_date, filter_chat)
            ios_handler.calls(cdb, data, args.timezone_offset, filter_chat)


def process_calls(args, db, data: ChatCollection, filter_chat) -> None:
    """Process call history if available."""
    if args.android:
        android_handler.calls(db, data, args.timezone_offset, filter_chat)
    elif args.ios and args.call_db_ios is not None:
        with sqlite3.connect(args.call_db_ios) as cdb:
            cdb.row_factory = sqlite3.Row
            ios_handler.calls(cdb, data, args.timezone_offset, filter_chat)


def handle_media_directory(args, temp_dirs=None) -> None:
    """Handle media directory copying or moving."""

    if args.skip_media:
        logger.info("Skipping media directory as per --skip-media")
        return
    if os.path.isdir(args.media):
        dest_name = os.path.basename(args.media.rstrip(os.sep))
        media_path = os.path.join(args.output, dest_name)

        if os.path.isdir(media_path):
            logger.info(
                "WhatsApp directory already exists in output directory. Skipping..."
            )

        else:
            if args.move_media:
                try:
                    logger.info("Moving media directory...")
                    shutil.move(args.media, media_path)
                except PermissionError:
                    logger.error(
                        "Cannot remove original WhatsApp directory. Perhaps the directory is opened?"
                    )
            else:
                logger.info("Copying media directory...")
                shutil.copytree(args.media, media_path)

        if args.cleanup_temp and not args.move_media:
            abs_media = os.path.realpath(args.media)
            if temp_dirs and any(
                abs_media.startswith(os.path.realpath(tmp) + os.sep)
                for tmp in temp_dirs
            ):
                shutil.rmtree(abs_media, ignore_errors=True)
            else:
                logger.warning(
                    "Refusing to delete non-temporary media directory: %s",
                    args.media,
                )


def create_output_files(args, data: ChatCollection, contact_store=None) -> None:
    """Create output files in the specified formats."""
    # Create HTML files if requested
    if not args.no_html:
        # Enrich from vcards if available
        if contact_store and not contact_store.is_empty():
            contact_store.enrich_from_vcards(data)

        # Detect platform and use appropriate HTML generator
        platform_detected = _detect_platform_from_data(data)

        if platform_detected == "ios" and hasattr(ios_handler, "create_html"):
            logger.info("Using iOS-optimized HTML generation")
            ios_handler.create_html(
                data,
                args.output,
                args.template,
                args.embedded,
                args.offline,
                args.size,
                args.no_avatar,
                args.whatsapp_theme,
                args.headline,
                args.separate_by_type,
            )
        else:
            # Use Android handler for Android, exported, or fallback
            logger.info(
                f"Using Android-compatible HTML generation for platform: {platform_detected}"
            )
            android_handler.create_html(
                data,
                args.output,
                args.template,
                args.embedded,
                args.offline,
                args.size,
                args.no_avatar,
                args.whatsapp_theme,
                args.headline,
                args.separate_by_type,
            )

    # Create text files if requested
    if args.text_format:
        logger.info("Writing text file...")
        android_handler.create_txt(data, args.text_format)

    # Create JSON files if requested
    if args.json and not args.import_json:
        export_json(args, data, contact_store)

    # Create summary file if requested
    if args.summary:
        export_summary(args, data)


def export_json(args, data: ChatCollection, contact_store=None) -> None:
    """Export data to JSON format."""
    # Enrich from vcards if available
    if contact_store and not contact_store.is_empty():
        contact_store.enrich_from_vcards(data)

    # Convert ChatStore objects to JSON
    if data and isinstance(data.get(next(iter(data))), ChatStore):
        data = {jik: chat.to_json() for jik, chat in data.items()}

    # Export as a single file or per chat
    if not args.json_per_chat:
        if args.stream_json:
            export_single_json_stream(args, data)
        else:
            export_single_json(args, data)
    else:
        export_multiple_json(args, data)


def export_single_json(args, data: Dict) -> None:
    """Export data to a single JSON file."""
    try:
        json_path = SecurePathValidator.validate_path(args.json)
    except (ValueError, PathTraversalError) as e:
        logger.error("Invalid JSON output path: %s", e)
        return

    with open(json_path, "w") as f:
        json_data = json.dumps(
            data,
            ensure_ascii=not args.avoid_encoding_json,
            indent=args.pretty_print_json,
        )
        logger.info("Writing JSON file...(%s)", bytes_to_readable(len(json_data)))
        f.write(json_data)


def export_single_json_stream(args, data: Dict) -> None:
    """Stream JSON data using asynchronous file writes."""

    async def _stream() -> None:
        try:
            json_path = SecurePathValidator.validate_path(args.json)
        except (ValueError, PathTraversalError) as e:
            logger.error("Invalid JSON output path: %s", e)
            return

        async with aiofiles.open(json_path, "w") as f:
            await f.write("{")
            for index, (jid, chat) in enumerate(data.items()):
                obj = {jid: chat}
                chunk = json.dumps(
                    obj,
                    ensure_ascii=not args.avoid_encoding_json,
                    indent=args.pretty_print_json,
                )[1:-1]
                if args.pretty_print_json is not None and index == 0:
                    await f.write("\n")
                if index > 0:
                    await f.write(",")
                    if args.pretty_print_json is not None:
                        await f.write("\n")
                if args.pretty_print_json is not None:
                    await f.write(" " * args.pretty_print_json + chunk)
                else:
                    await f.write(chunk)
            if args.pretty_print_json is not None:
                await f.write("\n")
            await f.write("}")

    asyncio.run(_stream())


def export_multiple_json(args, data: Dict) -> None:
    """Export data to multiple JSON files, one per chat."""
    # Adjust output path if needed
    try:
        json_path = str(
            SecurePathValidator.validate_path(
                args.json[:-5] if args.json.endswith(".json") else args.json
            )
        )
    except (ValueError, PathTraversalError) as e:
        logger.error("Invalid JSON output directory: %s", e)
        return

    # Create directory if it doesn't exist
    if not os.path.isdir(json_path):
        os.makedirs(json_path, exist_ok=True)

    # Create subdirectories for groups and individuals if requested
    if getattr(args, "separate_by_type", False):
        groups_dir = os.path.join(json_path, "groups")
        individuals_dir = os.path.join(json_path, "individuals")
        os.makedirs(groups_dir, exist_ok=True)
        os.makedirs(individuals_dir, exist_ok=True)

    # Export each chat
    chats = list(data.keys())
    total = len(chats)
    for index, jik in track(
        enumerate(chats, 1), total=total, description="Exporting chats"
    ):
        if data[jik]["name"] is not None:
            contact = data[jik]["name"].replace("/", "")
        else:
            contact = jik.replace("+", "")

        # Determine target directory based on chat type
        if getattr(args, "separate_by_type", False):
            target_dir = (
                os.path.join(json_path, "groups")
                if data[jik].get("is_group", False)
                else os.path.join(json_path, "individuals")
            )
        else:
            target_dir = json_path

        with open(f"{target_dir}/{sanitize_filename(contact)}.json", "w") as f:
            file_content = json.dumps(
                {jik: data[jik]},
                ensure_ascii=not args.avoid_encoding_json,
                indent=args.pretty_print_json,
            )
            f.write(file_content)
        logger.info("Writing JSON file...(%d/%d)", index, total)
    logger.info("")


def export_summary(args, data: ChatCollection) -> None:
    """Write a summary JSON file for the collection."""
    try:
        summary_path = SecurePathValidator.validate_path(args.summary)
    except (ValueError, PathTraversalError) as e:
        logger.error("Invalid summary path: %s", e)
        return

    summary = {"total_chats": len(data), "chats": {}}
    for jid, chat in data.items():
        summary["chats"][jid] = {
            "name": chat.name,
            "message_count": len(chat),
        }
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)


def copy_exported_media(
    chat_file: str, data: ChatCollection, output_dir: str, workers: int = 4
) -> None:
    """Copy media referenced in an exported chat.

    Args:
        chat_file: Path to the exported chat file.
        data: Collection that contains the parsed chat.
        output_dir: Destination folder for the media files.
    """
    src_dir = os.path.dirname(chat_file)
    chat = data.get_chat("ExportedChat")
    if chat is None:
        return

    media_dir = os.path.join(output_dir, "media")
    os.makedirs(media_dir, exist_ok=True)

    file_pairs: list[tuple[str, str]] = []
    for msg in chat.values():
        if msg.media and isinstance(msg.data, str) and os.path.isfile(msg.data):
            try:
                rel_path = os.path.relpath(msg.data, src_dir)
            except ValueError:
                continue

            rel_path = os.path.normpath(rel_path)
            if os.path.isabs(rel_path) or rel_path.startswith(".."):
                logger.warning("Skipping unsafe media path: %s", msg.data)
                continue

            dst = os.path.normpath(os.path.join(media_dir, rel_path))
            media_abs = os.path.abspath(media_dir) + os.sep
            if not os.path.abspath(dst).startswith(media_abs):
                logger.warning("Skipping media outside destination: %s", rel_path)
                continue

            os.makedirs(os.path.dirname(dst), exist_ok=True)
            file_pairs.append((msg.data, dst))
            msg.data = os.path.relpath(dst, output_dir)

    if file_pairs:
        copy_parallel(file_pairs, workers=workers)

    if chat.media_base == "":
        chat.media_base = "media/"


def process_exported_chat(args, data: ChatCollection) -> None:
    """Process an exported chat file."""
    exported_handler.messages(
        args.exported,
        data,
        args.assume_first_as_me,
        args.prompt_user,
    )

    copy_exported_media(
        args.exported,
        data,
        args.output,
        workers=args.copy_workers,
    )

    if not args.no_html:
        # Detect platform and use appropriate HTML generator
        platform_detected = _detect_platform_from_data(data)

        if platform_detected == "ios" and hasattr(ios_handler, "create_html"):
            logger.info("Using iOS-optimized HTML generation for exported chat")
            ios_handler.create_html(
                data,
                args.output,
                args.template,
                args.embedded,
                args.offline,
                args.size,
                args.no_avatar,
                args.whatsapp_theme,
                args.headline,
                args.separate_by_type,
            )
        else:
            # Use Android handler for Android, exported, or fallback
            logger.info(
                f"Using Android-compatible HTML generation for exported chat (platform: {platform_detected})"
            )
            android_handler.create_html(
                data,
                args.output,
                args.template,
                args.embedded,
                args.offline,
                args.size,
                args.no_avatar,
                args.whatsapp_theme,
                args.headline,
                args.separate_by_type,
            )


@log_performance
def run(args, parser) -> None:
    """Execute the export process with parsed arguments."""
    logger = get_logger(__name__)
    security_logger = get_security_logger()
    temp_dirs: List[str] = []

    with log_operation("whatsapp_export", output_dir=args.output):
        logger.info("Starting WhatsApp Chat Export process")

        auto_detect_backup(args, temp_dirs)

        # Check for updates
        if args.check_update:
            logger.info("Checking for updates")
            sys.exit(check_update(allow_network=True))

        # Validate arguments
        logger.debug("Validating arguments")
        validate_args(parser, args)

        # Create output directory with security validation
        try:
            output_path = SecurePathValidator.validate_path(args.output)
            output_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Output directory created/validated: {output_path}")
        except (PathTraversalError, ValueError) as e:
            security_logger.error(
                f"Invalid output path detected: {args.output}", extra={"error": str(e)}
            )
            raise

    # Initialize data collection
    data = ChatCollection()

    # Set up contact store for vCard enrichment if needed
    contact_store = setup_contact_store(args)

    if args.import_json:
        # Import from JSON
        import_from_json(args.json, data)

        # Detect platform and use appropriate HTML generator
        platform_detected = _detect_platform_from_data(data)

        if platform_detected == "ios" and hasattr(ios_handler, "create_html"):
            logger.info("Using iOS-optimized HTML generation for JSON import")
            ios_handler.create_html(
                data,
                args.output,
                args.template,
                args.embedded,
                args.offline,
                args.size,
                args.no_avatar,
                args.whatsapp_theme,
                args.headline,
                args.separate_by_type,
            )
        else:
            # Use Android handler for Android, exported, or fallback
            logger.info(
                f"Using Android-compatible HTML generation for JSON import (platform: {platform_detected})"
            )
            android_handler.create_html(
                data,
                args.output,
                args.template,
                args.embedded,
                args.offline,
                args.size,
                args.no_avatar,
                args.whatsapp_theme,
                args.headline,
                args.separate_by_type,
            )
    elif args.exported:
        # Process exported chat
        process_exported_chat(args, data)
    else:
        # Process Android or iOS data
        if args.android:
            # Set default media path if not provided
            if args.media is None:
                args.media = "WhatsApp"

            # Set default DB paths if not provided
            if args.db is None:
                args.db = "msgstore.db"
            if args.wa is None:
                args.wa = "wa.db"

            # Decrypt backup if needed
            if args.key is not None:
                error = decrypt_android_backup(args)
                if error != 0:
                    handle_decrypt_error(error)
        elif args.ios:
            # Set up identifiers based on business flag
            if args.business:
                from Whatsapp_Chat_Exporter.utility import (
                    WhatsAppBusinessIdentifier as identifiers,
                )
            else:
                from Whatsapp_Chat_Exporter.utility import (
                    WhatsAppIdentifier as identifiers,
                )
            args.identifiers = identifiers

            # Set default media path if not provided
            if args.media is None:
                args.media = identifiers.DOMAIN

            # Extract media from backup if needed
            if args.backup is not None:
                backup_path = args.backup
                if os.path.isfile(backup_path) and (
                    zipfile.is_zipfile(backup_path) or tarfile.is_tarfile(backup_path)
                ):
                    backup_path = extract_archive(backup_path)
                    temp_dirs.append(backup_path)

                if not os.path.isdir(args.media):
                    ios_media_handler.extract_media(
                        backup_path, identifiers, args.decrypt_chunk_size
                    )
                else:
                    logger.info(
                        "WhatsApp directory already exists, skipping WhatsApp file extraction."
                    )

            # Set default DB paths if not provided
            if args.db is None:
                args.db = identifiers.MESSAGE
            if args.wa is None:
                args.wa = "ContactsV2.sqlite"

        # Process contacts
        process_contacts(args, data, contact_store)

        # Process messages, media, and calls
        process_messages(args, data)

        # Create output files
        create_output_files(args, data, contact_store)

        # Handle media directory
        handle_media_directory(args, temp_dirs)
        report_resource_usage("After media handling")

    logger.info("Everything is done!")
    report_resource_usage("Final")

    # Clean up optimization resources
    cleanup_optimizations()

    for tmp in temp_dirs:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> None:
    """Entry point for console scripts."""
    parser = setup_argument_parser()
    args = parser.parse_args()

    # Set up comprehensive logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level=log_level, verbose=args.verbose)

    logger = get_logger(__name__)
    logger.info("WhatsApp Chat Exporter starting")

    try:
        run(args, parser)
    except Exception as e:
        logger.error(f"Application failed with error: {e}", exc_info=True)
        raise
