"""Work Object."""

from json import loads
from time import time
from typing import Any, Dict, List, Literal, Optional, Union
from warnings import warn

from pydantic import (
    Field,
    SecretStr,
    StrictFloat,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from workflow.definitions.config import Config
from workflow.definitions.notify import Notify
from workflow.http.context import HTTPContext


class Work(BaseSettings):
    """Work Object.

    Args:
        BaseSettings (BaseSettings): Pydantic BaseModel with settings.

    Note:
        In the case where default value for a field is specified in multiple places,
        the selection priority in descending order is:
            1. Arguments passed to the `Work` Object.
            2. Environment variables defined with the `WORKFLOW_` prefix.
            3. Variables loaded from the secrets directory.
            4. The default values in the constructor.

        Environemnt Prefixes:
            - `WORKFLOW_` for all work attributes.
            - `WORKFLOW_CONFIG_` for all work config attributes.
            - `WORKFLOW_NOTIFY_` for all work notify attributes.
            - `WORKFLOW_HTTP_` for all work http attributes.


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

    model_config = SettingsConfigDict(
        title="Workflow Work Object",
        validate_default=True,
        validate_assignment=True,
        validate_return=True,
        revalidate_instances="always",
        env_prefix="WORKFLOW_",
        secrets_dir="/run/secrets",
        extra="ignore",
    )

    pipeline: StrictStr = Field(
        ...,
        min_length=1,
        description="Name of the pipeline (required). Reformated to hyphen-case.",
        examples=["sample-pipeline"],
    )
    site: str = Field(
        ...,
        description="Site where the work will be performed (required).",
        examples=["chime"],
    )
    user: StrictStr = Field(
        ...,
        description="User ID who created the work (required).",
        examples=["shinybrar"],
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
    tags: Optional[List[str]] = Field(
        default=None,
        description="""
        Searchable tags for the work. Merged with values from env WORKFLOW_TAGS.
        """,
        examples=[["tag", "tagged", "tagteam"]],
    )
    event: Optional[List[int]] = Field(
        default=None,
        description="Unique ID[s] the work was performed against.",
        examples=[[9385707, 9385708]],
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
    http: HTTPContext = Field(
        default=None,
        validate_default=False,
        description="HTTP Context for doing work.",
        exclude=True,
        repr=False,
    )
    ###########################################################################
    # Configuration attributes
    ###########################################################################
    config: Config = Field(
        default=Config(),
        description="Configuration of the work.",
        examples=[Config()],
    )
    notify: Notify = Field(
        default=Notify(),
        description="Notification configuration of the work.",
        examples=[Notify()],
    )
    ###########################################################################
    # Default Validators
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
                SyntaxWarning(f"pipeline reformatted {original}->{pipeline}"),
                stacklevel=2,
            )
        return pipeline

    @field_validator("site", mode="after", check_fields=True)
    def validate_site(cls, site: str) -> str:
        """Validate the site name.

        Args:
            site (str): Name of the site.

        Raises:
            ValueError: If the site name is not in the list of valid sites.

        Returns:
            str: Validated site name.
        """
        valid: List[str] = [
            "local",
            "chime",
            "kko",
            "gbo",
            "hco",
            "canfar",
            "cedar",
            "calcul-quebec",
        ]
        if site not in valid:
            raise ValueError(f"site must be one of {valid}")
        return site

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
    def validate_model(cls, data: Any) -> Any:
        """Validate the work model.

        Args:
            data (Any): Work data to validate.

        Raises:
            ValueError: If both `function` and `command` are set.

        Returns:
            Any: Validated work data.
        """
        if data.get("function") and data.get("command"):
            raise ValueError("command and function cannot be set together.")
        return data

    ###########################################################################
    # Default Work Class Methods
    ###########################################################################
    @property
    def payload(self) -> Dict[str, Any]:
        """Return the dictionary representation of the work.

        Returns:
            Dict[str, Any]: The payload of the work.
            Non-instanced attributes are excluded from the payload.
        """
        payload: Dict[str, Any] = self.model_dump()
        return payload

    @classmethod
    def from_json(cls, json: str) -> "Work":
        """Create a work from a json string.

        Args:
            json (str): The json string.

        Returns:
            Work: Work Object.
        """
        return cls(**loads(json))

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Work":
        """Create a work from a dictionary.

        Args:
            payload (Dict[str, Any]): The dictionary.

        Returns:
            Work: Work Object.
        """
        return cls(**payload)

    ###########################################################################
    # HTTP Methods for the Work Class
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
        baseurl: str = "http://localhost:8004",
        timeout: float = 15.0,
        token: Optional[SecretStr] = None,
    ) -> Any:
        """Withdraw work from the buckets backend.

        Args:
            pipeline (str): Name of the pipeline to withdraw work from.
            event (Optional[List[int]]): List of event ids to withdraw work for.
            site (Optional[str]): Name of the site to withdraw work for.
            priority (Optional[int]): Priority of the work to withdraw.
            user (Optional[str]): Name of the user to withdraw work for.
            tags (Optional[List[str]]): List of tags to withdraw work from.
            parent (Optional[str]): Parent id of the work to withdraw.
            httpargs (Optional[Dict[str, Any]]): Additional args for http client.

        Returns:
            Optional[Work]: The withdrawn work if successful, None otherwise.
        """
        # Context is used to source environtment variables, which are overwriten
        # by the arguments passed to the function.
        http = HTTPContext(baseurl=baseurl, token=token, timeout=timeout)
        payload = http.buckets.withdraw(
            pipeline=pipeline,
            event=event,
            site=site,
            priority=priority,
            user=user,
            tags=tags,
            parent=parent,
        )
        if payload:
            work = cls.from_dict(payload)
            work.http = http
            return work
        return None

    def deposit(
        self,
        return_ids: bool = False,
        baseurl: str = "http://localhost:8004",
        timeout: float = 15.0,
        token: Optional[SecretStr] = None,
    ) -> Union[bool, List[str]]:
        """Deposit work to the buckets backend.

        Args:
            return_ids (bool, optional): Whether to return database ids.
                Defaults to False.

        Returns:
            Union[bool, List[str]]: True if successful, False otherwise.
        """
        if not self.http:
            self.http = HTTPContext(baseurl=baseurl, token=token, timeout=timeout)
        return self.http.buckets.deposit(works=[self.payload], return_ids=return_ids)

    def update(self) -> bool:
        """Update work in the buckets backend.

        Returns:
            bool: True if successful, False otherwise.
        """
        return self.http.buckets.update([self.payload])

    def delete(self) -> bool:
        """Delete work from the buckets backend.

        Returns:
            bool: True if successful, False otherwise.
        """
        return self.http.buckets.delete_ids([str(self.id)])
