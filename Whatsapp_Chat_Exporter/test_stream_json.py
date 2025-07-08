import json
from types import SimpleNamespace
from Whatsapp_Chat_Exporter.__main__ import export_single_json, export_single_json_stream


def create_sample_dict():
    return {"chat": {"name": "Test", "messages": {"1": {"data": "hi"}}}}


def test_streaming_json(tmp_path):
    data = create_sample_dict()
    std = tmp_path / "std.json"
    stream = tmp_path / "stream.json"
    args = SimpleNamespace(json=str(std), avoid_encoding_json=False, pretty_print_json=None)
    export_single_json(args, data)
    args.json = str(stream)
    export_single_json_stream(args, data)
    with open(std) as f1, open(stream) as f2:
        assert json.load(f1) == json.load(f2)
