from __future__ import annotations

import os
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Tuple

from .utility import Device

__all__ = ["detect"]


def _extract_archive(path: str) -> str:
    temp_dir = tempfile.mkdtemp()
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            zf.extractall(temp_dir)
    elif tarfile.is_tarfile(path):
        with tarfile.open(path) as tf:
            tf.extractall(temp_dir)
    return temp_dir


def _search(root: str, names: Tuple[str, ...]) -> str | None:
    for base, _, files in os.walk(root):
        for name in names:
            if name in files:
                return os.path.join(base, name)
    return None


def detect(path: str) -> Tuple[Device | None, str]:
    """Detect backup type and return device and working path.

    If ``path`` is an archive, it will be extracted to a temporary directory.
    The returned path is either the original path or the extracted directory.
    """
    working = path
    if os.path.isfile(path) and (zipfile.is_zipfile(path) or tarfile.is_tarfile(path)):
        working = _extract_archive(path)

    if os.path.isdir(working):
        if _search(working, ("Manifest.db",)):
            return Device.IOS, working
        if _search(
            working,
            (
                "msgstore.db",
                "msgstore.db.crypt12",
                "msgstore.db.crypt14",
                "msgstore.db.crypt15",
            ),
        ):
            return Device.ANDROID, working
    else:
        name = Path(working).name.lower()
        if name in {
            "msgstore.db",
            "msgstore.db.crypt12",
            "msgstore.db.crypt14",
            "msgstore.db.crypt15",
        }:
            return Device.ANDROID, working
        if name == "chatstorage.sqlite":
            return Device.IOS, working

    return None, working
