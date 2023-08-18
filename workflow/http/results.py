"""Workflow Results API."""

from workflow.http.client import Client


class Results(Client):
    """HTTP Client for interacting with the Results backend.

    Args:
        Client (workflow.http.client): The base class for interacting with the backend.

    Returns:
        Results: A client for interacting with the Buckets backend.
    """

    pass
