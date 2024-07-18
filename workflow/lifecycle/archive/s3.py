"""S3 archive functions."""

import os
from pathlib import Path
from typing import List, Optional

from minio import Minio

from workflow import DEFAULT_WORKSPACE_PATH
from workflow.utils import logger, read

log = logger.get_logger("workflow.lifecycle.archive.s3")


try:
    workspace = read.workspace(DEFAULT_WORKSPACE_PATH)
except Exception as error:
    log.debug(f"Failed to import s3 archive configuration, {error}")
    log.debug("Using empty workspace configuration.")
    workspace = {}

WORKFLOW_S3_ARCHIVE_CONFIG = workspace.get("archive", {}).get("s3", {})
WORKFLOW_S3_ACCESS_KEY = os.getenv("WORKFLOW_S3_ACCESS_KEY")
WORKFLOW_S3_SECRET_KEY = os.getenv("WORKFLOW_S3_SECRET_KEY")


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
        workflow_s3_endpoint = WORKFLOW_S3_ARCHIVE_CONFIG.get(site, {}).get("url", "")
        workflow_s3_bucket = WORKFLOW_S3_ARCHIVE_CONFIG.get(site, {}).get("bucket", "")
        # Initialise minio client
        log.info("Connecting to S3 storage to copy files")
        log.debug(f"Endpoint: {workflow_s3_endpoint}")
        log.debug(f"Access Key: {WORKFLOW_S3_ACCESS_KEY}")
        log.debug(f"Secret Key: {WORKFLOW_S3_SECRET_KEY}")
        client = Minio(
            endpoint=workflow_s3_endpoint,
            access_key=WORKFLOW_S3_ACCESS_KEY,
            secret_key=WORKFLOW_S3_SECRET_KEY,
        )
        log.info("Connected ✅")
        # Check bucket exists and if not, create it
        if not client.bucket_exists(workflow_s3_bucket):
            log.info(f"Bucket {workflow_s3_bucket} does not exist. Creating it.")
            client.make_bucket(workflow_s3_bucket)
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
                bucket_name=workflow_s3_bucket,
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


def move(path: Path, payload: Optional[List[str]], site: str) -> bool:
    """Move the work products to the archive.

    Args:
        path (Path): Destination path.
        payload (List[str]): List of products to move.
        site (str): Site work was performed at.
    """
    try:
        workflow_s3_endpoint = WORKFLOW_S3_ARCHIVE_CONFIG.get(site, {}).get("url", "")
        workflow_s3_bucket = WORKFLOW_S3_ARCHIVE_CONFIG.get(site, {}).get("bucket", "")
        # Initialise minio client
        log.info("Connecting to S3 storage to move files")
        log.debug(f"Endpoint: {workflow_s3_endpoint}")
        log.debug(f"Access Key: {WORKFLOW_S3_ACCESS_KEY}")
        log.debug(f"Secret Key: {WORKFLOW_S3_SECRET_KEY}")
        client = Minio(
            endpoint=workflow_s3_endpoint,
            access_key=WORKFLOW_S3_ACCESS_KEY,
            secret_key=WORKFLOW_S3_SECRET_KEY,
        )
        log.info("Connected ✅")
        # Check bucket exists and if not, create it
        if not client.bucket_exists(workflow_s3_bucket):
            log.info(f"Bucket {workflow_s3_bucket} does not exist. Creating it.")
            client.make_bucket(workflow_s3_bucket)
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
                bucket_name=workflow_s3_bucket,
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


def delete(path: Path, payload: Optional[List[str]], site: str) -> bool:
    """Delete the work products from the archive.

    Args:
        path (Path): Destination path.
        payload (List[str]): List of products to delete.
        site (str): Site work was performed at.
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
