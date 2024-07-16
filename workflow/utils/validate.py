"""Utilities for validating data."""

import platform
import re
import subprocess
from importlib import import_module
from sys import getsizeof
from typing import Any, Callable, Dict, List, Tuple

from workflow.definitions.work import Work
from workflow.utils.logger import get_logger

logger = get_logger("workflow.utils.validate")


def url(url: str) -> bool:
    """Return True if the URL is valid.

    Args:
        url (str): The URL to validate.

    Returns:
        bool: True if the URL is valid.
    """
    regex = re.compile(
        r"^(https?://)?"  # http:// or https:// (optional)
        r"("
        r"localhost|"  # localhost
        r"((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"  # ipv4
        r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"  # ipv4
        r"|"
        r"([a-zA-Z0-9]+([-.\w]*[a-zA-Z0-9])*"  # domain...
        r"(\.[a-zA-Z0-9]{2,3})+)"  # ...with top level domain
        r")"
        r"(?::\d{2,5})?"  # optional port
        r"(?:/?|[/?]\S+)?$",
        re.IGNORECASE,
    )  # optional trailing path/query

    return re.match(regex, url) is not None


def function(function: str) -> Callable[..., Any]:
    """Validate the user function.

    Args:
        function (str): Name of the user function.
            Must be in the form of 'module.submodule.function'.

    Raises:
        TypeError: Raised if the function is not callable.
        ImportError: Raised if the function cannot be imported.

    Returns:
        Callable[..., Any]: The user function.
    """
    try:
        # Name of the module containing the user function
        module_name, func_name = function.rsplit(".", 1)
        module = import_module(module_name)
        function = getattr(module, func_name)
        logger.debug(f"discovered {function} @ {module.__file__}")
        # Check if the function is callable
        if not callable(function):
            raise TypeError(f"{function} is not callable")
    except Exception as error:
        logger.error(error)
        raise ImportError(f"failed to import: {function}")
    return function


def command(command: str) -> bool:
    """Validate the command.

    Args:
        command (str): Name of the command.

    Returns:
        bool: True if the command exists, False otherwise.
    """
    command = command.split(" ")[0]
    try:
        if platform.system() == "Windows":
            response = subprocess.check_output(  # nosec
                ["where", command], shell=True, universal_newlines=True
            )
            logger.debug(f"discovered {command} @ {response}")
        else:
            response = subprocess.check_output(  # nosec
                ["which", command], universal_newlines=True
            )
            logger.debug(f"discovered {command} @ {response}")
        return True
    except subprocess.CalledProcessError:
        return False


def deployments(config: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Validate deployments.

    Args:
        config (Dict[str, Any]): Config payload.

    Returns:
        Tuple[List[str], List[str]]: Unused deployments and orphaned steps.
    """
    unused_deployments = []
    orphaned_steps = []
    deployments = config.get("deployments", [])
    steps = config["pipeline"]["steps"]

    for deployment in deployments:
        n_used = int()
        top_level = False
        # ? First case: unused deployments
        if config["pipeline"].get("runs_on", None):
            if deployment["name"] in config["pipeline"]["runs_on"]:
                n_used += 1
                top_level = True
        for step in steps:
            has_runs_on = False
            if step.get("runs_on", None):
                used = deployment["name"] in step["runs_on"]
                has_runs_on = True
                if used:
                    n_used += 1
                # ? Second case: orphaned steps
                if not used and not has_runs_on:
                    orphaned_steps.append(step["name"])
            if not top_level and not has_runs_on:
                orphaned_steps.append(step["name"])

        if n_used == 0:
            unused_deployments.append(deployment["name"])

    return (unused_deployments, list(set(orphaned_steps)))


def outcome(output: Any) -> Tuple[Dict[str, Any], List[str], List[str]]:
    """Parse the output, returning results, products, and plots.

    Args:
        output (Any): The output from the work execution.

    Returns:
        Tuple[Dict[str, Any], List[str], List[str]]:
            Results, products, and plots.
    """
    results: Dict[str, Any] = {}
    products: List[str] = []
    plots: List[str] = []

    if isinstance(output, dict):
        results = output
    elif isinstance(output, tuple):
        # Assign values based on type and position in the tuple
        for item in output:
            if isinstance(item, dict) and not results:
                results = item
            elif isinstance(item, list):
                if not products:
                    products = item
                elif not plots:
                    plots = item
            else:
                logger.error(f"unable to parse output item {item}")
    else:
        logger.info("unable to parse output from work execution")

    return results, products, plots


def size(
    work: Work,
    fields: List[str] = ["results", "products", "plots"],
    size: int = 4_000_000,
) -> Work:
    """Check if the data is less than the specified.

    Args:
        work (Work): Work object.
        fields (List[str], optional): Fields.
            Defaults to ["results", "products", "plots"].
        size (int, optional): Size. Defaults to 4_000_000.

    Returns:
        Work: Work object.
    """
    for field in fields:
        data = getattr(work, field)
        fsize: int = getsizeof(data)
        if fsize > size:
            logger.error(
                f"{field} size {fsize/1000000:.2f}MB exceeds max: {size/1000000:.2f}MB"
            )
            # Set the field to None
            logger.warning(f"setting {field} to None")
            setattr(work, field, None)
    return work
