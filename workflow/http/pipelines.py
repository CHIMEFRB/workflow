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


class Pipelines(Client):
    """HTTP Client for interacting with the Pipelines backend.

    Args:
        Client (workflow.http.client): The base class for interacting with the backend.

    Returns:
        Pipelines: A client for interacting with the Pipelines backend.
    """

    @retry(
        reraise=True,
        wait=wait_random(min=1.5, max=3.5),
        stop=(stop_after_delay(5) | stop_after_attempt(1)),
    )
    @try_request
    def deploy(self, data: Dict[str, Any]):
        """Deploys a PipelineConfig from payload data.

        Parameters
        ----------
        data : Dict[str, Any]
            YAML data.

        Returns
        -------
        List[str]
            IDs of PipelineConfig objects generated.
        """
        with self.session as session:
            url = f"{self.baseurl}/v1/pipelines"
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
            response: Response = session.get(url=f"{self.baseurl}/v1/pipelines/count")
            response.raise_for_status()
        return response.json()

    @try_request
    def list_pipeline_configs(
        self, config_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """View the current pipeline configurations in the pipelines backend.

        Parameters
        ----------
        config_name : Optional[str], optional
            PipelineConfig name, by default None

        Returns
        -------
        List[Dict[str, Any]]
            List of PipelineConfig payloads.
        """
        with self.session as session:
            url = (
                f"{self.baseurl}/v1/pipelines"
                if config_name is None
                else f'{self.baseurl}/v1/pipelines?query={{"name":"{config_name}"}}'
            )
            response: Response = session.get(url=url)
            response.raise_for_status()
        return response.json()

    @try_request
    def get_pipeline_config(
        self, collection: str, query: Dict[str, Any], projection: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gets details for one pipeline configuration.

        Parameters
        ----------
        collection : str
            PipelineConfig name.
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
                "query": dumps(query),
                "name": collection,
                "projection": dumps(projection),
            }
            url = f"{self.baseurl}/v1/pipelines?{urlencode(params)}"
            response: Response = session.get(url=url)
            response.raise_for_status()
        return response.json()[0]

    @retry(
        reraise=True,
        wait=wait_random(min=1.5, max=3.5),
        stop=(stop_after_delay(5) | stop_after_attempt(1)),
    )
    @try_request
    def remove(self, pipeline: str, id: str) -> Response:
        """Removes a cancelled pipeline configuration.

        Parameters
        ----------
        pipeline : str
            PipelineConfig name.
        id : str
            PipelineConfig ID.

        Returns
        -------
        List[Dict[str, Any]]
            Response payload.
        """
        with self.session as session:
            query = {"id": id}
            params = {"query": dumps(query), "name": pipeline}
            url = f"{self.baseurl}/v1/pipelines?{urlencode(params)}"
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
            url = f"{self.baseurl}/v1/pipelines/cancel?{urlencode(params)}"
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
