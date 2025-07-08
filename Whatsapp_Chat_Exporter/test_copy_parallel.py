import os
from Whatsapp_Chat_Exporter.utility import copy_parallel


def test_copy_parallel(tmp_path):
    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    src_dir.mkdir()
    dst_dir.mkdir()
    pairs = []
    for i in range(3):
        src = src_dir / f"f{i}.txt"
        dst = dst_dir / f"f{i}.txt"
        src.write_text(str(i))
        pairs.append((str(src), str(dst)))
    copy_parallel(pairs, workers=2)
    for _, dst in pairs:
        assert os.path.exists(dst)
        with open(dst) as f:
            assert f.read() in {"0", "1", "2"}
