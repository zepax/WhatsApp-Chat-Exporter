import importlib.metadata
from Whatsapp_Chat_Exporter.__main__ import setup_argument_parser, validate_args
import pytest


def _parser(monkeypatch):
    monkeypatch.setattr(importlib.metadata, "version", lambda name: "0.0.0")
    return setup_argument_parser()


def test_backup_not_found(tmp_path, capsys, monkeypatch):
    parser = _parser(monkeypatch)
    key = tmp_path / "key"
    key.write_text("dummy")
    (tmp_path / "msg.db").touch()
    (tmp_path / "wa.db").touch()
    args = parser.parse_args(
        [
            "-a",
            "--db",
            str(tmp_path / "msg.db"),
            "--wa",
            str(tmp_path / "wa.db"),
            "-b",
            str(tmp_path / "missing.crypt15"),
            "-k",
            str(key),
        ]
    )
    with pytest.raises(SystemExit):
        validate_args(parser, args)
    err = capsys.readouterr().err
    assert "Backup file not found" in err


def test_key_required_for_backup(tmp_path, capsys, monkeypatch):
    parser = _parser(monkeypatch)
    backup = tmp_path / "chat.crypt15"
    backup.touch()
    (tmp_path / "msg.db").touch()
    (tmp_path / "wa.db").touch()
    args = parser.parse_args(
        [
            "-a",
            "--db",
            str(tmp_path / "msg.db"),
            "--wa",
            str(tmp_path / "wa.db"),
            "-b",
            str(backup),
        ]
    )
    with pytest.raises(SystemExit):
        validate_args(parser, args)
    err = capsys.readouterr().err
    assert "Encryption key needed" in err
