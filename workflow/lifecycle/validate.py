"""Validate the user function and command."""
import subprocess
from importlib import import_module
from typing import Any, Callable

from chime_frb_api import get_logger

logger = get_logger("workflow")


def function(function: str) -> Callable[..., Any]:
    """Validate the user function.

    Args:
        function (str): Name of the user function.
            Must be in the form of 'module.submodule.function'.

    Raises:
        TypeError: Raised if the function is not callable.
        error: Raised if the function cannot be imported.

    Returns:
        Callable[..., Any]: The user function.
    """
    try:
        # Name of the module containing the user function
        module_name, func_name = function.rsplit(".", 1)
        module = import_module(module_name)
        function = getattr(module, func_name)
        # Check if the function is callable
        if not callable(function):
            raise TypeError(f"{function} is not callable")
    except Exception as error:
        logger.exception(error)
        raise error
    return function


def command(command: str) -> bool:
    """Validate the command.

    Args:
        command (str): Name of the command.

    Returns:
        bool: True if the command exists, False otherwise.
    """
    try:
        subprocess.check_output(["which", command])
        return True
    except subprocess.CalledProcessError:
        return False
