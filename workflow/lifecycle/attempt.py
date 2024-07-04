"""Workflow lifecycle module."""

from typing import Any, Dict, List, Optional

from requests import exceptions

from workflow.definitions.work import Work
from workflow.http.context import HTTPContext
from workflow.lifecycle import archive, execute
from workflow.utils.logger import get_logger, set_tag, unset_tag

logger = get_logger("workflow.lifecycle.attempt")


def work(
    buckets: List[str],
    function: Optional[str],
    command: Optional[str],
    argsource: str,
    site: str,
    tags: List[str],
    parents: List[str],
    events: List[int],
    config: Dict[str, Any],
    http: Optional[HTTPContext] = None,
) -> bool:
    """Attempt to perform work.

    Args:
        buckets (List[str]): Name of the buckets to perform work from.
        function (Optional[str]): Static function to perform work.
        command (Optional[str]): Static command to perform work.
        argsource (str): Source of arguments for the function.
        site (str): Site to filter work by.
        tags (List[str]): Tags to filter work by.
        parents (List[str]): Parent pipeline to filter work by.
        config (Dict[str, Any]): Workspace configuration.

    Raises:
        TimeoutError: _description_

    Returns:
        bool: _description_
    """
    work: Optional[Work] = None
    status: bool = False

    try:
        # Attempt to get work from the workflow queue
        try:
            work = Work.withdraw(
                pipeline=buckets,
                site=site,
                tags=tags,
                parent=parents,
                event=events,
                http=http,
            )
        except exceptions.ConnectTimeout as error:
            logger.error("connection timeout getting work")
            raise error
        except exceptions.RequestException as error:
            logger.error("request exception getting work")
            raise error
        except Exception as error:
            logger.error("error getting work")
            raise error

        if work:
            # Set the work id for the logger
            set_tag(work.id)  # type: ignore
            logger.info("got work: ✅")
            logger.debug(f"{work.payload}")

            # When overloading, work cannot have both a function and a command
            if function:
                logger.debug(f"overloading work with static function: {function}")
                work.command = None
                work.function = function
            if command:
                logger.debug(f"overloading work with static command: {command}")
                work.function = None
                work.command = command.split(" ")

            assert work.command or work.function, "neither function or command provided"

            # Get the user function from the work object dynamically
            if work.function and argsource == "parameters":
                logger.debug(f"executing function: {work.function}")
                work = execute.function(work)
            elif work.function and argsource == "work":
                logger.debug(f"executing function with work object: {work.function}")
                work = execute.function_with_work(work)

            # If we have a valid command, execute it
            if work.command:
                logger.debug(f"executing command: {work.command}")
                work = execute.command(work)

            # * Note: work.status is already set to either "success" or "failure"
            # * in the execute module. We don't need to set it here.

            archive.run(work, config)
            work.update()
            status = True
    except Exception as error:
        logger.error(error)
        if work:
            work.results = {"error": str(error)}
            work.products = None
            work.plots = None
            work.status = "failure"
    finally:
        if work:
            work.update()
            logger.info("work completed: ✅")
            unset_tag()
        return status
