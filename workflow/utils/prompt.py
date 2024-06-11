"""Utility functions for prompting the user for input."""

import click
from rich.console import Console

console = Console()


def confirmation(msg: str) -> bool:
    """Get confirmation from the user.

    Args:
        msg (str): Message to display to the user.

    Returns:
        bool: True if the user confirms, False otherwise.
    """
    console.print(
        "Please confirm the following action:",
        style="bold red",
        justify="center",
    )
    console.print(msg, style="magenta italic")
    # Get confirmation from the user
    confirmation = click.prompt('Type "yes" to confirm', default="no")
    return confirmation.lower() == "yes"
