import pytest

from Whatsapp_Chat_Exporter import ios_media_handler
from Whatsapp_Chat_Exporter.utility import get_chat_condition, WhatsAppIdentifier


def test_get_chat_condition_rejects_invalid():
    with pytest.raises(ValueError):
        get_chat_condition(["1' OR '1'='1"], True, ["jid"], "jid", "android")


def test_copy_whatsapp_db_missing(tmp_path):
    extractor = ios_media_handler.BackupExtractor(
        str(tmp_path), WhatsAppIdentifier, 1024
    )
    with pytest.raises(ios_media_handler.IOSMediaError) as exc:
        extractor._copy_whatsapp_databases()
    assert exc.value.code == 1
