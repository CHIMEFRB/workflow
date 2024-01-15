"""Workflow Pipelines API."""

from workflow.http.client import Client


class Pipelines(Client):
    """HTTP Client for interacting with the Pipelines backend.

    Args:
        Client (workflow.http.client): The base class for interacting with the backend.

    Returns:
        Results: A client for interacting with the Pipelines backend.
    """

    pass
