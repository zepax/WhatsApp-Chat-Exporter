# from contacts_names_from_vcards import readVCardsFile

import tempfile
import os

from Whatsapp_Chat_Exporter.vcards_contacts import normalize_number, read_vcards_file


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
    pass

def test_fuzzy_match_numbers():
    pass

def test_normalize_number():
    assert normalize_number('0531234567', '1') == '1531234567'
    assert normalize_number('001531234567', '2') == '1531234567'
    assert normalize_number('+1531234567', '34') == '1531234567'
    assert normalize_number('053(123)4567', '34') == '34531234567'
    assert normalize_number('0531-234-567', '58') == '58531234567'
