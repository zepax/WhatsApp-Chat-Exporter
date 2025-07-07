import zipfile
from pathlib import Path

from Whatsapp_Chat_Exporter.backup_detector import detect
from Whatsapp_Chat_Exporter.utility import Device


def test_detect_ios_folder(tmp_path):
    (tmp_path / "Manifest.db").write_text("")
    device, path = detect(str(tmp_path))
    assert device == Device.IOS
    assert Path(path) == tmp_path


def test_detect_android_zip(tmp_path):
    inner = tmp_path / "folder"
    inner.mkdir()
    (inner / "msgstore.db").write_text("")
    zip_path = tmp_path / "backup.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(inner / "msgstore.db", "msgstore.db")
    device, path = detect(str(zip_path))
    assert device == Device.ANDROID
    assert Path(path).exists()


def test_detect_android_crypt(tmp_path):
    crypt = tmp_path / "msgstore.db.crypt14"
    crypt.write_text("")
    device, path = detect(str(crypt))
    assert device == Device.ANDROID
    assert Path(path) == crypt
