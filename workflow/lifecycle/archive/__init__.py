"""Archive lifecycle module."""
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from minio import Minio

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
        date = datetime.fromtimestamp(work.creation).strftime("%Y%m%d")  # type: ignore
        path: Path = Path(
            f"{mounts.get(work.site)}/workflow/{date}/{work.pipeline}/{work.id}"
        )

        if (
            work.config.archive.products
            in archive_config.get("products", {}).get("methods", [])
            and work.products
        ):
            storage: str = archive_config.get("products", {}).get("storage", "")
            if storage:
                actions[storage][work.config.archive.products](
                    path,
                    work.products,
                )
                changes = True
            else:
                log.warning(
                    f"Archive storage {storage} not configured for products in workspace."
                )
        elif work.config.archive.products not in archive_config.get("products", {}).get(
            "methods", []
        ):
            log.warning(
                f"Archive method {work.config.archive.products} not allowed by workspace."
            )

        if (
            work.config.archive.plots
            in archive_config.get("plots", {}).get("methods", [])
            and work.plots
        ):
            storage: str = archive_config.get("plots", {}).get("storage", "")
            if storage:
                actions[storage][work.config.archive.plots](
                    path,
                    work.plots,
                )
                changes = True
            else:
                log.warning(
                    f"Archive storage {storage} not configured for plots in workspace."
                )
        elif work.config.archive.plots not in archive_config.get("plots", {}).get(
            "methods", []
        ):
            log.warning(
                f"Archive method {work.config.archive.plots} not allowed by workspace."
            )
        if changes:
            # TODO: Perform permissions for plots and products separately
            permissions(path, work.site)
    except Exception as error:
        log.warning(error)
