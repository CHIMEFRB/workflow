"""Workflow Results API."""

from typing import Any, Dict, List

from requests.models import Response

from workflow.http.client import Client
from workflow.utils.decorators import try_request
from workflow.utils.prompt import confirmation


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

    def deposit(self, works: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Deposit works into the results backend.

        Args:
            works (List[Dict[str, Any]]): A list of payloads from Work Objects.

        Note:
            This method is not intended for direct use by the user.
            Work status must be 'success' or 'failure'.

        Raises:
            AssertionError: If work status is not 'success' or 'failure'.

        Returns:
            Dict[str, bool]: Dictionary of deposit results for each pipeline.

        Examples:
        >>> from workflow.http.results import Results
        >>> from workflow.definitions.work import Work
        >>> results = Results()
        >>> work = Work.withdraw(pipeline="test)
        >>> work.status = "success"
        >>> status = results.deposit([work.payload])
        """
        for work in works:
            assert work["status"] in [
                "success",
                "failure",
            ], "work.status must be 'success' or 'failure'"
        with self.session as session:
            response: Response = session.post(url=f"{self.baseurl}/results", json=works)
            response.raise_for_status()
            return response.json()

    def update(self, works: List[Dict[str, Any]]) -> bool:
        """Update works in the results backend.

        Args:
            works (List[Dict[str, Any]]): A list of payloads from Work Objects.

        Note:
            This method is not intended for direct use by the user.
            Work status must be 'success' or 'failure'.

        Returns:
            bool: Whether the works were updated successfully.
        """
        with self.session as session:
            response: Response = session.put(url=f"{self.baseurl}/results", json=works)
            response.raise_for_status()
        return response.json()

    def delete_ids(self, pipeline: str, ids: List[str]) -> bool:
        """Delete results from the results backend.

        Args:
            pipeline (str): Name of pipeline.
            ids (List[str]): The IDs of the works to delete.

        Returns:
            bool: Whether the results were deleted successfully.
        """
        with self.session as session:
            response: Response = session.delete(
                url=f"{self.baseurl}/results", params={pipeline: ids}
            )
            response.raise_for_status()
        return response.json()

    def view(
        self,
        pipeline: str,
        query: Dict[str, Any],
        projection: Dict[str, bool] = {},
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """View works in the results backend.

        Args:
            pipeline (str): Name of pipeline.
            query (Dict[str, Any]): MongoDB query.
            projection (Dict[str, bool], optional): MongoDB projection.
                Defaults to {}.
            skip (int, optional): Number of works to skip.
                Defaults to 0.
            limit (int, optional): Number of works to limit to. -1 for no limit.
                Defaults to 100.

        Returns:
            List[Dict[str, Any]]: List of work payloads.
        """
        query["pipeline"] = pipeline
        if limit == -1:
            limit = 0
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

    def count(
        self,
        pipeline: str,
        query: Dict[str, Any],
    ) -> int:
        """Get count of results filtered by the query.

        Args:
            pipeline (str): Name of pipeline.
            query (Dict[str, Any]): MongoDB query.

        Returns:
            int: The number of results that match the query.
        """
        query["pipeline"] = pipeline
        payload = {
            "query": query,
        }
        with self.session as session:
            response: Response = session.post(
                url=f"{self.baseurl}/view/count", json=payload
            )
            response.raise_for_status()
        return response.json()

    def status(self) -> Dict[str, int]:
        """Get the status of the results backend.

        Returns:
            Dict[str, int]: The status of the results backend.
        """
        with self.session as session:
            response: Response = session.get(url=f"{self.baseurl}/status")
            response.raise_for_status()
        return response.json()

    def get_by_count(self, pipeline: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get results by count from the specified pipeline.

        Args:
            pipeline (str): The name of the pipeline.
            count (int): The number of results to get. Defaults to 10.

        Returns:
            List[Dict[str, Any]]: Retrieved results.
        """
        response = self.view(
            pipeline=pipeline, query={}, projection={}, skip=0, limit=count
        )
        return response

    def get_by_id(self, pipeline: str, ids: List[str]) -> List[Dict[str, Any]]:
        """Get results by ID from the specified pipeline.

        Args:
            pipeline (str): The name of the pipeline.
            ids (List[str]): The IDs of the results to get.

        Returns:
            List[Dict[str, Any]]: Retrieved results.
        """
        response = self.view(
            pipeline=pipeline, query={"id": {"$in": ids}}, projection={}, limit=-1
        )
        return response

    def get_by_event(self, pipeline: str, event_number: int) -> List[Dict[str, Any]]:
        """Get work filtered by event number from the results backend.

        Args:
            pipeline (str): The name of the pipeline.
            event_number (int): The event number of the event.

        Returns:
            List[Dict[str, Any]]: Retrieved results.
        """
        return self.view(
            pipeline=pipeline,
            query={"event": [event_number]},
            projection={},
            limit=-1,
        )

    def get_locked(
        self, pipeline: str, skip: int = 0, count: int = 10
    ) -> List[Dict[str, Any]]:
        """Get work that is locked from the results backend.

        Args:
            pipeline (str): The name of the pipeline.
            skip (int, optional): The number of results to skip. Defaults to 0.
            count (int, optional): The maximum number of results. Defaults to 10.

        Note:
            Only results with valid results, plots and products are returned.

        Returns:
            List[Dict[str, Any]]: A list of the locked results.
        """
        return self.view(
            pipeline=pipeline,
            query={"results.locked": True},
            projection={
                "event": True,
                "plots": True,
                "products": True,
                "results": True,
            },
            skip=skip,
            limit=count,
        )

    def get_locked_count(self, pipeline: str) -> int:
        """Retrieves the count of locked results.

        Args:
            pipeline (str): The name of the pipeline.

        Returns:
            int: The count of locked results.
        """
        return self.count(
            pipeline=pipeline,
            query={"results.locked": True},
        )

    def lock(self, pipeline: str, ids: List[str]) -> bool:
        """Lock results.

        Note:
            A locked result cannot be deleted or updated.

        Args:
            pipeline (str): The name of the pipeline.
            ids (List[str]): The IDs of the results to lock.

        Returns:
            Boolean: True if successful, False if not.
        """
        payload: List[Dict[str, Any]] = self.get_by_id(pipeline, ids)
        for work in payload:
            work["results"]["locked"] = True
        response = self.update(payload)
        return True if response else False

    def unlock(self, pipeline: str, ids: List[str], force: bool = False) -> bool:
        """Unlock results.

        Args:
            pipeline (str): The pipeline name.
            ids (List[str]): The IDs of the results to unlock.
            force (bool): Force the unlock. Defaults to False.

        Returns:
            Bool: True if successful, False if not.
        """
        msg = "Unlocking results will allow them to be deleted or updated."
        if force or confirmation(msg):
            works = self.get_by_id(pipeline, ids)
            for work in works:
                work["results"]["locked"] = False
            response = self.update(works)
            return True if response else False
        return False
