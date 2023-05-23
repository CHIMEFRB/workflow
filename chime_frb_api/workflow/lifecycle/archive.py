"""Archive lifecycle module."""
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from chime_frb_api import get_logger
from chime_frb_api.configs import MOUNTS, TEST_MOUNTS
from chime_frb_api.workflow import Work

logger = get_logger("workflow")


def copy(path: Path, payload: Optional[List[str]]) -> bool:
    """Copy the work products to the archive.

    Args:
        path (Path): Destination path.
        payload (List[str]): List of products to copy.
        site (str): Site name.
    """
    status: bool = False
    try:
        path.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.is_dir() and os.access(path, os.W_OK) and payload:
            for index, item in enumerate(payload):
                shutil.copy(item, path.as_posix())
                payload[index] = (path / item.split("/")[-1]).as_posix()
        elif not payload:
            logger.info("No files in payload.")
        status = True
    except Exception as error:
        logger.exception(error)
        status = False
    finally:
        return status


def move(path: Path, payload: Optional[List[str]]) -> bool:
    """Move the work products to the archive.

    Args:
        path (Path): Destination path.
        payload (List[str]): List of products to move.
    """
    status: bool = False
    try:
        path.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.is_dir() and os.access(path, os.W_OK) and payload:
            for index, item in enumerate(payload):
                shutil.move(item, path.as_posix())
                payload[index] = (path / item.split("/")[-1]).as_posix()
        elif not payload:
            logger.info("No files in payload.")
        status = True
    except Exception as error:
        logger.exception(error)
        status = False
    finally:
        return status


def delete(path: Path, payload: Optional[List[str]]) -> bool:
    """Delete the work products from the archive.

    Args:
        path (Path): Destination path.
        payload (List[str]): List of products to delete.
    """
    try:
        if payload:
            to_remove = []
            for index, item in enumerate(payload):
                os.remove(item)
                to_remove.append(item)
        else:
            logger.info("No files in payload.")
        status = True
    except Exception as error:
        logger.exception(error)
        status = False
    finally:
        if payload:
            for item in to_remove:
                payload.remove(item)
        return status


def upload(path: Path, payload: Optional[List[str]]) -> bool:
    """Upload the work products to the archive.

    Args:
        path (Path): Destination path.
        payload (List[str]): List of products to upload.

    Returns:
        bool: True if the upload was successful, False otherwise.
    """
    logger.warning("upload not implemented")
    return True


def permissions(path: Path, site: str) -> bool:
    """Set the permissions for the work products in the archive."""
    try:
        if site == "canfar":
            subprocess.run(f"setfacl -R -m g:chime-frb-ro:r {path.as_posix()}")
            subprocess.run(f"setfacl -R -m g:chime-frb-rw:rw {path.as_posix()}")
        status = True
    except FileNotFoundError as error:
        logger.exception(error)
        logger.debug(
            "Linux dependency 'acl' not installed. Trying to use chgrp and chmod instead."  # noqa: E501
        )
        try:
            subprocess.run(f"chgrp -R chime-frb-rw {path.as_posix()}")
            subprocess.run(f"chmod g+w {path.as_posix()}")
            status = True
        except Exception as error:
            logger.exception(error)
            status = False
    finally:
        return status


def run(work: Work, test_mode: bool = False):
    """Run the archive lifecycle for a work object.

    Parameters
    ----------
    work : Work
        The work object to run the archive lifecycle for.
    test_mode: bool
        If being run in tests.
    """
    try:
        actions = {
            "copy": copy,
            "move": move,
            "delete": delete,
            "upload": upload,
        }
        date = datetime.fromtimestamp(work.creation).strftime("%Y%m%d")  # type: ignore
        if not test_mode:
            path = Path(
                f"{MOUNTS.get(work.site)}/workflow/{date}/{work.pipeline}/{work.id}"
            )
        else:
            path = Path(
                f"{TEST_MOUNTS.get(work.site)}/workflow/{date}/{work.pipeline}/{work.id}"
            )
        if work.config.archive.products != "pass":
            if work.products:
                actions[work.config.archive.products](path, work.products)
        if work.config.archive.plots != "pass":
            if work.plots:
                actions[work.config.archive.plots](path, work.plots)
        if (
            work.config.archive.products != "pass"
            or work.config.archive.plots != "pass"
        ):
            permissions(path, work.site)
    except Exception as error:
        logger.exception(error)
