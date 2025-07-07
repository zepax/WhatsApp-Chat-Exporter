import os
import shutil
from types import SimpleNamespace
from Whatsapp_Chat_Exporter.__main__ import handle_media_directory


def test_handle_media_skip(monkeypatch, tmp_path):
    media = tmp_path / "media"
    out = tmp_path / "out"
    media.mkdir()
    out.mkdir()
    args = SimpleNamespace(
        media=str(media),
        output=str(out),
        move_media=False,
        skip_media=True,
        cleanup_temp=False,
    )
    called = {"copy": False, "move": False}

    def fake_copy(src, dst):
        called["copy"] = True

    def fake_move(src, dst):
        called["move"] = True

    monkeypatch.setattr(shutil, "copytree", fake_copy)
    monkeypatch.setattr(shutil, "move", fake_move)

    handle_media_directory(args, [str(tmp_path)])
    assert not called["copy"]
    assert not called["move"]


def test_handle_media_cleanup(monkeypatch, tmp_path):
    media = tmp_path / "media"
    out = tmp_path / "out"
    media.mkdir()
    out.mkdir()
    args = SimpleNamespace(
        media=str(media),
        output=str(out),
        move_media=False,
        skip_media=False,
        cleanup_temp=True,
    )

    def fake_copy(src, dst):
        os.makedirs(dst, exist_ok=True)

    monkeypatch.setattr(shutil, "copytree", fake_copy)

    handle_media_directory(args, [str(tmp_path)])
    assert not media.exists()


def test_handle_media_sanitizes_path(monkeypatch, tmp_path):
    base = tmp_path / "base"
    sub = base / "sub"
    out = tmp_path / "out"
    evil = base / "evil"
    base.mkdir()
    sub.mkdir()
    evil.mkdir()
    out.mkdir()
    path_with_parent = sub / ".." / "evil"
    args = SimpleNamespace(
        media=str(path_with_parent) + os.sep,
        output=str(out),
        move_media=False,
        skip_media=False,
        cleanup_temp=False,
    )
    called = {}

    def fake_copy(src, dst):
        called["src"] = src
        called["dst"] = dst

    monkeypatch.setattr(shutil, "copytree", fake_copy)

    handle_media_directory(args, [str(base)])
    assert called["src"] == str(path_with_parent) + os.sep
    assert called["dst"] == os.path.join(str(out), "evil")
