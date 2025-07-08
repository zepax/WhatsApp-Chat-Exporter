from Whatsapp_Chat_Exporter.bplist import BPListWriter, BPListReader


def test_binary_roundtrip():
    obj = {"a": 1, "b": [1, 2, 3], "c": {"d": True}}
    writer = BPListWriter(obj)
    data = writer.binary()
    assert data.startswith(b"bplist00")
    parsed = BPListReader(data).parse()
    assert parsed == obj


def test_write(tmp_path):
    obj = {"x": "y"}
    writer = BPListWriter(obj)
    writer.binary()
    path = tmp_path / "test.plist"
    writer.write(path)
    with open(path, "rb") as f:
        read_data = f.read()
    assert read_data == writer.bplist
    assert BPListReader(read_data).parse() == {"x": b"y"}
from Whatsapp_Chat_Exporter.bplist import BPListWriter, BPListReader


