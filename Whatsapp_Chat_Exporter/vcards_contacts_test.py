# from contacts_names_from_vcards import readVCardsFile

import tempfile
import os

from Whatsapp_Chat_Exporter.vcards_contacts import (
    normalize_number,
    read_vcards_file,
    map_number_to_name,
    filter_chats_by_prefix,
)


def test_readVCardsFile():
    sample_vcf = """BEGIN:VCARD\nFN:John Doe\nTEL:+1234567890\nEND:VCARD\n"""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp:
        tmp.write(sample_vcf)
        path = tmp.name
    try:
        result = read_vcards_file(path, "1")
        assert result == [("1234567890", "John Doe")]
    finally:
        os.unlink(path)

def test_create_number_to_name_dicts():
    contacts = [
        {"full_name": "Alice", "numbers": ["0531234567", "+1537654321"]},
        {"full_name": "Bob", "numbers": ["12345"]},
    ]
    mapping = map_number_to_name(contacts, "1")
    assert ("1531234567", "Alice (1)") in mapping
    assert ("1537654321", "Alice (2)") in mapping
    assert ("112345", "Bob") in mapping

