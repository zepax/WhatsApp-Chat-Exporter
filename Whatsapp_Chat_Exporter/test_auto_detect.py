import os
import zipfile
from types import SimpleNamespace
from Whatsapp_Chat_Exporter.__main__ import auto_detect_backup


def _args(**kwargs):
    base = dict(
        backup=None,
        db=None,
        android=False,
        ios=False,
        exported=None,
        import_json=False,
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


def test_detect_android_crypt(tmp_path):
    path = tmp_path / "msgstore.db.crypt14"
    path.write_text("dummy")
    args = _args(backup=str(path))
    temp_dirs = []
    auto_detect_backup(args, temp_dirs)
    assert args.android and not args.ios
    assert args.backup == str(path)
    assert not temp_dirs


def test_detect_ios_archive(tmp_path):
    ios_dir = tmp_path / "ios"
    ios_dir.mkdir()
    (ios_dir / "Manifest.db").write_text("x")
    archive = tmp_path / "backup.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.write(ios_dir / "Manifest.db", "Manifest.db")
    args = _args(backup=str(archive))
    temp_dirs = []
    auto_detect_backup(args, temp_dirs)
    assert args.ios and not args.android
    assert len(temp_dirs) == 1
    assert os.path.isdir(temp_dirs[0])
    assert args.backup == temp_dirs[0]
import os
import zipfile
from types import SimpleNamespace
from Whatsapp_Chat_Exporter.__main__ import auto_detect_backup


def _args(**kwargs):
    base = dict(
        backup=None,
        db=None,
        android=False,
        ios=False,
        exported=None,
        import_json=False,
    )
    base.update(kwargs)
