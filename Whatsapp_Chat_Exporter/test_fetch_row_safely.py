import sqlite3
import pytest

from Whatsapp_Chat_Exporter.android_handler import _fetch_row_safely


class FakeCursor:
    def __init__(self, fail_times=0):
        self.fail_times = fail_times
        self.calls = 0

    def fetchone(self):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise sqlite3.OperationalError("locked")
        return {"ok": True}


def test_fetch_row_safely_success():
    cursor = FakeCursor(fail_times=2)
    row = _fetch_row_safely(cursor, max_retries=5, delay=0)
    assert row == {"ok": True}
    assert cursor.calls == 3


def test_fetch_row_safely_exceeds_retries():
    cursor = FakeCursor(fail_times=3)
    with pytest.raises(sqlite3.OperationalError):
        _fetch_row_safely(cursor, max_retries=2, delay=0)
