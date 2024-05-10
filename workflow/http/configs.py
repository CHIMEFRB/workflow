"""Workflow Pipelines API."""

from json import dumps
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from requests.models import Response
from tenacity import retry
from tenacity.stop import stop_after_attempt, stop_after_delay
from tenacity.wait import wait_random

from workflow.http.client import Client
from workflow.utils.decorators import try_request


class Configs(Client):
    """HTTP Client for interacting with the Configs endpoints on pipelines backend.

    Args:
        Client (workflow.http.client): The base class for interacting with the backend.

    Returns:
        Configs: A client for interacting with workflow-pipelines.
    """

    @retry(
        reraise=True,
        wait=wait_random(min=1.5, max=3.5),
        stop=(stop_after_delay(5) | stop_after_attempt(1)),
    )
    @try_request
    def deploy(self, data: Dict[str, Any]):
        """Deploys a Config from payload data.

        Parameters
        ----------
        data : Dict[str, Any]
            YAML data.

        Returns
        -------
        List[str]
            ID of Config object generated.
        """
        with self.session as session:
            url = f"{self.baseurl}/v2/configs"
            response: Response = session.post(url, json=data)
            response.raise_for_status()
        return response.json()

    @try_request
    def count(self) -> Dict[str, Any]:
        """Count all documents in a collection.

        Returns
        -------
        Dict[str, Any]
            Dictionary with count.
        """
        with self.session as session:
            response: Response = session.get(
                url=f"{self.baseurl}/v2/configs/count?database=configs"
            )
            response.raise_for_status()
        return response.json()

    @try_request
    def get_configs(
        self,
        config_name: str,
        query: Optional[str] = "{}",
        projection: Optional[str] = "{}",
    ) -> List[Dict[str, Any]]:
        """View the current configurations on pipelines backend.

        Parameters
        ----------
        config_name : str
            Config name, by default None
        query : str, optional
            Query payload.
        projection : str, optional
            Query projection.

        Returns
        -------
        List[Dict[str, Any]]
            List of Config payloads.
        """
        with self.session as session:
            # ? When using urlencode, internal dict object get single-quoted
            # ? This can trigger error on workflow-pipelines backend
            params = {"projection": projection, "query": query}
            if config_name:
                params.update({"name": config_name})
            url = f"{self.baseurl}/v2/configs?{urlencode(params)}"
            response: Response = session.get(url=url)
            response.raise_for_status()
        return response.json()

    @retry(
        reraise=True,
        wait=wait_random(min=1.5, max=3.5),
        stop=(stop_after_delay(5) | stop_after_attempt(1)),
    )
    @try_request
    def remove(self, config: str, id: str) -> Response:
        """Removes a cancelled pipeline configuration.

        Parameters
        ----------
        config : str
            Config name.
        id : str
            Config ID.

        Returns
        -------
        List[Dict[str, Any]]
            Response payload.
        """
        with self.session as session:
            query = {"id": id}
            params = {"query": dumps(query), "name": config}
            url = f"{self.baseurl}/v2/configs?{urlencode(params)}"
            response: Response = session.delete(url=url)
            response.raise_for_status()
        return response

    @retry(wait=wait_random(min=0.5, max=1.5), stop=(stop_after_delay(30)))
    @try_request
    def stop(self, pipeline: str, id: str) -> List[Dict[str, Any]]:
        """Stops the manager for a PipelineConfig.

        Parameters
        ----------
        pipeline : str
            Pipeline name.
        id : str
            PipelineConfig ID.

        Returns
        -------
        List[Dict[str, Any]]
            List of stopped PipelineConfig objects.
        """
        with self.session as session:
            query = {"id": id}
            params = {"query": dumps(query), "name": pipeline}
            url = f"{self.baseurl}/v2/configs/cancel?{urlencode(params)}"
            response: Response = session.put(url)
            response.raise_for_status()
        if response.status_code == 304:
            return []
        return response.json()

    @try_request
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
