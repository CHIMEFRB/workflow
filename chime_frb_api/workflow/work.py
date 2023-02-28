"""Work Object."""

from json import loads
from os import environ
from time import time
from typing import Any, Dict, List, Literal, Optional, Union
from warnings import warn

from pydantic import BaseModel, Field, StrictFloat, StrictStr, root_validator
from tenacity import retry
from tenacity.stop import stop_after_delay
from tenacity.wait import wait_random

from chime_frb_api.modules.buckets import Buckets


class Archive(BaseModel):
    """Work Object Archive Configuration.

    Args:
        BaseModel (BaseModel): Pydantic BaseModel.

    Attributes:
        results (bool): Archive results for the work.
        products (Literal["pass", "copy", "move", "delete", "upload"]):
            Archive strategy for the products.
        plots (Literal["pass", "copy", "move", "delete", "upload"]):
            Archive strategy for the plots.
        logs (Literal["pass", "copy", "move", "delete", "upload"]):
            Archive strategy for the logs.
    """

    results: bool = Field(
        default=True,
        description="Archive results for the work.",
    )
    products: Literal["pass", "copy", "move", "delete", "upload"] = Field(
        default="copy",
        description="Archive strategy for the products.",
    )
    plots: Literal["pass", "copy", "move", "delete", "upload"] = Field(
        default="copy",
        description="Archive strategy for the plots.",
    )
    logs: Literal["pass", "copy", "move", "delete", "upload"] = Field(
        default="move",
        description="Archive strategy for the logs.",
    )


class WorkConfig(BaseModel):
    """Work Object Configuration.

    Args:
        BaseModel (BaseModel): Pydantic BaseModel.
    """

    class Config:
        """Pydantic Config."""

        validate_all = True
        validate_assignment = True

    archive: Archive = Archive()
    metrics: bool = Field(
        default=False,
        description="Generate grafana metrics for the work.",
    )
    pipeline: Optional[str] = Field(
        default=None,
        description="ID of the parent workflow pipeline.",
        example="5f9b5c5d7b54b5a9c5e5b5c5",
    )
    orgs: List[str] = Field(
        default=["chimefrb"],
        description="""
        List of organization[s] the work belongs to.
        Maps to the Github organization.
        """,
        example=["chimefrb", "chime-sps"],
    )
    teams: Optional[List[str]] = Field(
        default=None,
        description="""
        List of team[s] the work belongs to.
        Maps to the Github team within the organization.
        """,
        example=["frb-tsars", "frb-ops"],
    )
    token: Optional[str] = Field(
        default=next(
            (
                value
                for value in [
                    environ.get("GITHUB_TOKEN"),
                    environ.get("WORKFLOW_TOKEN"),
                    environ.get("GITHUB_PAT"),
                    environ.get("GITHUB_ACCESS_TOKEN"),
                    environ.get("GITHUB_PERSONAL_ACCESS_TOKEN"),
                    environ.get("GITHUB_OAUTH_TOKEN"),
                    environ.get("GITHUB_OAUTH_ACCESS_TOKEN"),
                ]
                if value is not None
            ),
            None,
        ),
        description="Github Personal Access Token.",
        example="ghp_1234567890abcdefg",
        repr=False,
    )


