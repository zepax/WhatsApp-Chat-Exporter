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
    input_json: str,
    output_json: str,
    remove_empty: bool = True,
    deduplicate: bool = True,
) -> None:
    """Clean chats from a JSON export."""
    from .chat_cleaner import ChatCleaner
    from .data_model import ChatCollection, ChatStore, Message
    import json

    with open(input_json, "r") as f:
        raw = json.load(f)

    collection = ChatCollection()
    for chat_id, chat_data in raw.items():
        chat = ChatStore(chat_data.get("type", "android"), name=chat_data.get("name"))
        for msg_id, msg_data in chat_data.get("messages", {}).items():
            msg = Message(
                from_me=msg_data.get("from_me", 0),
                timestamp=msg_data.get("timestamp", 0),
                time=msg_data.get("time", 0),
                key_id=msg_data.get("key_id", 0),
                received_timestamp=0,
                read_timestamp=0,
            )
            msg.data = msg_data.get("data")
            msg.media = msg_data.get("media", False)
            msg.meta = msg_data.get("meta", False)
            msg.sender = msg_data.get("sender")
            chat.add_message(msg_id, msg)
        collection.add_chat(chat_id, chat)

    ChatCleaner.clean(collection, remove_empty, deduplicate)

    with open(output_json, "w") as f:
        json.dump(collection.to_dict(), f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    app()
