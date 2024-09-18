"""Configure workflow during the lifecycle."""

from logging import Formatter, Logger
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import click
import requests
from logging_loki import LokiHandler

from workflow import DEFAULT_WORKSPACE_PATH
from workflow.definitions.work import Work
from workflow.utils import read, validate, write
from workflow.utils.logger import get_logger

logger = get_logger("workflow.lifecycle.process")


def workspace(workspace: Union[str, Dict[Any, Any]]):
    """Configure the workspace during the lifecycle.

    Args:
        workspace (Union[str, Dict[Any, Any]]): Workspace configuration src.
    """
    # workspace passed as a string for Path or URL
    if isinstance(workspace, str):
        if Path(workspace).absolute().exists():
            if workspace == DEFAULT_WORKSPACE_PATH.as_posix():
                logger.info("Running with active workspace.")
            else:
                logger.info(f"Saving {workspace} as active workspace.")
                # Save the workspace path to the default location
                write.workspace(Path(workspace))
        # Check if the workspace is a URL
        elif validate.url(workspace):
            logger.info(f"Running with workspace from URL {workspace}")
            # Fetch the workspace from the URL
            payload = read.url(workspace)
            logger.info(f"URL Workspace: {payload}")
            # Save the workspace to the default location
            write.workspace(payload)

    if isinstance(workspace, dict):
        name: Optional[str] = workspace.get("workspace")
        logger.info(f"Running with dict workspace: {name}")
        # Save the workspace to the default location
        write.workspace(workspace)


def loki(logger: Logger, config: Dict[str, Any]) -> bool:
    """Add a Loki handler to the logger.

    Args:
        logger (Logger): Python logger
        config (Dict[str, Any]): Workspace configuration

    Returns:
        bool: Loki handler status
    """
    status: bool = False
    urls: List[str] = []
    loki_urls: Optional[Any] = config.get("http", {}).get("baseurls", {}).get("loki")
    loki_tags: Optional[Any] = config.get("logging", {}).get("loki", {}).get("tags", {})
    if not loki_urls:
        return status
    elif isinstance(loki_urls, str):
        urls = [loki_urls]
    elif isinstance(loki_urls, list):
        urls = loki_urls
    else:
        logger.error(f"Invalid Loki URL: {loki_urls}")
        return status

    for url in urls:
        try:
            status_code: int = requests.get(
                url.replace("loki/api/v1/push", "ready"), timeout=1
            ).status_code
            if status_code == 200:
                loki_handler = LokiHandler(url=url, tags=loki_tags, version="1")
                loki_handler.setFormatter(
                    Formatter("%(levelname)s %(tag)s %(name)s %(message)s")
                )
                loki_handler.setLevel(logger.root.level)
                logger.root.addHandler(loki_handler)
                logger.debug(f"Loki URL: {url}")
                status = True
                return status
        except Exception as error:
            logger.debug(error)
    return status


def arguments(func: Callable[..., Any], work: Work) -> List[str]:
    """Return a list of CLI arguments.

    Args:
        arguments (Dict[str, Any]): CLI arguments

    Returns:
        List[str]: List of CLI arguments
    """
    args: List[str] = []

    for parameter in func.params:  # type: ignore
        parameter_name_in_cli = parameter.opts[-1]
        paraneter_name_in_function = parameter.name
        parameter_value_in_work = work.parameters.get(  # type: ignore
            paraneter_name_in_function, None
        )

        if parameter_value_in_work:
            if isinstance(parameter_value_in_work, list):
                parameter_value_in_work = " ".join(parameter_value_in_work)

            if isinstance(parameter, click.Argument):
                # If argument, then the parameter is purely positional without a key
                args.append(f"{parameter_value_in_work}")
            elif isinstance(parameter, click.Option):
                if hasattr(parameter, "is_flag") and parameter.is_flag:
                    # If is_flag=True,
                    # then the parameter is a flag and doesn't have a value
                    args.append(f"{parameter_name_in_cli}")
                else:
                    if len(parameter_name_in_cli) == 2:
                        # Short options
                        # (often denoted by a single hyphen and a single letter like -r)
                        # are commonly written with a space
                        # between the option and its value
                        args.append(
                            f"{parameter_name_in_cli} {parameter_value_in_work}"
                        )
                    elif len(parameter_name_in_cli) > 2:
                        # Long options
                        # (often denoted by two hyphens and a word like --recursive)
                        # are commonly written with an equals sign
                        # between the option and its value
                        args.append(
                            f"{parameter_name_in_cli}={parameter_value_in_work}"
                        )

    return args


def defaults(func: Callable[..., Any], work: Work) -> Work:
    """Gather the parameters for the user function.

    Args:
        func (Callable[..., Any]): User function
        work (Work): Work object

    Returns:
        Tuple[Callable[..., Any], Dict[str, Any]]:
            Tuple of user function and parameters
    """
    # Options calculated from the click command and work parameters
    options: Dict[str, Any] = {}
    # Parameters passed to work object
    parameters: Dict[str, Any] = work.parameters or {}
    # Known work parameters keys
    known: List[Any] = list(work.parameters.keys()) if work.parameters else []
    if isinstance(func, click.Command):
        logger.info(f"click cli detected for func {work.function}")
        # Get default options from the click command
        for parameter in func.params:
            name_in_cli = parameter.opts[-1]
            name_in_function = parameter.name

            if name_in_function not in known:
                if hasattr(parameter, "default") and parameter.default:
                    parameter_default_value = parameter.default

                    if hasattr(parameter, "is_flag") and parameter.is_flag:
                        if parameter_default_value is True:
                            # Flags aren't assigned values
                            # its CLI name is just included or not included
                            options[name_in_cli] = None
                    else:
                        options[name_in_cli] = parameter_default_value
            else:
                parameter_given_value = parameters.get(name_in_function)  # type: ignore

                if hasattr(parameter, "is_flag") and parameter.is_flag:
                    if parameter_given_value is True:
                        # Flags aren't assigned values
                        # its CLI name is just included or not included
                        options[name_in_cli] = None
                else:
                    options[name_in_cli] = parameter_given_value
        logger.info(f"click cli options: {options}")
        work.parameters = options
    logger.debug(f"work parameters: {work.parameters}")
    return work