class Work(BaseModel):
    """Work Object.

    Args:
        BaseModel (BaseModel): Pydantic BaseModel.

    Attributes:
        pipeline (str): Name of the pipeline. Automatically reformated to hyphen-case.
        site (str): Site where the work will be performed.
        user (str): Github ID who created the work.
        function (str): Name of the function to run as `function(**parameters)`.
        parameters (Dict[str, Any]): Parameters to pass to the function.
        command (List[str]): Command to run as `subprocess.run(command)`.
        results (Dict[str, Any]): Results of the work.
        products (Dict[str, Any]): Products of the work.
        plots (Dict[str, Any]): Plots of the work.
        event (List[str]): List of CHIME/FRB events associated with the work.
        tags (List[str]): List of tags associated with the work.
        timeout (float): Timeout in seconds for the work.
        retries (int): Number of retries for the work.
        priority (int): Priority of the work.
        config (WorkConfig): Work configuration.
        id (str): ID of the work.
        creation (float): Creation time of the work.
        start (float): Start time of the work.
        stop (float): Stop time of the work.
        status (str): Status of the work.

    Deprecated Attributes:
        precursors (List[str]): List of precursors of the work.
        path (str): Path to the work.
        archive (bool): Archive configuration.
        group (List[str]): Group of the work.

    Raises:
        ValueError: If the work is not valid.

    Returns:
        Work: Work object.

    Example:
        ```python
        from chime_frb_api.workflow import Work
        work = Work(pipeline="test")
        work.deposit(return_ids=True)
    """

    class Config:
        """Pydantic Config."""

        validate_all = True
        validate_assignment = True

    ###########################################################################
    # Required Attributes. Set by user.
    ###########################################################################
    pipeline: StrictStr = Field(
        ...,
        min_length=1,
        description="Name of the pipeline. Automatically reformated to hyphen-case.xw",
        example="example-pipeline",
    )
    site: Literal[
        "chime", "kko", "gbo", "hco", "canfar", "cedar", "local", "aro", "allenby"
    ] = Field(
        default=environ.get("WORKFLOW_SITE", "local"),
        description="Site where the work will be performed.",
        example="chime",
    )
    user: Optional[StrictStr] = Field(
        default=None, description="User ID who created the work.", example="shinybrar"
    )

    ###########################################################################
    # Optional attributes, might be provided by the user.
    ###########################################################################
    function: str = Field(
        default=None,
        description="""
        Name of the function to run as `function(**parameters)`.
        Only either `function` or `command` can be provided.
        """,
        example="requests.get",
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="""
        Parameters to pass the pipeline function.
        """,
        example={"event_number": 9385707},
    )
    command: List[str] = Field(
        default=None,
        description="""
        Command to run as `subprocess.run(command)`.
        Note, only either `function` or `command` can be provided.
        """,
        example=["python", "example.py", "--example", "example"],
    )
    results: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Results of the work performed, if any.",
        example={"dm": 100.0, "snr": 10.0},
    )
    products: Optional[List[StrictStr]] = Field(
        default=None,
        description="""
        Name of the non-human-readable data products generated by the pipeline.
        """,
        example=["spectra.h5", "dm_vs_time.png"],
    )
    plots: Optional[List[StrictStr]] = Field(
        default=None,
        description="""
        Name of visual data products generated by the pipeline.
        """,
        example=["waterfall.png", "/arc/projects/chimefrb/9385707/9385707.png"],
    )
    event: Optional[List[int]] = Field(
        default=None,
        description="CHIME/FRB Event ID[s] the work was performed against.",
        example=[9385707, 9385708],
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="""
        Searchable tags for the work. Merged with values from env WORKFLOW_TAGS.
        """,
        example=["dm-analysis"],
    )
    timeout: int = Field(
        default=3600,
        ge=1,
        le=86400,
        description="""
        Timeout in seconds for the work to finish.
        Defaults 3600s (1 hr) with range of [1, 86400] (1s-24hrs).
        """,
        example=7200,
    )
    retries: int = Field(
        default=2,
        lt=6,
        description="Number of retries before giving up. Defaults to 2.",
        example=4,
    )
    priority: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Priority of the work. Defaults to 3.",
        example=1,
    )
    config: WorkConfig = WorkConfig()
    ###########################################################################
    # Deprecated attributes, will be removed in future versions.
    ###########################################################################
    precursors: Optional[List[Dict[StrictStr, StrictStr]]] = Field(
        default=None,
        deprecated=True,
        description="This field has been deprecated.",
    )
    path: Optional[str] = Field(
        default=None, description="This field has been deprecated.", deprecated=True
    )
    archive: bool = Field(
        default=None,
        description="""
        This field has been deprecated. Use `config.archive` instead.
        """,
        example=True,
    )
    group: Optional[StrictStr] = Field(
        default=None,
        description="This field has been deprecated. Use config.orgs|teams instead.",
    )

    ###########################################################################
    # Automaticaly set attributes
    ###########################################################################
    id: Optional[StrictStr] = Field(
        default=None, description="Work ID created by the database."
    )
    creation: Optional[StrictFloat] = Field(
        default=None, description="Unix timestamp of when the work was created."
    )
    start: Optional[StrictFloat] = Field(
        default=None,
        description="Unix timestamp when the work was started, reset at each attempt.",
    )
    stop: Optional[StrictFloat] = Field(
        default=None,
        description="Unix timestamp when the work was stopped, reset at each attempt.",
    )
    attempt: int = Field(
        default=0, ge=0, description="Attempt number at performing the work."
    )
    status: Literal["created", "queued", "running", "success", "failure"] = Field(
        default="created", description="Status of the work."
    )
    ###########################################################################
    # Attribute setters for the work attributes
    ###########################################################################

    @root_validator
    def post_init(cls, values: Dict[str, Any]):
        """Initialize work attributes after validation."""
        # Change pipeline to be lowercase and replace spaces/underscores with dashes
        values["pipeline"] = (
            values["pipeline"].lower().replace(" ", "-").replace("_", "-")
        )
        # Set creation time if not already set
        if values.get("creation") is None:
            values["creation"] = time()
        # Update tags from environment variable WORKFLOW_TAGS
        if environ.get("WORKFLOW_TAGS"):
            env_tags: List[str] = str(environ.get("WORKFLOW_TAGS")).split(",")
            # If tags are already set, append the new ones
            if values.get("tags"):
                values["tags"] = values["tags"] + env_tags
            else:
                values["tags"] = env_tags
            # Remove duplicates
            values["tags"] = list(set(values["tags"]))

        # Check if both command and function are set
        if values.get("command") and values.get("function"):
            raise ValueError("command and function cannot be set together.")

        if not values.get("config").token:  # type: ignore
            msg = "token not set, this will be required in v3.0.0."
            warn(
                FutureWarning(msg),
                stacklevel=2,
            )

        # Display deprecation warning for precursors & config
        deprecations: List[str] = ["precursors", "path", "archive", "group"]
        for deprecation in deprecations:
            msg = f"`{deprecation}` has been deprecated and will be removed in v3.0.0."
            if values.get(deprecation):
                warn(msg, DeprecationWarning, stacklevel=2)
                values[deprecation] = None

        if values.get("site") == "allenby":
            warn(
                """\n
                Site `allenby` been changed to `kko`.
                With release v3.0.0 this will be a required change.
                """,
                FutureWarning,
                stacklevel=2,
            )
            values["site"] = "kko"
        return values

    ###########################################################################
    # Work methods
    ###########################################################################

    @property
    def payload(self) -> Dict[str, Any]:
        """Return the dictioanary representation of the work.

        Returns:
            Dict[str, Any]: The payload of the work.
            Non-instanced attributes are excluded from the payload.
        """
        payload: Dict[str, Any] = self.dict(exclude={"token": True})
        return payload

    @classmethod
    def from_json(cls, json_str: str) -> "Work":
        """Create a work from a json string.

        Args:
            json_str (str): The json string.

        Returns:
            Work: The work.
        """
        return cls(**loads(json_str))

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Work":
        """Create a work from a dictionary.

        Args:
            payload (Dict[str, Any]): The dictionary.

        Returns:
            Work: The work.
        """
        return cls(**payload)

    ###########################################################################
    # HTTP Methods
    ###########################################################################

    @classmethod
    def withdraw(
        cls,
        pipeline: str,
        event: Optional[List[int]] = None,
        site: Optional[str] = None,
        priority: Optional[int] = None,
        user: Optional[str] = None,
        **kwargs: Dict[str, Any],
    ) -> Optional["Work"]:
        """Withdraw work from the buckets backend.

        Args:
            pipeline (str): Name of the pipeline.
            **kwargs (Dict[str, Any]): Keyword arguments for the Buckets API.

        Returns:
            Work: Work object.
        """
        buckets = Buckets(**kwargs)  # type: ignore
        payload = buckets.withdraw(
            pipeline=pipeline, event=event, site=site, priority=priority, user=user
        )
        if payload:
            return cls.from_dict(payload)
        return None

    @retry(wait=wait_random(min=0.5, max=1.5), stop=(stop_after_delay(30)))
    def deposit(
        self, return_ids: bool = False, **kwargs: Dict[str, Any]
    ) -> Union[bool, List[str]]:
        """Deposit work to the buckets backend.

        Args:
            **kwargs (Dict[str, Any]): Keyword arguments for the Buckets API.

        Returns:
            bool: True if successful, False otherwise.
        """
        buckets = Buckets(**kwargs)  # type: ignore
        return buckets.deposit(works=[self.payload], return_ids=return_ids)

    @retry(wait=wait_random(min=0.5, max=1.5), stop=(stop_after_delay(30)))
    def update(self, **kwargs: Dict[str, Any]) -> bool:
        """Update work in the buckets backend.

        Args:
            **kwargs (Dict[str, Any]): Keyword arguments for the Buckets API.

        Returns:
            bool: True if successful, False otherwise.
        """
        buckets = Buckets(**kwargs)  # type: ignore
        return buckets.update([self.payload])

    @retry(wait=wait_random(min=0.5, max=1.5), stop=(stop_after_delay(30)))
    def delete(self, **kwargs: Dict[str, Any]) -> bool:
        """Delete work from the buckets backend.

        Args:
            ids (List[str]): List of ids to delete.

        Returns:
            bool: True if successful, False otherwise.
        """
        buckets = Buckets(**kwargs)  # type: ignore
        return buckets.delete_ids([str(self.id)])
