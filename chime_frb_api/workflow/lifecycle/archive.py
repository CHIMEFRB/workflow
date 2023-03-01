"""Archive lifecycle module."""
from pathlib import Path
from typing import List, Optional

from chime_frb_api import get_logger
from chime_frb_api.workflow import Work

logger = get_logger("workflow")


def copy(path: Path, payload: Optional[List[str]]):
    """Copy the work products to the archive.

    Args:
        path (Path): Destination path.
        payload (Optional[List[str]]): List of products to copy.
        site (str): Site name.
    """
    pass


def move(path: Path, payload: Optional[List[str]]):
    """Move the work products to the archive.

    Args:
        path (Path): Destination path.
        payload (Optional[List[str]]): List of products to move.
    """
    pass


def delete(path: Path, payload: Optional[List[str]]):
    """Delete the work products from the archive.

    Args:
        path (Path): Destination path.
        payload (Optional[List[str]]): List of products to delete.
    """
    pass


def upload() -> bool:
    """Upload the work products to the archive.

    Returns:
        bool: True if the upload was successful, False otherwise.
    """
    logger.warning("upload not implemented")
    return True


def permissions(path: Path, site: str):
    """Set the permissions for the work products in the archive."""
    pass


def run(work: Work):
    """Run the archive lifecycle for a work object.

    Parameters
    ----------
    work : Work
        The work object to run the archive lifecycle for.
    """
    path = Path(".")
    if work.config.archive.products == "copy":
        copy(path, work.products)
