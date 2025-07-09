# from contacts_names_from_vcards import readVCardsFile

import os
import tempfile

from Whatsapp_Chat_Exporter.vcards_contacts import (
    filter_chats_by_prefix,
    map_number_to_name,
    normalize_number,
    read_vcards_file,
)


def test_readVCardsFile():
    sample_vcf = """BEGIN:VCARD\nFN:John Doe\nTEL:+1234567890\nEND:VCARD\n"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
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


def test_fuzzy_match_numbers():
    chats = {
        "1234567890": object(),
        "12345": object(),
        "987654321": object(),
    }
    filtered = filter_chats_by_prefix(chats, "123")
    assert set(filtered.keys()) == {"1234567890", "12345"}


def test_normalize_number():
    assert normalize_number("0531234567", "1") == "1531234567"
    assert normalize_number("001531234567", "2") == "1531234567"
    assert normalize_number("+1531234567", "34") == "1531234567"
    assert normalize_number("053(123)4567", "34") == "34531234567"
    assert normalize_number("0531-234-567", "58") == "58531234567"
    assert normalize_number("0531234567", "") == "531234567"
    assert normalize_number("0531-234-567", "") == "531234567"
