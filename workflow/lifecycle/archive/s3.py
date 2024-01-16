"""S3 archive functions."""
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from minio import Minio

from workflow.definitions.work import Work
from workflow.lifecycle.archive import log

# TODO: Tarik: If S3 need extra info:
# - ENDPOINT
# - ACCESS KEY
# - SECRET KEY
# - BUCKET

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
    # TODO: Tarik: Implement copy for S3
    # PERF: Tarik: Improve function
    try:
        # Initialise minio client
        client = Minio(
            endpoint=os.getenv("S3_ENDPOINT"),
            access_key=os.getenv("S3_ACCESS_KEY"),
            secret_key=os.getenv("S3_SECRET_KEY"),
            secure=False,
        )
        # Check path exists and is writable
        if not path.exists() or not path.is_dir() or not os.access(path, os.W_OK):
            log.error("Destination path is invalid or not writable.")
            return False
        # Check there are files to copy
        if not payload:
            log.info("No files in payload.")
            return True
        for index, item in enumerate(payload):
            # Check file exists
            if not os.path.exists(item):
                log.warning(f"File {item} does not exist.")
                continue
            # Upload file to S3
            response = client.fput_object(
                bucket_name=os.getenv("S3_BUCKET"),
                object_name=(path / item.split("/")[-1]).as_posix(),
                file_path=item,
            )
            # Update payload with new path
            payload[
                index
            ] = f"s3://{os.getenv('S3_BUCKET')}/{response["_bucket_name"]}/{response["_object_name"]}"
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
    # TODO: Tarik: Implement move for S3
    logger.warning("upload currently not implemented")
    raise NotImplementedError


def delete(path: Path, payload: None | List[str]) -> bool:
    """Delete the work products from the archive.

    Args:
        path (Path): Destination path.
        payload (List[str]): List of products to delete.
    """
    # TODO: Tarik: Implement delete for S3
    logger.warning("delete currently not implemented")
    raise NotImplementedError

def permissions(path: Path, site: str) -> bool:
    """Set the permissions for the work products in the archive."""
    # TODO: Tarik: Implement permissions for S3
    logger.warning("permissions currently not implemented")
    raise NotImplementedError
