import typer
from pathlib import Path
from typing import Optional

from . import __main__

app = typer.Typer(help="WhatsApp Chat Exporter")


@app.command()
def export(
    android: bool = typer.Option(False, "--android", "-a", help="Target is Android"),
    ios: bool = typer.Option(False, "--ios", "-i", help="Target is iPhone/iPad"),
    exported: Optional[Path] = typer.Option(None, "--exported", "-e", help="Chat export file"),
    backup: Optional[Path] = typer.Option(None, "--backup", help="Backup file"),
    wa: Optional[Path] = typer.Option(None, "--wa", help="Contacts database"),
    media: Optional[Path] = typer.Option(None, "--media", help="Media directory"),
    db: Optional[Path] = typer.Option(None, "--db", help="Message database"),
    output: Path = typer.Option(Path("result"), "--output", "-o", help="Output directory"),
    json: Optional[Path] = typer.Option(None, "--json", "-j", help="Save chats to JSON"),
) -> None:
    """Export WhatsApp chats."""
    parser = __main__.setup_argument_parser()
    args = parser.parse_args([])
    args.android = android
    args.ios = ios
    args.exported = str(exported) if exported else None
    args.backup = str(backup) if backup else None
    args.wa = str(wa) if wa else None
    args.media = str(media) if media else None
    args.db = str(db) if db else None
    args.output = str(output)
    args.json = str(json) if json else None
    __main__.run(args, parser)


if __name__ == "__main__":
    app()

