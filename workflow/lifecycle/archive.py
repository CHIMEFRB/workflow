"""Archive lifecycle module."""
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from workflow.definitions.work import Work
from workflow.utils.logger import get_logger

logger = get_logger("workflow")


def copy(path: Path, payload: Optional[List[str]]) -> bool:
    """Copy the work products to the archive.

    Args:
        path (Path): Destination path.
        payload (List[str]): List of files to copy.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        if not path.exists() or not path.is_dir() or not os.access(path, os.W_OK):
            logger.error("Destination path is invalid or not writable.")
            return False
        if not payload:
            logger.info("No files in payload.")
            return True
        for index, item in enumerate(payload):
            if not os.path.exists(item):
                logger.warning(f"File {item} does not exist.")
                continue
            shutil.copy(item, path.as_posix())
            payload[index] = (path / item.split("/")[-1]).as_posix()
        return True
    except Exception as error:
        logger.exception(error)
        return False


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


def delete(path: Path, payload: None | List[str]) -> bool:
    """Delete the work products from the archive.

    Args:
        path (Path): Destination path.
        payload (List[str]): List of products to delete.
    """
    status: bool = False
    try:
        if payload:
            for item in payload:
                os.remove(item)
                payload.remove(item)
        else:
            logger.info("no files to delete.")
        status = True
    except Exception as error:
        logger.exception(error)
    finally:
        return status


def upload(path: Path, payload: Optional[List[str]]) -> bool:
    """Upload the work products to the archive.

    Args:
        path (Path): Destination path.
        payload (List[str]): List of products to upload.

    Returns:
        bool: True if the upload was successful, False otherwise.
    """
    logger.warning("upload currently not implemented")
    raise NotImplementedError


def permissions(path: Path, site: str) -> bool:
    """Set the permissions for the work products in the archive."""
    status: bool = False
    try:
        if site == "canfar":
            subprocess.run(f"setfacl -R -m g:chime-frb-ro:r {path.as_posix()}")
            subprocess.run(f"setfacl -R -m g:chime-frb-rw:rw {path.as_posix()}")
        status = True
    except FileNotFoundError as error:
        logger.warning(error)
        logger.debug(
            "Linux tool 'acl' not installed, trying chgrp and chmod instead."  # noqa: E501
        )
        try:
            subprocess.run(f"chgrp -R chime-frb-rw {path.as_posix()}")
            subprocess.run(f"chmod g+w {path.as_posix()}")
            status = True
        except Exception as error:
            logger.warning(error)
            status = False
    finally:
        return status


def run(work: Work, workspace: Dict[str, Any]):
    """Run the archive lifecycle for a work object.

    Args:
        work (Work): The work object to run the archive lifecycle for.
        workspace (Dict[str, Any]): The workspace configuration.
    """
    try:
        # workspace: Dict[str, Any] = read.workspace(DEFAULT_WORKSPACE_PATH.as_posix())
        mounts: Dict[str, Any] = workspace.get("archive", {}).get("mounts", {})
        changes: bool = False
        actions = {
            "copy": copy,
            "move": move,
            "delete": delete,
            "upload": upload,
        }
        date = datetime.fromtimestamp(work.creation).strftime("%Y%m%d")  # type: ignore
        path: Path = Path(
            f"{mounts.get(work.site)}/workflow/{date}/{work.pipeline}/{work.id}"
        )
        if work.config.archive.products != "pass" and work.products:
            actions[work.config.archive.products](path, work.products)
            changes = True
        if work.config.archive.plots != "pass" and work.plots:
            actions[work.config.archive.plots](path, work.plots)
            changes = True
        if changes:
            permissions(path, work.site)
    except Exception as error:
        logger.warning(error)
