"""Workflow Pipelines API."""

from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from requests.models import Response

from workflow.http.client import Client
from workflow.utils.decorators import try_request


class Pipelines(Client):
    """HTTP Client for interacting with the Pipelines backend.

    Args:
        Client (workflow.http.client): The base class for interacting with the backend.

    Returns:
        Pipelines: A client for interacting with the Pipelines backend.
    """

    @try_request
    def count(self) -> Dict[str, Any]:
        """Count all documents in a collection.

        Returns
        -------
        Dict[str, Any]
            Dictionary with count.
        """
        with self.session as session:
            params = {"database": "pipelines"}
            response: Response = session.get(
                url=f"{self.baseurl}/configs/count?{urlencode(params)}"
            )
            response.raise_for_status()
        return response.json()

    def list_pipelines(self, name: Optional[str] = None) -> List[Dict[str, Any]]:
        """View the current pipeline configurations in the pipelines backend.

        Parameters
        ----------
        name : Optional[str], optional
            Config name, by default None

        Returns
        -------
        List[Dict[str, Any]]
            List of PipelineConfig payloads.
        """
        with self.session as session:
            params = {"database": "pipelines"}
            if name:
                params.update({"name": name})
            url = f"{self.baseurl}/configs?{urlencode(params)}"
            response: Response = session.get(url=url)
            response.raise_for_status()
        return response.json()

    def get_pipelines(self, name: str, query: str, projection: str) -> Dict[str, Any]:
        """Gets details for one pipeline configuration.

        Parameters
        ----------
        name : str
            Config name.
        query : Dict[str, Any]
            Dictionary with search parameters.
        projection : Dict[str, Any]
            Dictionary with projection parameters.

        Returns
        -------
        Dict[str, Any]
            Pipeline configuration payload.
        """
        with self.session as session:
            params = {
                "query": query,
                "name": name,
                "projection": projection,
                "database": "pipelines",
            }
            url = f"{self.baseurl}/configs?{urlencode(params)}"
            response: Response = session.get(url=url)
            response.raise_for_status()
        return response.json()

    def info(self) -> Dict[str, Any]:
        """Get the version of the pipelines backend.

        Returns
        -------
        Dict[str, Any]
            Pipelines backend info.
        """
        client_info = self.model_dump()
        with self.session as session:
            response: Response = session.get(url=f"{self.baseurl}/version")
            response.raise_for_status()
        server_info = response.json()
        return {"client": client_info, "server": server_info}

    def status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get the status of all pipelines.

        Parameters
        ----------
        params : Dict[str, Any]
            Dictionary with query parameters.

        Returns
        -------
        Dict[str, Any]
            Dictionary with pipeline status.
        """
        with self.session as session:
            response: Response = session.get(
                url=f"{self.baseurl}/status", params=params
            )
            response.raise_for_status()
        return response.json()
