import os
import shutil
import zipfile
import tarfile
from Whatsapp_Chat_Exporter.utility import extract_archive


def _create_sample_files(base_dir):
    base = base_dir / "src"
    base.mkdir()
    file_path = base / "foo.txt"
    file_path.write_text("hello")
    return file_path


def test_extract_zip(tmp_path):
    file_path = _create_sample_files(tmp_path)
    archive = tmp_path / "backup.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.write(file_path, file_path.name)
    out_dir = extract_archive(str(archive))
    extracted = os.path.join(out_dir, "foo.txt")
    try:
        assert os.path.isfile(extracted)
        with open(extracted) as f:
            assert f.read() == "hello"
    finally:
        shutil.rmtree(out_dir)


def test_extract_tar(tmp_path):
    file_path = _create_sample_files(tmp_path)
    archive = tmp_path / "backup.tar.gz"
    with tarfile.open(archive, "w:gz") as tf:
        tf.add(file_path, arcname=file_path.name)
    out_dir = extract_archive(str(archive))
    extracted = os.path.join(out_dir, "foo.txt")
    try:
        assert os.path.isfile(extracted)
        with open(extracted) as f:
            assert f.read() == "hello"
    finally:
        shutil.rmtree(out_dir)
