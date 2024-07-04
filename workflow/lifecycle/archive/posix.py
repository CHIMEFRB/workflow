"""POSIX archive functions."""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from workflow.utils import logger

log = logger.get_logger("workflow.lifecycle.archive.posix")


def extract_basepath(path: Path):
    """Extract the base path from a given path.

    Uses the fact that the path is build using the following format,
    path = basepath / f"/workflow/{date}/{work.pipeline}/{work.id}"

    Args:
        path: Path to extract from.

    Returns:
        Path: Base path.
    """
    try:
        split_path = re.split(r"/workflow/\d+", path.as_posix())
        basepath = split_path[0]
        return Path(basepath)
    except Exception as e:
        raise e


def check_basepath(path: Path):
    """Validates if the basepath exists.

    If the path given contains '/workflow' it is not the basepath and so the basepath
    is extracted before the evaluation.

    Args:
        path: Path to validate.

    Raises:
        FileNotFoundError: If the path doesn't exist.

    Returns:
        bool: True if the path exists.
    """
    if "/workflow" in path.as_posix():
        path = extract_basepath(path)
    if not path.exists():
        raise FileNotFoundError(f"Mount {path} does not exist.")
    else:
        return True


def bypass(path: Path, payload: Optional[List[str]], site: str) -> bool:
    """Bypass the archive.

    Args:
        path (Path): Destination path.
        payload (List[str]): List of files to copy.
        site (str): Site work was performed at.
    """
    log.info("Bypassing archive.")
    return True


def copy(path: Path, payload: Optional[List[str]], site: str) -> bool:
    """Copy the work products to the archive.

    Args:
        path (Path): Destination path.
        payload (List[str]): List of files to copy.
        site (str): Site work was performed at.
    """
    try:
        check_basepath(path)
        path.mkdir(parents=True, exist_ok=True)
        if not path.exists() or not path.is_dir() or not os.access(path, os.W_OK):
            log.error("Destination path is invalid or not writable.")
            return False
        if not payload:
            log.info("No files in payload.")
            return True
        for index, item in enumerate(payload):
            if not os.path.exists(item):
                log.warning(f"File {item} does not exist.")
                continue
            shutil.copy(item, path.as_posix())
            payload[index] = (path / item.split("/")[-1]).as_posix()
        return True
    except Exception as error:
        log.exception(error)
        return False


def move(path: Path, payload: Optional[List[str]], site: str) -> bool:
    """Move the work products to the archive.

    Args:
        path (Path): Destination path.
        payload (List[str]): List of products to move.
        site (str): Site work was performed at.
    """
    status: bool = False
    try:
        check_basepath(path)
        path.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.is_dir() and os.access(path, os.W_OK) and payload:
            for index, item in enumerate(payload):
                shutil.move(item, path.as_posix())
                payload[index] = (path / item.split("/")[-1]).as_posix()
        elif not payload:
            log.info("No files in payload.")
        status = True
    except Exception as error:
        log.exception(error)
        status = False
    finally:
        return status


def delete(path: Path, payload: Optional[List[str]], site: str) -> bool:
    """Delete the work products from the archive.

    Args:
        path (Path): Destination path.
        payload (List[str]): List of products to delete.
        site (str): Site work was performed at.
    """
    status: bool = False
    try:
        check_basepath(path)
        if payload:
            for item in payload:
                os.remove(item)
                payload.remove(item)
        else:
            log.info("no files to delete.")
        status = True
    except Exception as error:
        log.exception(error)
    finally:
        return status


def permissions(path: Path, config: Dict[str, Any]) -> bool:
    """Set the permissions for the work products in the archive."""
    status: bool = False
    try:
        check_basepath(path)
        if not path.exists():
            raise NotADirectoryError

        user: Optional[str] = config.get("user")
        group: Optional[str] = config.get("group")
        if not user and not group:
            raise ValueError("Either user or group must be specified.")

        command: str = config.get(
            "command",
            "chgrop -R {group} {path}; chmod -R g+w {path}",
        )
        command = eval(f"f'{command}'")
        subprocess.run(command)
        status = True

    except NotADirectoryError:
        log.error(f"Path {path.as_posix()} does not exist.")
        status = False

    except ValueError as error:
        log.error(error)
        status = False

    except FileNotFoundError as error:
        log.warning(error)
        try:
            subprocess.run(f"chgrp -R chime-frb-rw {path.as_posix()}")
            subprocess.run(f"chmod g+w {path.as_posix()}")
            status = True
        except Exception as error:
            log.warning(error)
            status = False

    finally:
        return status
