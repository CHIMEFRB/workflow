"""Workflow Schedules API."""

from json import dumps
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from requests.models import Response
from tenacity import retry
from tenacity.stop import stop_after_attempt, stop_after_delay
from tenacity.wait import wait_random

from workflow.http.client import Client
from workflow.utils.decorators import try_request


class Schedules(Client):
    """HTTP Client for interacting with the Schedules endpoints.

    Args:
        Client (workflow.http.client): The base class for interacting with the backend.

    Returns:
        Schedules: A client for interacting with the Schedule endpoints.
    """

    @retry(
        reraise=True,
        wait=wait_random(min=1.5, max=3.5),
        stop=(stop_after_delay(5) | stop_after_attempt(1)),
    )
    def deploy(self, data: Dict[str, Any]):
        """Deploys a Schedule from payload data.

        Parameters
        ----------
        data : Dict[str, Any]
            YAML data.

        Returns
        -------
        List[str]
            IDs of Schedule objects generated.
        """
        with self.session as session:
            url = f"{self.baseurl}/schedule"
            response: Response = session.post(url, json=data)
            response.raise_for_status()
        return response.json()

    @try_request
    def get_schedule(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Gets details for one Schedule.

        Parameters
        ----------
        query : Dict[str, Any]
            Dictionary with search parameters.

        Returns
        -------
        Dict[str, Any]
            Schedule payload.
        """
        with self.session as session:
            params = {"query": dumps(query)}
            url = f"{self.baseurl}/schedule?{urlencode(params)}"
            response: Response = session.get(url=url)
            response.raise_for_status()
        return response.json()[0]

    @retry(
        reraise=True,
        wait=wait_random(min=1.5, max=3.5),
        stop=(stop_after_delay(5) | stop_after_attempt(1)),
    )
    @try_request
    def remove(self, id: str) -> Response:
        """Removes a schedule.

        Parameters
        ----------
        id : str
            Schedule ID.

        Returns
        -------
        List[Dict[str, Any]]
            Response payload.
        """
        with self.session as session:
            query = {"id": id}
            params = {"query": dumps(query)}
            url = f"{self.baseurl}/schedule?{urlencode(params)}"
            response: Response = session.delete(url=url)
            response.raise_for_status()
        return response

    @try_request
    def list_schedules(self, name: Optional[str]) -> List[Dict[str, Any]]:
        """Gets the list of all schedules.

        Parameters
        ----------
        name : Optional[str]
            Schedule name.

        Returns
        -------
        List[Dict[str, Any]]
            List of schedule payloads.
        """
        with self.session as session:
            query = dumps({"config.name": name})
            projection = dumps(
                {
                    "id": True,
                    "status": True,
                    "lives": True,
                    "has_spawned": True,
                    "next_time": True,
                    "crontab": True,
                    "config.name": True,
                }
            )
            url = (
                f"{self.baseurl}/schedule?projection={projection}"
                if name is None
                else f"{self.baseurl}/schedule?query={query}&projection={projection}"
            )
            response: Response = session.get(url=url)
            response.raise_for_status()
        return response.json()

    @try_request
    def count_schedules(self, schedule_name: Optional[str] = None) -> Dict[str, Any]:
        """Count schedules per pipeline name.

        Parameters
        ----------
        schedule_name : Optional[str], optional
            Schedule name, by default None

        Returns
        -------
        Dict[str, Any]
            Count payload.
        """
        with self.session as session:
            query = dumps({"name": schedule_name})
            url = (
                f"{self.baseurl}/schedule/count"
                if not schedule_name
                else f"{self.baseurl}/schedule/count?query={query}"
            )
            response: Response = session.get(url=url)
            response.raise_for_status()
        return response.json()
