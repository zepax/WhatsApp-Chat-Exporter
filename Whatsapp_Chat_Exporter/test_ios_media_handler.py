<<<<<<< HEAD
import os
import sqlite3
from plistlib import dumps, FMT_BINARY
from Whatsapp_Chat_Exporter import ios_media_handler
from Whatsapp_Chat_Exporter.utility import WhatsAppIdentifier


def _make_manifest(path: str, rows: list[tuple[str, str, int]]) -> None:
    metadata = dumps({"$objects": [None, {"Birth": 0, "LastModified": 0}]}, fmt=FMT_BINARY)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE Files (fileID TEXT, domain TEXT, relativePath TEXT, flags INTEGER, file BLOB)"
        )
        for file_id, rel_path, flags in rows:
            conn.execute(
                "INSERT INTO Files VALUES (?, ?, ?, ?, ?)",
                (file_id, WhatsAppIdentifier.DOMAIN, rel_path, flags, metadata),
            )
        conn.commit()


def test_extract_media_files_traversal(monkeypatch, tmp_path):
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    good_hash = "aa1111"
    bad_hash = "bb2222"
    abs_hash = "cc3333"
    for h in (good_hash, bad_hash, abs_hash):
        d = base_dir / h[:2]
        d.mkdir(exist_ok=True)
        (d / h).write_text(h)
    _make_manifest(
        base_dir / "Manifest.db",
        [
            ("dir000", "safe", 2),
            (good_hash, "safe/good.txt", 1),
            (bad_hash, "../evil.txt", 1),
            (abs_hash, "/abs.txt", 1),
        ],
    )
    work_dir = tmp_path / "wd"
    work_dir.mkdir()
    monkeypatch.chdir(work_dir)

    extractor = ios_media_handler.BackupExtractor(
        str(base_dir), WhatsAppIdentifier, decrypt_chunk_size=1024
    )
    extractor._extract_media_files()

    out_root = work_dir / WhatsAppIdentifier.DOMAIN
    assert (out_root / "safe" / "good.txt").is_file()
    assert not (work_dir / "evil.txt").exists()
    assert not (work_dir / "abs.txt").exists()

=======
import os
import sqlite3
from plistlib import dumps, FMT_BINARY
from Whatsapp_Chat_Exporter import ios_media_handler
from Whatsapp_Chat_Exporter.utility import WhatsAppIdentifier


def _make_manifest(path: str, rows: list[tuple[str, str, int]]) -> None:
    metadata = dumps({"$objects": [None, {"Birth": 0, "LastModified": 0}]}, fmt=FMT_BINARY)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE Files (fileID TEXT, domain TEXT, relativePath TEXT, flags INTEGER, file BLOB)"
        )
        for file_id, rel_path, flags in rows:
            conn.execute(
                "INSERT INTO Files VALUES (?, ?, ?, ?, ?)",
                (file_id, WhatsAppIdentifier.DOMAIN, rel_path, flags, metadata),
            )
        conn.commit()


def test_extract_media_files_traversal(monkeypatch, tmp_path):
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    good_hash = "aa1111"
    bad_hash = "bb2222"
    abs_hash = "cc3333"
    for h in (good_hash, bad_hash, abs_hash):
        d = base_dir / h[:2]
        d.mkdir(exist_ok=True)
        (d / h).write_text(h)
    _make_manifest(
        base_dir / "Manifest.db",
        [
            ("dir000", "safe", 2),
            (good_hash, "safe/good.txt", 1),
            (bad_hash, "../evil.txt", 1),
            (abs_hash, "/abs.txt", 1),
        ],
    )
    work_dir = tmp_path / "wd"
    work_dir.mkdir()
    monkeypatch.chdir(work_dir)

    extractor = ios_media_handler.BackupExtractor(
        str(base_dir), WhatsAppIdentifier, decrypt_chunk_size=1024
    )
    extractor._extract_media_files()

    out_root = work_dir / WhatsAppIdentifier.DOMAIN
    assert (out_root / "safe" / "good.txt").is_file()
    assert not (work_dir / "evil.txt").exists()
    assert not (work_dir / "abs.txt").exists()

>>>>>>> 0b087d242fb332e1e94c87caa74b2b5dc3ef79a0
