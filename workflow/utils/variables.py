"""Variables needed for console printing."""

status_colors = {
    "active": "bright_blue",
    "running": "blue",
    "created": "lightblue",
    "queued": "yellow",
    "success": "green",
    "failure": "red",
    "cancelled": "dark_goldenrod",
    "expired": "dark_goldenrod",
}

status_symbols = {
    "created": "\U000026AA",  # white
    "active": "\U0001F7E2",  # green
    "paused": "\U0001F7E1",  # yellow
    "success": "\U00002705",  # Green check
    "failure": "\U0000274C",  # cross mark
    "cancelled": "\U0001F534",  # red
}
