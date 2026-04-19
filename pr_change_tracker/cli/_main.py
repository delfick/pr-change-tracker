from __future__ import annotations

import click

from ._commands import event_processor, serve_http


@click.group(help="Interact with pr change tracker")
def main() -> None:
    pass


main.add_command(serve_http)
main.add_command(event_processor)
