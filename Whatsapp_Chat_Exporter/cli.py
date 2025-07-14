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


@app.command()
def clean(
    input_file: str,
    output_file: str = None,
    remove_duplicates: bool = True,
    duplicate_threshold: int = 60,
    remove_system: bool = False,
    anonymize_names: bool = False,
    anonymize_phones: bool = False,
    anonymize_emails: bool = False,
    output_format: str = None,
    start_date: str = None,
    end_date: str = None,
    create_backup: bool = True,
    verbose: bool = False,
) -> None:
    """Clean and process WhatsApp chat exports with advanced features."""
    from .chat_cleaner import ChatCleaner, CleaningConfig, parse_date

    # Parse dates if provided
    start_datetime = parse_date(start_date) if start_date else None
    end_datetime = parse_date(end_date) if end_date else None

    # Create configuration
    config = CleaningConfig(
        remove_duplicates=remove_duplicates,
        duplicate_threshold_seconds=duplicate_threshold,
        start_date=start_datetime,
        end_date=end_datetime,
        remove_system_messages=remove_system,
        anonymize_names=anonymize_names,
        anonymize_phones=anonymize_phones,
        anonymize_emails=anonymize_emails,
        create_backup=create_backup,
        output_format=output_format or "json",
    )

    # Initialize and run cleaner
    cleaner = ChatCleaner(config)
    success = cleaner.clean_file(input_file, output_file)

    if verbose or not success:
        cleaner.print_summary()

    if not success:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
