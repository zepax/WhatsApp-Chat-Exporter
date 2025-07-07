from typer.testing import CliRunner
from Whatsapp_Chat_Exporter.cli import app
import importlib.metadata
import pytest


@pytest.fixture(autouse=True)
def _fake_version(monkeypatch):
    monkeypatch.setattr(importlib.metadata, "version", lambda name: "0.0.0")


runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "export" in result.output


def test_cli_help_export():
    result = runner.invoke(app, ["export", "--help"])
    assert result.exit_code == 0
    assert "--android" in result.output
    assert "--prompt-user" in result.output
