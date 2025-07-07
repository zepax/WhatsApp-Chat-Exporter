from typer.testing import CliRunner
from Whatsapp_Chat_Exporter.cli import app


runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "export" in result.output


def test_cli_help_export():
    result = runner.invoke(app, ["export", "--help"])
    assert result.exit_code == 0
    assert "--android" in result.output
