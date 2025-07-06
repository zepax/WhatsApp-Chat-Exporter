import importlib
import builtins
import sys
import types

import pytest


def test_optional_import(monkeypatch):
    """ios_media_handler should handle missing dependency gracefully."""

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "iphone_backup_decrypt":
            raise ModuleNotFoundError
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    import Whatsapp_Chat_Exporter.ios_media_handler as mod
    importlib.reload(mod)
    assert mod.support_encrypted is False

    dummy = types.ModuleType("iphone_backup_decrypt")

    class DummyRelativePath:
        WHATSAPP_MESSAGES = 1
        WHATSAPP_CONTACTS = 2
        WHATSAPP_CALLS = 3

    dummy.EncryptedBackup = object
    dummy.RelativePath = DummyRelativePath
    monkeypatch.setattr(builtins, "__import__", original_import)
    monkeypatch.setitem(sys.modules, "iphone_backup_decrypt", dummy)
    importlib.reload(mod)
    assert mod.support_encrypted is True

