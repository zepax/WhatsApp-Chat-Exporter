import os
import shutil
from types import SimpleNamespace
from Whatsapp_Chat_Exporter.__main__ import handle_media_directory


def test_handle_media_skip(monkeypatch, tmp_path):
    media = tmp_path / "media"
    out = tmp_path / "out"
    media.mkdir()
    out.mkdir()
    args = SimpleNamespace(media=str(media), output=str(out), move_media=False,
                           skip_media=True, cleanup_temp=False)
    called = {"copy": False, "move": False}

    def fake_copy(src, dst):
        called["copy"] = True

    def fake_move(src, dst):
        called["move"] = True

    monkeypatch.setattr(shutil, "copytree", fake_copy)
    monkeypatch.setattr(shutil, "move", fake_move)

    handle_media_directory(args)
    assert not called["copy"]
    assert not called["move"]


def test_handle_media_cleanup(monkeypatch, tmp_path):
    media = tmp_path / "media"
    out = tmp_path / "out"
    media.mkdir()
    out.mkdir()
    args = SimpleNamespace(media=str(media), output=str(out), move_media=False,
                           skip_media=False, cleanup_temp=True)

    def fake_copy(src, dst):
        os.makedirs(dst, exist_ok=True)

    monkeypatch.setattr(shutil, "copytree", fake_copy)

    handle_media_directory(args)
    assert not media.exists()
