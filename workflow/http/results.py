"""Workflow Results API."""

from typing import Any, Dict, List

from requests.models import Response

from workflow.http.client import Client
from workflow.utils.decorators import try_request


class Results(Client):
    """HTTP Client for interacting with the Results backend.

    Args:
        Client (workflow.http.client): The base class for interacting with the backend.

    Returns:
        Results: A client for interacting with the Buckets backend.
    """

    @try_request
    def info(self) -> Dict[str, Any]:
        """Get the version of the results backend.

        Returns:
            Dict[str, Any]: The version of the results backend.
        """
        client_info = self.model_dump()
        with self.session as session:
            response: Response = session.get(url=f"{self.baseurl}/version")
            response.raise_for_status()
        server_info = response.json()
        return {"client": client_info, "server": server_info}

    @try_request
    def count(self) -> Dict[str, Any]:
        """Gets count of pipelines on results backend.

        Returns
        -------
        Dict[str, Any]
            Count payload.
        """
        with self.session as session:
            response: Response = session.get(url=f"{self.baseurl}/status")
            response.raise_for_status()
        return response.json()

    @try_request
    def view(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Queries details for a specific Result.

        Parameters
        ----------
        payload : Dict[str, Any]
            Query payload.

        Returns
        -------
        List[Dict[str, Any]]
            Filtered results.
        """
        with self.session as session:
            response: Response = session.post(url=f"{self.baseurl}/view", json=payload)
            response.raise_for_status()
        return response.json()
