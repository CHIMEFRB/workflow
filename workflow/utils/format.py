"""Refomat functions."""

from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console


def needs_reformat(data: Dict[str, Any]) -> Tuple[bool, bool, bool]:
    """Determines if data needs reformat.

    Parameters
    ----------
    data : Dict[str, Any]
        Payload.

    Returns
    -------
    Tuple[bool, bool, bool]
        Tuple of fields that need reformat.
    """
    matrix = False
    steps = False
    version = False
    if isinstance(data["pipeline"], dict):
        if "steps" not in data["pipeline"].keys():
            steps = True
    if "matrix" in data.keys():
        matrix = True
    if data["version"] == "1" or isinstance(data["version"], int):
        version = True
    return steps, matrix, version


def reformat(
    data: Dict[str, Any],
    r_steps: bool,
    r_matrix: bool,
    r_version: bool,
    console: Optional[Console] = None,
) -> Dict[str, Any]:
    """Reformats data to work on Pipeline V2 backend.

    Parameters
    ----------
    data : Dict[str, Any]
        Config payload.
    r_steps: bool
        If steps needs to be reformatted.
    r_matrix : bool
        If matrix needs to be reformatted.
    r_version: bool,
        If version needs to be reformatted.
    console: Console,
        Console object.

    Returns
    -------
    Dict[str, Any]
        Reformatted data.
    """
    # ? Reformat steps
    if r_steps:
        if console:
            console.print("Reformatting steps.", style="green")
        steps: List[Dict[str, Any]] = []
        for step_name in data["pipeline"].keys():
            step = data["pipeline"][step_name]
            step["name"] = step_name.replace("_", "-")
            steps.append(step)
        data.pop("pipeline")
        data["pipeline"] = {"steps": steps}

    # ? Check top level matrix
    if r_matrix:
        if console:
            console.print("Reformatting top level matrix.", style="green")
        matrix: Optional[Dict[str, Any]] = None
        if data.get("matrix", None):
            matrix = data["matrix"]
            data.pop("matrix")
            data["pipeline"]["matrix"] = matrix

    # ? Fix version
    if r_version:
        if console:
            console.print("Fixing version.", style="green")
        data["version"] = "2"

    return data
