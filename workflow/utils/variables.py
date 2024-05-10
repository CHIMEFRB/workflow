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
    "queued": "\U0001F4C5",  # 📅
    "active": "\U0001F7E2",  # green circle
    "running": "\U0001F3C3",  # 🏃
    "success": "\U00002705",  # Green check
    "paused": "\U0001F7E1",  # yellow
    "failure": "\U0000274C",  # cross mark
    "cancelled": "\U0001F6AB",  # 🚫
}
