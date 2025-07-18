import concurrent.futures
import hmac
import io
import logging
import zlib
from hashlib import sha256
from typing import Tuple, Union

from Whatsapp_Chat_Exporter.utility import CRYPT14_OFFSETS, Crypt, DbType

logger = logging.getLogger(__name__)

try:
    from Crypto.Cipher import AES
except ModuleNotFoundError:
    support_backup = False
else:
    support_backup = True

try:
    import javaobj
except ModuleNotFoundError:
    support_crypt15 = False
else:
    support_crypt15 = True


class DecryptionError(Exception):
    """Base class for decryption-related exceptions.

    This exception indicates a general failure in the decryption process.
    More specific error types should be used when the failure cause is known.
    """

    def __init__(
        self, message: str = "Decryption failed", original_error: Exception = None
    ):
        super().__init__(message)
        self.original_error = original_error


class InvalidKeyError(DecryptionError):
    """Raised when the provided key is invalid.

    This typically occurs when:
    - The key file is corrupted or has wrong format
    - The key doesn't match the encrypted backup
    - The key size is incorrect (not 158 bytes for crypt12/14)
    """

    def __init__(self, message: str = "Invalid encryption key provided"):
        super().__init__(message)


class InvalidFileFormatError(DecryptionError):
    """Raised when the input file format is invalid.

    This occurs when:
    - The backup file is too small or corrupted
    - The file doesn't match expected crypt12/14/15 format
    - Required headers or signatures are missing
    """

    def __init__(self, message: str = "Invalid backup file format"):
        super().__init__(message)


class OffsetNotFoundError(DecryptionError):
    """Raised when the correct offsets for decryption cannot be found.

    This happens when:
    - The backup file uses unknown IV and database start offsets
    - Brute force offset detection fails
    - The file structure doesn't match any known patterns

    Consider reporting new offset patterns to help improve the tool.
    """

    def __init__(self, message: str = "Could not determine correct decryption offsets"):
        super().__init__(message)


class BruteForceInterrupted(DecryptionError):
    """Raised when brute force decryption is interrupted by the user.

    This is a normal exception that occurs when the user presses Ctrl+C
    during the brute force offset detection process.
    """

    def __init__(self, message: str = "Brute force decryption was interrupted by user"):
        super().__init__(message)


def _derive_main_enc_key(key_stream: bytes) -> Tuple[bytes, bytes]:
    """
    Derive the main encryption key for the given key stream.

    Args:
        key_stream (bytes): The key stream to generate HMAC of HMAC.

    Returns:
        Tuple[bytes, bytes]: A tuple containing the main encryption key and the original key stream.
    """
    intermediate_hmac = hmac.new(b"\x00" * 32, key_stream, sha256).digest()
    key = hmac.new(intermediate_hmac, b"backup encryption\x01", sha256).digest()
    return key, key_stream


def _extract_enc_key(keyfile: bytes) -> Tuple[bytes, bytes]:
    """
    Extract the encryption key from the keyfile.

    Args:
        keyfile (bytes): The keyfile containing the encrypted key.

    Returns:
        Tuple[bytes, bytes]: values from _derive_main_enc_key()
    """
    key_stream = b"".join(
        [byte.to_bytes(1, "big", signed=True) for byte in javaobj.loads(keyfile)]
    )
    return _derive_main_enc_key(key_stream)


def brute_force_offset(max_iv: int = 200, max_db: int = 200):
    """
    Brute force the offsets for IV and database start position in WhatsApp backup files.

    Args:
        max_iv (int, optional): Maximum value to try for IV offset. Defaults to 200.
        max_db (int, optional): Maximum value to try for database start offset. Defaults to 200.

    Yields:
        tuple: A tuple containing:
            - int: Start position of IV
            - int: End position of IV (start + 16)
            - int: Start position of database
    """
    for iv in range(0, max_iv):
        for db in range(0, max_db):
            yield iv, iv + 16, db


