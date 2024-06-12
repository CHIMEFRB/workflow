"""Workflow Buckets API."""

from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

from requests.models import Response
from tenacity import retry
from tenacity.stop import stop_after_delay
from tenacity.wait import wait_random

from workflow.http.client import Client
from workflow.utils.logger import get_logger
from workflow.utils.prompt import confirmation

logger = get_logger("workflow.http.buckets")


class Buckets(Client):
    """HTTP Client for interacting with the Buckets backend.

    Args:
        Client (workflow.http.client): The base class for interacting with the backend.

    Returns:
        Buckets: A client for interacting with the Buckets backend.
    """

    @retry(wait=wait_random(min=0.1, max=2), stop=(stop_after_delay(30)))
    def deposit(
        self, works: List[Dict[str, Any]], return_ids: bool = False
    ) -> Union[bool, List[str]]:
        """Deposit works into the buckets backend.

        Args:
            works (List[Dict[str, Any]]): The payload from the Work Object.
            return_ids (bool, optional): Whether to return the ids of the works.
                Defaults to False.

        Raises:
            RequestException: If the request fails.

        Returns:
            Union[bool, List[str]]:
                Whether the request was successful or the ids of the works.

        Examples:
        >>> from chime_frb_api.buckets import Buckets
        >>> from chime_frb_api.tasks import Work
        >>> work = Work(pipeline="sample")
        >>> buckets.deposit([work.payload])
        True
        >>> buckets.deposit([work.payload], return_ids=True)
        ["5f9b5e1b7e5c4b5eb1b""]
        """
        params: Dict[str, Any] = {"return_ids": return_ids}
        with self.session as session:
            response: Response = session.post(
                url=f"{self.baseurl}/work?{urlencode(params)}",
                json=works,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
        if return_ids:
            return response.json()
        return True

    def withdraw(
        self,
        pipeline: Union[str, List[str]],
        event: Optional[List[int]] = None,
        site: Optional[str] = None,
        priority: Optional[int] = None,
        user: Optional[str] = None,
        tags: Optional[List[str]] = None,
        parent: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Withdraw `queued` work from the buckets backend.

        Args:
            pipeline (str | List[str]): The pipeline to withdraw work from.
            event (Optional[List[int]], optional): The event to filter by.
            site (Optional[str], optional): The site to filter by.
            priority (Optional[int], optional): The priority to withdraw from.
            user (Optional[str], optional): The user to filter by.
            tags (Optional[List[str]], optional): The tags to filter by.
            parent (Optional[str], optional): The parent to filter by.

        Raises:
            RequestException: If the request fails.

        Returns:
            Dict[str, Any]: The work withdrawn.
        """
        if isinstance(pipeline, str):
            pipeline = [pipeline]
        query: Dict[str, Any] = {"pipeline": {"$in": pipeline}}
        query.update({"site": site} if site else {})
        query.update({"priority": priority} if priority else {})
        query.update({"user": user} if user else {})
        query.update({"event": {"$in": event}} if event else {})
        query.update({"tags": {"$in": tags}} if tags else {})
        query.update({"config.parent": {"$in": parent}} if parent else {})
        with self.session as session:
            response: Response = session.post(
                url=f"{self.baseurl}/work/withdraw", json=query
            )
            response.raise_for_status()
        return response.json()

    @retry(wait=wait_random(min=0.1, max=2), stop=(stop_after_delay(30)))
    def update(self, works: List[Dict[str, Any]]) -> bool:
        """Update works in the buckets backend.

        Args:
            works (List[Dict[str, Any]]): The payload from the Work Object.

        Returns:
            bool: Whether the works were updated successfully.
        """
        with self.session as session:
            response: Response = session.put(url=f"{self.baseurl}/work", json=works)
            response.raise_for_status()
        return response.json()

    @retry(wait=wait_random(min=0.1, max=2), stop=(stop_after_delay(30)))
    def delete_ids(self, ids: List[str]) -> bool:
        """Delete works from the buckets backend with the given ids.

        Args:
            ids (List[str]): The IDs of the works to delete.

        Returns:
            bool: Whether the works were deleted successfully.
        """
        with self.session as session:
            response: Response = session.delete(
                url=f"{self.baseurl}/work", params={"ids": ids}
            )
            response.raise_for_status()
        return response.json()

    def delete_many(
        self,
        pipeline: str,
        status: Optional[str] = None,
        events: Optional[List[int]] = None,
        tags: Optional[List[str]] = None,
        parent: Optional[str] = None,
        force: bool = False,
    ) -> bool:
        """Delete works belonging to a pipeline from the buckets backend.

        If a status is provided, only works with that status will be deleted.
        If an event number is provided, only works with that event will be deleted.

        Args:
            pipeline (str): The pipeline to delete works from.
            status (Optional[List[str]]): The status to delete works with.
                e.g. ["queued"].
            event (Optional[List[int]]): The event to delete works with.
            force (bool, optional): Whether to force the deletion without requiring
                user confirmation. Defaults to False.

        Returns:
            bool: Whether any works were deleted.
        """
        query: Dict[str, Any] = {"pipeline": pipeline}
        query.update({"status": status} if status else {})
        query.update({"event": {"$in": events}} if events else {})
        query.update({"tags": {"$in": tags}} if tags else {})
        query.update({"config.parent": parent} if parent else {})
        projection = {"id": True}
        result = self.view(query, projection)
        ids: List[str] = []
        if result:
            ids = [work["id"] for work in result]
        # Get user confirmation before deleting
        if ids and not force:
            msg = f"Are you sure you want to delete {len(ids)} works?"
            # Display upto 5 ids only
            msg += "\n\tids: " + ", ".join(ids[:5]) + ("..." if len(ids) > 5 else "")
            msg += "\n\tstatus: " + status if status else ""
            msg += "\n\tevents: " + ", ".join(map(str, events)) if events else ""
            msg += "\n\ttags: " + ", ".join(tags) if tags else ""
            msg += "\n\tparent: " + parent if parent else ""
            force = confirmation(msg)
        if ids and force:
            return self.delete_ids(ids)
        return False

    def status(self, pipeline: Optional[str] = None) -> Dict[str, Any]:
        """View the status of the buckets backend.

        If overall is True, the status of all pipelines will be returned.

        Args:
            pipeline (Optional[str], optional): The pipeline to return the status of.

        Returns:
            List[Dict[str, Any]]: The status of the buckets backend.
        """
        url: str = f"{self.baseurl}/status"
        if pipeline:
            url = f"{url}/details/{pipeline}"
        with self.session as session:
            response: Response = session.get(url=url)
            response.raise_for_status()
        return response.json()

    def pipelines(self) -> List[str]:
        """View the current pipelines in the buckets backend.

        Returns:
            List[str]: The current pipelines.
        """
        with self.session as session:
            response: Response = session.get(url=f"{self.baseurl}/status/pipelines")
            response.raise_for_status()
        return response.json()

    def view(
        self,
        query: Dict[str, Any],
        projection: Dict[str, bool] = {},
        skip: int = 0,
        limit: Optional[int] = 100,
    ) -> List[Dict[str, Any]]:
        """View works in the buckets backend.

        Args:
            query (Dict[str, Any]): The query to filter the works with.
            projection (Dict[str, bool]): The projection to use to map the output.
            skip (int, optional): The number of works to skip. Defaults to 0.
            limit (Optional[int], optional): The number of works to limit to.
                Defaults to 100.

        Returns:
            List[Dict[str, Any]]: The works matching the query.
        """
        projection.update({"_id": False})
        payload = {
            "query": query,
            "projection": projection,
            "skip": skip,
            "limit": limit,
        }
        with self.session as session:
            response: Response = session.post(url=f"{self.baseurl}/view", json=payload)
            response.raise_for_status()
        return response.json()

    def audit(self) -> Dict[str, Any]:
        """Audit work buckets backend.

        The audit process retries failed work, expires any work past the
        expiration time and checks for any stale work older than 7 days.

        Returns:
            Dict[str, Any]: The audit results.
        """
        reply: Dict[str, Any] = {}
        urls: Dict[str, str] = {
            "failed": "/audit/failed",
            "expired": "/audit/expired",
            "stale": "/audit/stale/7.0",
        }
        with self.session as session:
            for process, url in urls.items():
                response: Response = session.get(url=f"{self.baseurl}{url}")
                response.raise_for_status()
                reply[process] = response.json()
        return reply

    def info(self) -> Dict[str, Any]:
        """Get the version of the buckets backend.

        Returns:
            Dict[str, Any]: The version of the buckets backend.
        """
        client_info = self.model_dump()
        with self.session as session:
            response: Response = session.get(url=f"{self.baseurl}/version")
            response.raise_for_status()
        server_info = response.json()
        return {"client": client_info, "server": server_info}
