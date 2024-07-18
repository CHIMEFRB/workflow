"""Archive lifecycle module."""

from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict

from workflow.definitions.work import Work
from workflow.lifecycle.archive import http, posix, s3
from workflow.utils import logger

log = logger.get_logger("workflow.lifecycle.archive")


class ArchiveResultsError(Exception):
    """Exception raised for any error in archiving the results for a Work.

    Attributes:
        message (str): Explanation for the error.
    """

    def __init__(
        self, message="Something went wrong when archiving the results."
    ) -> None:
        """Initialize the ArchiveResultsError.

        Args:
            message (str): Error message to display.
        """
        self.message = message
        super().__init__(self.message)


def _get_basepath(mounts: Dict[str, Any], site: str, storage: str) -> Path:
    """Get the basepath from the config for the given site and storage.

    Args:
        mounts: Archive mounts configuration.
        site: Site to get the basepath for.
        storage: Storage type to get the basepath for.

    Raises:
        ArchiveResultsError: No configuration for the given storage in the workspace.

    Returns:
        Path: The basepath for the given site and storage.
    """
    if not storage:
        raise ArchiveResultsError("Storage must be given.")
    elif storage == "posix":
        basepath: Path = Path(f"{mounts.get(storage, {}).get(site, {})}")
    elif storage == "s3":
        basepath = Path(f"{mounts.get(storage, {}).get(site, {}).get('subpath', '')}")
    else:
        raise ArchiveResultsError(f"No configuration for {storage} in Workspace.")
    return basepath


def run(work: Work, workspace: Dict[str, Any]) -> None:
    """Run the archive lifecycle for a work object.

    Args:
        work (Work): The work object to run the archive lifecycle for.
        workspace (Dict[str, Any]): The workspace configuration.
    """
    try:
        mounts: Dict[str, Any] = workspace.get("archive", {})
        archive_config: Dict[str, Any] = workspace.get("config", {}).get("archive", {})
        changes: bool = False
        actions: Dict[str, Dict[str, Callable]] = {
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
        work_subpath: str = f"{date}/{work.pipeline}/{work.id}"

        try:
            if (
                work.config.archive.products
                in archive_config.get("products", {}).get("methods", [])
                and work.products
            ):
                storage: str = archive_config.get("products", {}).get("storage", "")
                basepath: Path = _get_basepath(mounts, work.site, storage)
                path: Path = basepath / work_subpath
                if storage in actions.keys():
                    actions[storage][work.config.archive.products](
                        path,
                        work.products,
                        work.site,
                    )
                    changes = True
                else:
                    log.warning(
                        f"Archive storage {storage} not supported, or storage has not been set for products in workspace."  # noqa: E501
                    )
            elif work.config.archive.products not in archive_config.get(
                "products", {}
            ).get("methods", []):
                log.warning(
                    f"Archive method {work.config.archive.products} not allowed for products by workspace."  # noqa: E501
                )
        except ArchiveResultsError as error:
            log.warning(error)

        try:
            if (
                work.config.archive.plots
                in archive_config.get("plots", {}).get("methods", [])
                and work.plots
            ):
                storage = archive_config.get("plots", {}).get("storage", "")
                basepath = _get_basepath(mounts, work.site, storage)
                path = basepath / work_subpath
                if storage in actions.keys():
                    actions[storage][work.config.archive.plots](
                        path,
                        work.plots,
                        work.site,
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
        except ArchiveResultsError as error:
            log.warning(error)

        if changes and "posix" in archive_config.get("permissions", {}):
            posix.permissions(
                path, archive_config.get("permissions", {}).get("posix", {})
            )
    except Exception as error:
        log.warning(error)