def _decrypt_database(db_ciphertext: bytes, main_key: bytes, iv: bytes) -> bytes:
    """Decrypt and decompress a database chunk.

    Args:
        db_ciphertext (bytes): The encrypted chunk of the database.
        main_key (bytes): The main decryption key.
        iv (bytes): The initialization vector.

    Returns:
        bytes: The decrypted and decompressed database.

    Raises:
        zlib.error: If decompression fails.
        ValueError: if the plaintext is not a SQLite database.
    """
    cipher = AES.new(main_key, AES.MODE_GCM, iv)
    db_compressed = cipher.decrypt(db_ciphertext)
    db = zlib.decompress(db_compressed)
    if db[0:6].upper() != b"SQLITE":
        raise ValueError(
            "The plaintext is not a SQLite database. Ensure you are using the correct key."
        )
    return db


def _decrypt_crypt14(database: bytes, main_key: bytes, max_worker: int = 10) -> bytes:
    """Decrypt a crypt14 database using multithreading for brute-force offset detection.

    Args:
        database (bytes): The encrypted database.
        main_key (bytes): The decryption key.
        max_worker (int, optional): The maximum number of threads to use for brute force. Defaults to 10.

    Returns:
        bytes: The decrypted database.

    Raises:
        InvalidFileFormatError: If the file is too small.
        OffsetNotFoundError: If no valid offsets are found.
    """
    if len(database) < 191:
        raise InvalidFileFormatError("The crypt14 file must be at least 191 bytes")

    # Attempt known offsets first
    for offsets in CRYPT14_OFFSETS:
        iv = database[offsets["iv"] : offsets["iv"] + 16]
        db_ciphertext = database[offsets["db"] :]
        try:
            return _decrypt_database(db_ciphertext, main_key, iv)
        except (zlib.error, ValueError):
            pass  # Try next offset

    logger.info("Common offsets failed. Initiating brute-force with multithreading...")

    # Convert brute force generator into a list for parallel processing
    offset_combinations = list(brute_force_offset())

    def attempt_decrypt(offset_tuple):
        """Attempt decryption with the given offsets."""
        start_iv, end_iv, start_db = offset_tuple
        iv = database[start_iv:end_iv]
        db_ciphertext = database[start_db:]

        try:
            db = _decrypt_database(db_ciphertext, main_key, iv)
            logger.info(
                "The offsets of your IV and database are %s and %s, "
                "respectively. To include your offsets in the program, "
                "please report it by creating an issue on GitHub: "
                "https://github.com/KnugiHK/Whatsapp-Chat-Exporter/discussions/47"
                "\nShutting down other threads...",
                start_iv,
                start_db,
            )
            return db
        except (zlib.error, ValueError):
            return None  # Decryption failed, move to next

    with concurrent.futures.ThreadPoolExecutor(max_worker) as executor:
        future_to_offset = {
            executor.submit(attempt_decrypt, offset): offset
            for offset in offset_combinations
        }

        try:
            for future in concurrent.futures.as_completed(future_to_offset):
                result = future.result()
                if result is not None:
                    # Shutdown remaining threads
                    executor.shutdown(wait=False, cancel_futures=True)
                    return result

        except KeyboardInterrupt:
            logger.warning(
                "Brute force interrupted by user (Ctrl+C). Exiting gracefully..."
            )
            executor.shutdown(wait=False, cancel_futures=True)
            raise BruteForceInterrupted("Brute force interrupted by user")

    raise OffsetNotFoundError("Could not find the correct offsets for decryption.")


def _decrypt_crypt12(database: bytes, main_key: bytes) -> bytes:
    """Decrypt a crypt12 database.

    Args:
        database (bytes): The encrypted database.
        main_key (bytes): The decryption key.

    Returns:
        bytes: The decrypted database.

    Raises:
        ValueError: If the file format is invalid or the signature mismatches.
    """
    if len(database) < 67:
        raise InvalidFileFormatError("The crypt12 file must be at least 67 bytes")

    _t2 = database[3:35]
    iv = database[51:67]
    db_ciphertext = database[67:-20]
    return _decrypt_database(db_ciphertext, main_key, iv)


