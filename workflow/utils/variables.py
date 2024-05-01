"""Variables needed for console printing."""

status_colors = {
    "created": "lightblue",
    "queued": "yellow",
    "active": "bright_blue",
    "running": "blue",
    "success": "green",
    "paused": "orange",
    "failure": "red",
    "cancelled": "dark_goldenrod",
    "expired": "dark_goldenrod",
}

status_symbols = {
    "created": "\U000026AA",  # white
    "queued": "\u23F3",  # hourglass
    "active": "\U0001F7E2",  # green
    "running": "\u2699",  # gear
    "success": "\U00002705",  # Green check
    "paused": "\U0001F7E1",  # yellow
    "failure": "\U0000274C",  # cross mark
    "cancelled": "\U0001F534",  # red
}
