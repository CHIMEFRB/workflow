"""Work Object."""

from json import loads
from os import environ
from time import time
from typing import Any, Dict, List, Literal, Optional, Union
from warnings import warn

from pydantic import BaseModel, Field, SecretStr, StrictFloat, StrictStr, root_validator
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

    class Config:
        """Pydantic Config."""

        validate_all = True
        validate_assignment = True

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


class Slack(BaseModel):
    """Work Object Slack Configuration.

    Args:
        BaseModel (BaseModel): Pydantic BaseModel.

    Attributes:
        channel_id (str): Slack channel to send notifications to.
        member_ids (List[str]): Slack members to send notifications to.
        message (str): Slack message to send notifications with.
        results (bool): Send slack notifications with the work results.
        products (bool): Send slack notifications with the work product links.
        plots (bool): Send slack notifications with the work plot links.
        blocks (Dict[str, Any]): Slack blocks to send notifications with.
        reply (Dict[str, Any]): Status of the slack notification.
    """

    class Config:
        """Pydantic Config."""

        validate_all = True
        validate_assignment = True

    channel_id: Optional[StrictStr] = Field(
        default=None,
        description="Slack channel to send notifications to.",
        example="C01JYQZQX0Y",
    )
    member_ids: Optional[List[StrictStr]] = Field(
        default=None,
        description="Slack members to send notifications to.",
        example=["U01JYQZQX0Y"],
    )
    message: Optional[StrictStr] = Field(
        default=None,
        description="Slack message to send notifications with.",
        example="Hello World!",
    )
    results: Optional[bool] = Field(
        default=None,
        description="Send slack notifications with the work results.",
    )
    products: Optional[bool] = Field(
        default=None,
        description="Send slack notifications with the work product links.",
    )
    plots: Optional[bool] = Field(
        default=None,
        description="Send slack notifications with the work plot links.",
    )
    blocks: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Slack blocks to send notifications with.",
    )
    reply: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Status of the slack notification.",
        example={"ok": True},
    )


class Notify(BaseModel):
    """Work Object Notification Configuration.

    Args:
        BaseModel (BaseModel): Pydantic BaseModel.

    Attributes:
        slack (Slack): Send slack notifications for the work.
    """

    slack: Slack = Slack()


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
    parent: Optional[str] = Field(
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


class Work(BaseModel):
    """Work Object.

    Args:
        BaseModel (BaseModel): Pydantic BaseModel.

    Attributes:
        pipeline (str): Name of the pipeline. (Required)
            Automatically reformated to hyphen-case.
        site (str): Site where the work will be performed. (Required)
        user (str): User who created the work. (Required)
        function (Optional[str]): Name of the function ran as `function(**parameters)`.
        command (Optional[List[str]]): Command to run as `subprocess.run(command)`.
        parameters (Optional[Dict[str, Any]]): Parameters to pass to the function.
        command (Optional[List[str]]): Command to run as `subprocess.run(command)`.
        results (Optional[Dict[str, Any]]): Results of the work.
        products (Optional[Dict[str, Any]]): Products of the work.
        plots (Optional[Dict[str, Any]]): Plots of the work.
        event (Optional[List[int]]): Event ID of the work.
        tags (Optional[List[str]]): Tags of the work.
        timeout (int): Timeout for the work in seconds. Default is 3600 seconds.
        retries (int): Number of retries for the work. Default is 2 retries.
        priority (int): Priority of the work. Default is 3.
        config (WorkConfig): Configuration of the work.
        notify (Notify): Notification configuration of the work.
        id (str): ID of the work.
        creation (float): Creation time of the work.
        start (float): Start time of the work.
        stop (float): Stop time of the work.
        status (str): Status of the work.

    Raises:
        ValueError: If the work is not valid.

    Returns:
        Work: Work object.

    Example:
        ```python
        from chime_frb_api.workflow import Work

        work = Work(pipeline="test-pipeline", site="chime", user="shinybrar")
        work.deposit(return_ids=True)
        ```
    """

    class Config:
        """Pydantic Config."""

        validate_all = True
        validate_assignment = True
        exclude_none = True

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
        "canfar",
        "cedar",
        "chime",
        "aro",
        "hco",
        "gbo",
        "kko",
        "local",
    ] = Field(
        ...,
        description="Site where the work will be performed.",
        example="chime",
    )
    user: StrictStr = Field(
        ..., description="User ID who created the work.", example="shinybrar"
    )
    token: Optional[SecretStr] = Field(
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
        exclude=True,
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
    notify: Notify = Notify()

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
        # Check if the pipeline name has any character that is uppercase
        reformatted: bool = False
        for char in values["pipeline"]:
            if char.isupper():
                values["pipeline"] = values["pipeline"].lower()
                reformatted = True
                break

        if any(char in {" ", "_"} for char in values["pipeline"]):
            values["pipeline"] = values["pipeline"].replace(" ", "-")
            values["pipeline"] = values["pipeline"].replace("_", "-")
            reformatted = True

        # Check if the pipeline has any character that is not alphanumeric or dash
        for char in values["pipeline"]:
            if not char.isalnum() and char not in ["-"]:
                raise ValueError(
                    "pipeline name can only contain letters, numbers & dashes"
                )

        if reformatted:
            warn(
                SyntaxWarning(f"pipeline reformatted to {values['pipeline']}"),
                stacklevel=2,
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

        if not values.get("token"):  # type: ignore
            msg = "workflow token required after v4.0.0."
            warn(
                FutureWarning(msg),
                stacklevel=2,
            )
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
        payload: Dict[str, Any] = self.dict(exclude={"config.token"})
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
