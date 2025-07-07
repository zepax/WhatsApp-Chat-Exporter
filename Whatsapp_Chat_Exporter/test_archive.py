import os
import shutil
import zipfile
import tarfile
import io
import pytest
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


def _create_bad_tar(tmp_path, name: str):
    tar_path = tmp_path / "bad.tar"
    with tarfile.open(tar_path, "w") as tf:
        info = tarfile.TarInfo(name)
        data = b"bad"
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    return tar_path


@pytest.mark.parametrize("member", ["../evil.txt", "/abs.txt", "foo/../../bar"])
def test_extract_tar_unsafe(tmp_path, member):
    archive = _create_bad_tar(tmp_path, member)
    with pytest.raises(ValueError):
        extract_archive(str(archive))
