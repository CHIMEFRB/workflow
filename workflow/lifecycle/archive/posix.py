"""POSIX archive functions."""
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from workflow.utils import logger

log = logger.get_logger("workflow.lifecycle.archive.posix")


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
    try:
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
            log.info("No files in payload.")
        status = True
    except Exception as error:
        log.exception(error)
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
        if not path.exists():
            raise NotADirectoryError

        user: str | None = config.get("user")
        group: str | None = config.get("group")
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
