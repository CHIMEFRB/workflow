"""HTTP archive functions."""

from pathlib import Path
from typing import List, Optional

from workflow.utils import logger

log = logger.get_logger("workflow.lifecycle.archive.http")


def bypass(path: Path, payload: Optional[List[str]]) -> bool:
    """Bypass the archive.

    Args:
        path (Path): Destination path.
        payload (List[str]): List of files to copy.
    """
    log.info("Bypassing archive.")
    return True


def copy(path: Path, payload: Optional[List[str]]) -> bool:
    """Copy the work products to the archive.

    Args:
        path (Path): Destination path.
        payload (List[str]): List of files to copy.
    """
    log.warning("upload currently not implemented")
    raise NotImplementedError


def move(path: Path, payload: Optional[List[str]]) -> bool:
    """Move the work products to the archive.

    Args:
        path (Path): Destination path.
        payload (List[str]): List of products to move.
    """
    log.warning("upload currently not implemented")
    raise NotImplementedError


def delete(path: Path, payload: Optional[List[str]]) -> bool:
    """Delete the work products from the archive.

    Args:
        path (Path): Destination path.
        payload (List[str]): List of products to delete.
    """
    log.warning("delete currently not implemented")
    raise NotImplementedError


def permissions(path: Path, site: str) -> bool:
    """Set the permissions for the work products in the archive."""
    log.warning("permissions currently not implemented")
    raise NotImplementedError
