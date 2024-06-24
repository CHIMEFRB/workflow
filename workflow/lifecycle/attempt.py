"""Workflow lifecycle module."""

import time
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
            if work.function:
                logger.debug(f"executing function: {work.function}")
                work = execute.function(work)

            # If we have a valid command, execute it
            if work.command:
                logger.debug(f"executing command: {work.command}")
                work = execute.command(work)

            if int(work.timeout) + int(work.start) < time.time():  # type: ignore
                raise TimeoutError("work timed out")

            archive.run(work, config)
            status = True
    except Exception as error:
        logger.exception(error)
        work.status = "failure"  # type: ignore
    finally:
        if work:
            product_url = config.get("http", {}).get("baseurls", {}).get("products", "")
            if any(work.notify.slack.model_dump().values()) and work.products:
                work.products = [
                    f"<{product_url}{product}|{product}>" for product in work.products
                ]
            if any(work.notify.slack.model_dump().values()) and work.plots:
                work.plots = [f"<{product_url}{plot}|{plot}>" for plot in work.plots]
            work.update()  # type: ignore
            logger.info("work completed: ✅")
        unset_tag()
        return status
