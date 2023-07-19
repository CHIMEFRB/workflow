"""Work Object."""

from json import loads
from os import environ
from time import time
from typing import Any, Dict, List, Literal, Optional, Union
from warnings import warn

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    StrictFloat,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
)
from tenacity import retry
from tenacity.stop import stop_after_delay
from tenacity.wait import wait_random

from workflow.work.config import Config
from workflow.work.notify import Notify


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
        from workflow import Work

        work = Work(pipeline="test-pipeline", site="chime", user="shinybrar")
        work.deposit(return_ids=True)
        ```
    """

    model_config = ConfigDict(
        title="Workflow Work Object",
        validate_default=True,
        validate_assignment=True,
        validate_return=True,
        revalidate_instances="always",
    )
    ###########################################################################
    # Required Attributes. Set by user.
    ###########################################################################
    pipeline: StrictStr = Field(
        ...,
        min_length=1,
        description="Name of the pipeline. Automatically reformated to hyphen-case.xw",
        examples=["sample-pipeline"],
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
        ..., description="Site where the work will be performed.", examples=["chime"]
    )
    user: StrictStr = Field(
        ..., description="User ID who created the work.", examples=["shinybrar"]
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
        description="Workflow Access Token.",
        examples=["ghp_1234567890abcdefg"],
        exclude=True,
    )

    ###########################################################################
    # Optional attributes, might be provided by the user.
    ###########################################################################
    function: Optional[str] = Field(
        default=None,
        description="""
        Name of the function to run as `function(**parameters)`.
        Only either `function` or `command` can be provided.
        """,
        examples=["workflow.example.mean"],
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="""
        Parameters to pass the pipeline function. Equivalent to
        running `function(**parameters)`. Note, only either
        `function` or `command` can be provided.
        """,
        examples=[{"a": 1, "b": 2}],
    )
    command: Optional[List[str]] = Field(
        default=None,
        description="""
        Command to run as `subprocess.run(command)`.
        Note, only either `function` or `command` can be provided.
        """,
        examples=[["python", "example.py", "--example", "example"]],
    )
    results: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Results of the work performed.",
        examples=[{"dm": 100.0, "snr": 10.0}],
    )
    products: Optional[List[StrictStr]] = Field(
        default=None,
        description="""
        Name of the non-human-readable data products generated by the pipeline.
        """,
        examples=[["spectra.h5", "dm_vs_time.png"]],
    )
    plots: Optional[List[StrictStr]] = Field(
        default=None,
        description="""
        Name of visual data products generated by the pipeline.
        """,
        examples=[["waterfall.png", "/arc/projects/chimefrb/9385707/9385707.png"]],
    )
    event: Optional[List[int]] = Field(
        default=None,
        description="Unique ID[s] the work was performed against.",
        examples=[[9385707, 9385708]],
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="""
        Searchable tags for the work. Merged with values from env WORKFLOW_TAGS.
        """,
        examples=[["tag", "tagged", "tagteam"]],
    )
    timeout: StrictInt = Field(
        default=3600,
        ge=1,
        le=86400,
        description="""
        Timeout in seconds for the work to finish.
        After the timeout, the work is marked as failed and retried
        if the number of attempts is less than the maximum number of retries.
        Defaults 3600s (1 hr) with range of [1, 86400] (1s-24hrs).
        """,
        examples=[7200],
    )
    retries: int = Field(
        default=2,
        lt=6,
        description="Number of retries before giving up. Defaults to 2.",
        examples=[4],
    )
    priority: int = Field(
        default=3,
        ge=1,
        le=5,
        description="""
        Priority of the work. Higher priority works are performed first.
        i.e. priority 5 > priority 1. Defaults to 3.""",
        examples=[1],
    )
    config: Config = Config()
    notify: Notify = Notify()

    ###########################################################################
    # Automaticaly set attributes
    ###########################################################################
    id: Optional[str] = Field(
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

    @field_validator("pipeline", mode="after", check_fields=True)
    def validate_pipeline(cls, pipeline: str) -> str:
        """Validate the pipeline name.

        Args:
            pipeline (str): Name of the pipeline.

        Raises:
            ValueError: If the pipeline name contains any character that is not

        Returns:
            str: Validated pipeline name.
        """
        original: str = pipeline
        pipeline = pipeline.lower()
        pipeline = pipeline.replace(" ", "-")
        pipeline = pipeline.replace("_", "-")
        for char in pipeline:
            if not char.isalnum() and char not in ["-"]:
                raise ValueError(
                    "pipeline name can only contain letters, numbers & dashes"
                )
        if original != pipeline:
            warn(
                SyntaxWarning(
                    f"pipeline name '{original}' reformatted to '{pipeline}'"
                ),
                stacklevel=2,
            )
        return pipeline

    @field_validator("creation", mode="after", check_fields=True)
    def validate_creation(cls, creation: Optional[StrictFloat]) -> float:
        """Validate and set the creation time.

        Args:
            creation (Optional[StrictFloat]): Creation time in unix timestamp.

        Returns:
            StrictFloat: Creation time in unix timestamp.
        """
        if creation is None:
            return time()
        return creation

    @model_validator(mode="before")
    def validate_model(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the work model.

        Args:
            data (Dict[str, Any]): Work data to validate.

        Raises:
            ValueError: If both `function` and `command` are set.

        Returns:
            Dict[str, Any]: Validated work data.
        """
        if data.get("function") and data.get("command"):
            raise ValueError("command and function cannot be set together.")
        return data

    @field_validator("token", mode="after", check_fields=True)
    def validate_token(cls, token: Optional[SecretStr]) -> None:
        """Validate the workflow token.

        Args:
            token (Optional[SecretStr]): Workflow token.
        """
        if token is None:
            msg = """
            Workflow token not provided.
            Token auth will become mandatory in the future.
            """
            warn(msg, FutureWarning, stacklevel=2)

        # # Update tags from environment variable WORKFLOW_TAGS
        # if environ.get("WORKFLOW_TAGS"):
        #     env_tags: List[str] = str(environ.get("WORKFLOW_TAGS")).split(",")
        #     # If tags are already set, append the new ones
        #     if values.get("tags"):
        #         values["tags"] = values["tags"] + env_tags
        #     else:
        #         values["tags"] = env_tags
        #     # Remove duplicates
        #     values["tags"] = list(set(values["tags"]))

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
        payload: Dict[str, Any] = self.model_dump(exclude={"config.token"})
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
        tags: Optional[List[str]] = None,
        parent: Optional[str] = None,
        **kwargs: Dict[str, Any],
    ) -> Optional["Work"]:
        """Withdraw work from the buckets backend.

        Args:
            pipeline (str): Name of the pipeline.
            **kwargs (Dict[str, Any]): Keyword arguments for the Buckets API.

        Returns:
            Work: Work object.
        """
        from chime_frb_api.modules.buckets import Buckets

        buckets = Buckets(**kwargs)  # type: ignore
        payload = buckets.withdraw(
            pipeline=pipeline,
            event=event,
            site=site,
            priority=priority,
            user=user,
            tags=tags,
            parent=parent,
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
        from chime_frb_api.modules.buckets import Buckets

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
        from chime_frb_api.modules.buckets import Buckets

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
        from chime_frb_api.modules.buckets import Buckets

        buckets = Buckets(**kwargs)  # type: ignore
        return buckets.delete_ids([str(self.id)])
