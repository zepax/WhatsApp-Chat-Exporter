import pytest
from Whatsapp_Chat_Exporter.utility import determine_metadata


def test_added_participant():
    content = {
        "action_type": 12,
        "is_me_joined": 0,
        "data": "bob@s.whatsapp.net",
    }
    assert determine_metadata(content, "Alice") == "Alice added bob"


def test_removed_participant():
    content = {
        "action_type": 14,
        "is_me_joined": 0,
        "data": "charlie@s.whatsapp.net",
    }
    assert determine_metadata(content, "Alice") == "Alice removed charlie"


def test_joined_via_link():
    content = {
        "action_type": 20,
        "is_me_joined": 0,
        "data": None,
    }
    assert determine_metadata(content, "Bob") == (
        "Bob joined this group by using an invite link"
    )


def test_added_fallback():
    content = {"action_type": 12, "is_me_joined": 0, "data": None}
    assert determine_metadata(content, "Alice") == "Alice added someone"
