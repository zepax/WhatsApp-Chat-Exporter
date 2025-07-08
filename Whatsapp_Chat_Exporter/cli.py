"""Lightweight Typer wrapper for the legacy argparse interface."""

import typer

from . import __main__

app = typer.Typer(help="WhatsApp Chat Exporter")


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    add_help_option=False,
)
def export(ctx: typer.Context) -> None:
    """Forward all arguments to the argparse parser."""
    parser = __main__.setup_argument_parser()
    if any(opt in ctx.args for opt in ("--help", "-h")):
        parser.print_help()
        raise typer.Exit()
    args = parser.parse_args(list(ctx.args))
    __main__.run(args, parser)


if __name__ == "__main__":
    app()
