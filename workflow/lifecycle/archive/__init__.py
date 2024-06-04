"""Archive lifecycle module."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from workflow.definitions.work import Work
from workflow.lifecycle.archive import http, posix, s3
from workflow.utils import logger

log = logger.get_logger("workflow.lifecycle.archive")


def run(work: Work, workspace: Dict[str, Any]) -> None:
    """Run the archive lifecycle for a work object.

    Args:
        work (Work): The work object to run the archive lifecycle for.
        workspace (Dict[str, Any]): The workspace configuration.
    """
    try:
        mounts: Dict[str, Any] = workspace.get("archive", {}).get("mounts", {})
        archive_config: Dict[str, Any] = workspace.get("config", {}).get("archive", {})
        changes: bool = False
        actions = {
            "s3": {
                "bypass": s3.bypass,
                "copy": s3.copy,
                "delete": s3.delete,
                "move": s3.move,
            },
            "posix": {
                "bypass": posix.bypass,
                "copy": posix.copy,
                "delete": posix.delete,
                "move": posix.move,
            },
            "http": {
                "bypass": http.bypass,
                "copy": http.copy,
                "delete": http.delete,
                "move": http.move,
            },
        }
        if work.creation:
            date: str = datetime.fromtimestamp(work.creation).strftime("%Y%m%d")
        else:
            raise NameError("Creation date not found in work object.")
        basepath: Path = Path(f"{mounts.get(work.site)}")
        path: Path = basepath / f"/workflow/{date}/{work.pipeline}/{work.id}"

        if (
            work.config.archive.products
            in archive_config.get("products", {}).get("methods", [])
            and work.products
        ):
            storage: str = archive_config.get("products", {}).get("storage", "")
            if storage in actions.keys():
                actions[storage][work.config.archive.products](
                    path,
                    work.products,
                )
                changes = True
            else:
                log.warning(
                    f"Archive storage {storage} not supported, or storage has not been set for products in workspace."  # noqa: E501
                )
        elif work.config.archive.products not in archive_config.get("products", {}).get(
            "methods", []
        ):
            log.warning(
                f"Archive method {work.config.archive.products} not allowed for products by workspace."  # noqa: E501
            )

        if (
            work.config.archive.plots
            in archive_config.get("plots", {}).get("methods", [])
            and work.plots
        ):
            storage = archive_config.get("plots", {}).get("storage", "")
            if storage in actions.keys():
                actions[storage][work.config.archive.plots](
                    path,
                    work.plots,
                )
                changes = True
            else:
                log.warning(
                    f"Archive storage {storage} not supported, or storage has not been set for plots in workspace."  # noqa: E501
                )
        elif work.config.archive.plots not in archive_config.get("plots", {}).get(
            "methods", []
        ):
            log.warning(
                f"Archive method {work.config.archive.plots} not allowed for plots by workspace."  # noqa: E501
            )
        if changes and "posix" in archive_config.get("permissions", {}):
            posix.permissions(
                path, archive_config.get("permissions", {}).get("posix", {})
            )
    except Exception as error:
        log.warning(error)