def _decrypt_crypt15(database: bytes, main_key: bytes, db_type: DbType) -> bytes:
    """Decrypt a crypt15 database.

    Args:
        database (bytes): The encrypted database.
        main_key (bytes): The decryption key.
        db_type (DbType): The type of database.

    Returns:
        bytes: The decrypted database.

    Raises:
        ValueError: If the file format is invalid or the signature mismatches.
    """
    if not support_crypt15:
        raise RuntimeError("Crypt15 is not supported")
    if len(database) < 131:
        raise InvalidFileFormatError("The crypt15 file must be at least 131 bytes")

    if db_type == DbType.MESSAGE:
        iv = database[8:24]
        db_offset = database[0] + 2
    elif db_type == DbType.CONTACT:
        iv = database[7:23]
        db_offset = database[0] + 1
    else:
        raise ValueError(f"Invalid db_type: {db_type}")

    db_ciphertext = database[db_offset:]
    return _decrypt_database(db_ciphertext, main_key, iv)


def decrypt_backup(
    database: bytes,
    key: Union[str, io.IOBase],
    output: str = None,
    crypt: Crypt = Crypt.CRYPT14,
    show_crypt15: bool = False,
    db_type: DbType = DbType.MESSAGE,
    *,
    dry_run: bool = False,
    keyfile_stream: bool = False,
    max_worker: int = 10,
) -> int:
    """
    Decrypt the WhatsApp backup database.

    Args:
        database (bytes): The encrypted database file.
        key (str or io.IOBase): The key to decrypt the database.
        output (str, optional): The path to save the decrypted database. Defaults to None.
        crypt (Crypt, optional): The encryption version of the database. Defaults to Crypt.CRYPT14.
        show_crypt15 (bool, optional): Whether to show the HEX key of the crypt15 backup. Defaults to False.
        db_type (DbType, optional): The type of database (MESSAGE or CONTACT). Defaults to DbType.MESSAGE.
        dry_run (bool, optional): Whether to perform a dry run. Defaults to False.
        keyfile_stream (bool, optional): Whether the key is a key stream. Defaults to False.

    Returns:
        int: The status code of the decryption process (0 for success).

    Raises:
        ValueError: If the key is invalid or output file not provided when dry_run is False.
        DecryptionError: for errors during decryption
        RuntimeError: for dependency errors
    """
    if not support_backup:
        raise RuntimeError("Dependencies for backup decryption are not available.")

    if not dry_run and output is None:
        raise ValueError(
            "The path to the decrypted database must be specified unless dry_run is true."
        )

    if isinstance(key, io.IOBase):
        key = key.read()

    if crypt is not Crypt.CRYPT15 and len(key) != 158:
        raise InvalidKeyError("The key file must be 158 bytes")

    # signature check, this is check is used in crypt 12 and 14
    if crypt != Crypt.CRYPT15:
        t1 = key[30:62]

        if t1 != database[15:47] and crypt == Crypt.CRYPT14:
            raise ValueError("The signature of key file and backup file mismatch")

        if t1 != database[3:35] and crypt == Crypt.CRYPT12:
            raise ValueError("The signature of key file and backup file mismatch")

    if crypt == Crypt.CRYPT15:
        if keyfile_stream:
            main_key, hex_key = _extract_enc_key(key)
        else:
            main_key, hex_key = _derive_main_enc_key(key)
        if show_crypt15:
            hex_key_str = " ".join(
                [hex_key.hex()[c : c + 4] for c in range(0, len(hex_key.hex()), 4)]
            )
            logger.info("The HEX key of the crypt15 backup is: %s", hex_key_str)
    else:
        main_key = key[126:]

    try:
        if crypt == Crypt.CRYPT14:
            db = _decrypt_crypt14(database, main_key, max_worker)
        elif crypt == Crypt.CRYPT12:
            db = _decrypt_crypt12(database, main_key)
        elif crypt == Crypt.CRYPT15:
            db = _decrypt_crypt15(database, main_key, db_type)
        else:
            raise ValueError(f"Unsupported crypt type: {crypt}")
    except (InvalidFileFormatError, OffsetNotFoundError, ValueError) as e:
        raise DecryptionError(f"Decryption failed: {e}") from e

    if not dry_run:
        with open(output, "wb") as f:
            f.write(db)
    return 0
