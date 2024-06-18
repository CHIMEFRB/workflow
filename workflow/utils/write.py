"""Writing utilities for workflow."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Union

import yaml

from workflow import DEFAULT_WORKSPACE_PATH


def workspace(
    source: Union[Path, Dict[str, Any]], destination: Path = DEFAULT_WORKSPACE_PATH
) -> None:
    """Write a workspace to a destination.

    Args:
        source (Union[Path, Dict[str, Any]]): Workspace to write.
        destination (Path): Destination to write the workspace.

    Raises:
        ValueError: If source is not a dictionary or a file path.

    Returns:
        None: None
    """
    if not destination.parent.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
    # If destination file exists, move it to a backup location file.
    date: str = datetime.now().strftime("%Y%m%d%H%M%S")
    if destination.exists():
        destination.replace(destination.with_suffix(f".{date}.bak"))
    # Make sure the source path exists.
    if isinstance(source, Path):
        assert source.exists(), f"workspace {source} does not exist."
        source.replace(destination)
        return
    # Write dictionary to destination.
    elif isinstance(source, dict):  # type: ignore
        with open(destination, "w") as filename:
            yaml.dump(source, filename)
        return
    else:
        raise ValueError(f"source {source} is not a dictionary or a file path.")
