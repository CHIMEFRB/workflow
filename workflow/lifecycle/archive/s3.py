"""S3 archive functions."""

import os
from pathlib import Path
from typing import List, Optional

from minio import Minio

from workflow.utils import logger

log = logger.get_logger("workflow.lifecycle.archive.s3")

WORKFLOW_S3_ENDPOINT = os.getenv("WORKFLOW_S3_ENDPOINT")
WORKFLOW_S3_ACCESS_KEY = os.getenv("WORKFLOW_S3_ACCESS_KEY")
WORKFLOW_S3_SECRET_KEY = os.getenv("WORKFLOW_S3_SECRET_KEY")
WORKFLOW_S3_BUCKET = os.getenv("WORKFLOW_S3_BUCKET", "workflow")


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
        # Initialise minio client
        log.info("Connecting to S3 storage to copy files")
        log.debug(f"Endpoint: {WORKFLOW_S3_ENDPOINT}")
        log.debug(f"Access Key: {WORKFLOW_S3_ACCESS_KEY}")
        log.debug(f"Secret Key: {WORKFLOW_S3_SECRET_KEY}")
        client = Minio(
            endpoint=WORKFLOW_S3_ENDPOINT,
            access_key=WORKFLOW_S3_ACCESS_KEY,
            secret_key=WORKFLOW_S3_SECRET_KEY,
        )
        log.info("Connected ✅")
        # Check bucket exists and if not, create it
        if not client.bucket_exists(WORKFLOW_S3_BUCKET):
            log.info(f"Bucket {WORKFLOW_S3_BUCKET} does not exist. Creating it.")
            client.make_bucket(WORKFLOW_S3_BUCKET)
        # Check there are files to copy
        if not payload:
            log.info("No files in payload.")
            return True
        split_path = path.as_posix().split("/")
        object_paths = "/".join(split_path[split_path.index("workflow") + 1 :])
        for index, item in enumerate(payload):
            # Check file exists
            if not os.path.exists(item):
                log.warning(f"File {item} does not exist.")
                continue
            # Upload file to S3
            client.fput_object(
                bucket_name=WORKFLOW_S3_BUCKET,
                object_name="/".join([object_paths, item.split("/")[-1]]),
                file_path=item,
            )
            # Update payload with new path
            payload[index] = (
                f"s3://{os.getenv('WORKFLOW_S3_ENDPOINT')}/workflow/{'/'.join([object_paths, item.split('/')[-1]])}"  # noqa: E501
            )
        log.info("Move complete ✅")
        return True
    except Exception as error:
        log.error("Move failed ❌")
        log.exception(error)
        return False


def move(path: Path, payload: Optional[List[str]]) -> bool:
    """Move the work products to the archive.

    Args:
        path (Path): Destination path.
        payload (List[str]): List of products to move.
    """
    try:
        # Initialise minio client
        log.info("Connecting to S3 storage to move files")
        log.debug(f"Endpoint: {WORKFLOW_S3_ENDPOINT}")
        log.debug(f"Access Key: {WORKFLOW_S3_ACCESS_KEY}")
        log.debug(f"Secret Key: {WORKFLOW_S3_SECRET_KEY}")
        client = Minio(
            endpoint=WORKFLOW_S3_ENDPOINT,
            access_key=WORKFLOW_S3_ACCESS_KEY,
            secret_key=WORKFLOW_S3_SECRET_KEY,
        )
        log.info("Connected ✅")
        # Check bucket exists and if not, create it
        if not client.bucket_exists(WORKFLOW_S3_BUCKET):
            log.info(f"Bucket {WORKFLOW_S3_BUCKET} does not exist. Creating it.")
            client.make_bucket(WORKFLOW_S3_BUCKET)
        # Check there are files to copy
        if not payload:
            log.info("No files in payload.")
            return True
        split_path = path.as_posix().split("/")
        object_paths = "/".join(split_path[split_path.index("workflow") + 1 :])
        for index, item in enumerate(payload):
            # Check file exists
            if not os.path.exists(item):
                log.warning(f"File {item} does not exist.")
                continue
            # Upload file to S3
            client.fput_object(
                bucket_name=WORKFLOW_S3_BUCKET,
                object_name="/".join([object_paths, item.split("/")[-1]]),
                file_path=item,
            )
            # Update payload with new path
            payload[index] = (
                f"s3://{os.getenv('WORKFLOW_S3_ENDPOINT')}/workflow/{'/'.join([object_paths, item.split('/')[-1]])}"  # noqa: E501  # noqa: E501
            )
            # Delete file
            os.remove(item)
        log.info("Move complete ✅")
        return True
    except Exception as error:
        log.error("Move failed ❌")
        log.exception(error)
        return False


def delete(path: Path, payload: Optional[List[str]]) -> bool:
    """Delete the work products from the archive.

    Args:
        path (Path): Destination path.
        payload (List[str]): List of products to delete.
    """
    # TODO: Implement delete for S3
    # NOTE: Do we need a specific delete function for S3?
    # Since Workflow always runs on a POSIX system, we can
    # just use the POSIX delete function.
    log.warning("delete currently not implemented")
    raise NotImplementedError


def permissions(path: Path, site: str) -> bool:
    """Set the permissions for the work products in the archive."""
    # TODO: Implement permissions for S3
    # NOTE: Permissions seems to be set on the bucket level, not the object level
    # So, perhaps add this to a bucket creation function?
    log.warning("permissions currently not implemented")
    raise NotImplementedError
