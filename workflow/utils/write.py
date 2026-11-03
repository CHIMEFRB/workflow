"""Writing utilities for workflow."""

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Union

import yaml

from workflow import DEFAULT_WORKSPACE_PATH


def workspace(
    source: Union[Path, Dict[str, Any]], destination: Path = DEFAULT_WORKSPACE_PATH
) -> None:
    """Write a workspace to a destination.

    The destination is replaced atomically, so a reader never finds it missing or
    partly written; when it changes, the previous one is kept as a dated `.bak`.
    A source file is copied, not moved.

    Args:
        source (Union[Path, Dict[str, Any]]): Workspace to write.
        destination (Path): Destination to write the workspace.

    Raises:
        ValueError: If source is not a dictionary or a file path.

    Returns:
        None: None
    """
    if isinstance(source, Path):
        assert source.exists(), f"workspace {source} does not exist."
        content: str = source.read_text()
    elif isinstance(source, dict):  # type: ignore
        content = yaml.dump(source)
    else:
        raise ValueError(f"source {source} is not a dictionary or a file path.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Runners can share one home (e.g. CANFAR sessions on /arc), so another one may be
    # reading the workspace right now: it is never moved away or left half-written.
    if destination.exists():
        if destination.read_text() == content:
            return
        # Back up the one being replaced, as a copy so it stays in place meanwhile.
        date: str = datetime.now().strftime("%Y%m%d%H%M%S")
        shutil.copy2(destination, destination.with_suffix(f".{date}.bak"))
    # Write beside it, then rename into place: readers see the old or the new file.
    descriptor, temporary = tempfile.mkstemp(
        dir=destination.parent, prefix=f".{destination.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w") as filename:
            filename.write(content)
        os.replace(temporary, destination)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
