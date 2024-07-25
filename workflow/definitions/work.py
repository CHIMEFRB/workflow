"""Workflow Work Object."""

from json import loads
from time import time
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import (
    AliasChoices,
    Field,
    FilePath,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from workflow import DEFAULT_WORKSPACE_PATH
from workflow.definitions.config import Config
from workflow.definitions.notify import Notify
from workflow.http.context import HTTPContext
from workflow.utils import read


class Work(BaseSettings):
    """Workflow Work Object.

    The work object defines the lifecycle of any action to be performed.

    Args:
        BaseSettings (BaseSettings): Pydantic BaseModel with settings.

    Note:
        The selection priority for attributes in descending order is:

          - Arguments passed to the `Work` Object.
          - Environment variables with `WORKFLOW_` prefix.
          - Variables from /run/secrets secrets directory.
          - The default values in the class constructor.

        Environemnt Prefixes:

          - `WORKFLOW_` for all work attributes.
          - `WORKFLOW_HTTP_` for all work http attributes.
          - `WORKFLOW_CONFIG_` for all work config attributes.
          - `WORKFLOW_NOTIFY_` for all work notify attributes.

        The size of the results dictionary is limited to 4MB. If the results
        dictionary is larger than 4MB, it is ignored and not mapped to the
        work object. Use the `products` attribute to store large data products.


    Attributes:
        pipeline (str): Name of the pipeline. (Required)
        site (str): Site where the work will be performed. (Required)
        user (str): User who created the work. (Required)

        function (str): Python function to run `function(**parameters)`.
        parameters (Dict[str, Any]): Parameters to pass to the function.
        command (List[str]): Command to run as `subprocess.run(command)`.
        results (Dict[str, Any]): Results from the work.
        products (List[str]): Data products from work.
        plots (List[str]):  Visual plots of the work.
        tags (List[str]): Searchable tags of the work.
        event (List[int]): Unique ID[s] the work was performed against.

        id (str): BSON ID of the work, set by the database.
        creation (float): Creation time of the work.
        start (float): Start time of the work, set by the backend.
        stop (float): Stop time of the work, set by the client.
        attempt (int): Attempt number of the work. Defaults to 0.
        status (str): Status of the work. Defaults to "created".
        timeout (int): Timeout for the work in seconds. Defaults to 3600 seconds.
        retries (int): Number of retries for the work. Defaults to 2 retries.
        priority (int): Priority of the work. Defaults to 3.
        config (Config): Configuration for the lifecycle of the work.
        notify (Notify): Notification configuration for the work.

        workspace (FilePath): Path to the active workspace configuration.
            Defaults to `~/.config/workflow/workspace.yml`. (Excluded from payload)
        token (SecretStr): Workflow Access Token. (Excluded from payload)
        http (HTTPContext): HTTP Context for backends. (Excluded from payload)


    Raises:
        ValueError: When work is invalid.

    Returns:
        Object (Work): Work object.

    Example:
        ```bash
        # Set the environment variables to override the defaults.
        export WORKFLOW_PRIORITY=4
        ```

        ```python
        from workflow.definitions.work import Work

        work = Work(pipeline="test", site="local", user="shinybrar")
        work.dump_model()
        {
            "config": {...},
            "notify": {"slack": {}},
            "pipeline": "test-pipeline",
            "site": "local",
            "user": "shinybrar",
            "timeout": 3600,
            "retries": 2,
            "priority": 4,  # Overridden by the environment variable.
            "attempt": 0,
            "status": "created",
        }
        work.deposit(return_ids=True)
        ```
    """

    # * Configuration for the Pydantic Model.
    model_config = SettingsConfigDict(
        title="Workflow Work Object",
        validate_assignment=True,
        validate_return=True,
        revalidate_instances="always",
        env_prefix="WORKFLOW_",
        secrets_dir="/run/secrets",
        extra="ignore",
        json_schema_mode_override="serialization",
    )
    # * Runtime configurations for the Work Object, these are not part of the payload.
    # * and describe the behavior of the work object in the current instantiation.
    workspace: FilePath = Field(
        default=DEFAULT_WORKSPACE_PATH,
        validate_default=True,
        description="Default workspace configuration filepath.",
        examples=["/home/user/.config/workflow/workspace.yml"],
        exclude=True,
    )
    token: Optional[SecretStr] = Field(
        default=None,
        validation_alias=AliasChoices(
            "WORKFLOW_HTTP_TOKEN",
            "WORKFLOW_TOKEN",
            "GITHUB_TOKEN",
            "GITHUB_PAT",
        ),
        exclude=True,
        description="Workflow Access Token.",
        examples=["ghp_1234567890abcdefg"],
    )
    http: HTTPContext = Field(
        default=None,
        validate_default=False,
        description="HTTP Context for backend connections.",
        exclude=True,
        repr=False,
    )
    # * Required attributes, must be provided by the user.
    pipeline: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Name of the pipeline (required). Reformated to hyphen-case.",
        examples=["sample-pipeline"],
    )
    site: str = Field(
        ...,
        description="""
        Site where the work will be performed (required).
        Valid sites are defined in the workspace configuration.
        """,
        examples=["chime"],
    )
    user: str = Field(
        ...,
        description="User ID who created the work (required).",
        examples=["shinybrar"],
    )
    # * Optional attributes, can be provided by the user.
    function: Optional[str] = Field(
        default=None,
        description="""
        Name of the Python function to run as `function(**parameters)`,
        Only either `function` or `command` can be provided.
        """,
        examples=["workflow.example.mean"],
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="""
        Parameters to pass the pipeline function. Equivalent to
        running `function(**parameters)`. Ignored if `command` is set.
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
    products: Optional[List[str]] = Field(
        default=None,
        description="""
        Name of the non-human-readable data products generated by the pipeline.
        """,
        examples=[["spectra.h5", "dm_vs_time.png"]],
    )
    plots: Optional[List[str]] = Field(
        default=None,
        validate_default=False,
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
    # * State Machine Attributes, set by the backend or optionally by the user.
    # * These attributed describe the lifecycle of the work object, irrespective
    # * of the current instantiation.
    id: Optional[str] = Field(
        default=None, description="Work ID created by the database."
    )
    creation: Optional[float] = Field(
        default=None, description="Unix timestamp of when the work was created."
    )
    start: Optional[float] = Field(
        default=None,
        description="Unix timestamp when the work was started, reset at each attempt.",
    )
    stop: Optional[float] = Field(
        default=None,
        description="Unix timestamp when the work was stopped, reset at each attempt.",
    )
    attempt: int = Field(
        default=0, ge=0, description="Attempt number at performing the work."
    )
    status: Literal["created", "queued", "running", "success", "failure"] = Field(
        default="created", description="Status of the work."
    )
    timeout: int = Field(
        default=3600,
        ge=1,
        le=86400 * 3,
        description="""
        Timeout in seconds for the work to finish.
        After the timeout, the work is marked as failed and retried
        if the number of attempts is less than the maximum number of retries.
        Defaults 3600s (1 hr) with range of [1, 259200] (1s-72hrs).
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
        i.e. 5 > 1 in priority. Defaults to 3.""",
        examples=[1],
    )
    # Config defines the flow of state before and after the work.
    config: Config = Field(
        default=Config(),
        description="Configuration of the work lifecycle.",
        examples=[Config()],
    )
    # Notify defines the notification settings for the work.
    notify: Notify = Field(
        default=Notify(),
        description="Notifications for work.",
        examples=[Notify()],
    )

    ###########################################################################
    # Validation Methods for Work Attributes
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
        for char in pipeline:
            if not char.isalnum() and char not in ["-"]:
                raise ValueError(
                    "pipeline name can only contain letters, numbers & hyphens."
                )
        return pipeline

    @field_validator("creation")
    def validate_creation(cls, creation: Optional[float]) -> float:
        """Validate and set the creation time.

        Args:
            creation (Optional[float]): Creation time in unix timestamp.

        Returns:
            float: Creation time in unix timestamp.
        """
        if creation is None:
            return time()
        return creation

    @model_validator(mode="before")
    def pre_validation(cls, data: Any) -> Any:
        """Validate the work model before creating the object.

        Args:
            data (Any): Work data to validate.

        Raises:
            ValueError: If both `function` and `command` are set.

        Returns:
            Any: Validated work data.
        """
        if data.get("function") and data.get("command"):
            raise ValueError("Only either function or command can be provided.")
        return data

    @model_validator(mode="after")
    def post_model_validation(self) -> "Work":
        """Validate the work model after creating the object.

        Raises:
            ValueError: Raised if,
                the site provided is not allowed in the workspace.

        Returns:
            Work: The current work object.
        """
        # Validate if the site provided is allowed in the workspace.
        if self.config.strategy == "strict":
            config: Dict[str, Any] = read.workspace(self.workspace)
            sites: List[str] = config.get("sites", [])
            if self.site not in sites:
                error = f"site {self.site} not in workspace: {sites}."
                raise ValueError(error)
        return self

    ###########################################################################
    # Work Class Methods
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
        pipeline: Union[str, List[str]],
        event: Optional[List[int]] = None,
        site: Optional[str] = None,
        priority: Optional[int] = None,
        user: Optional[str] = None,
        tags: Optional[List[str]] = None,
        parent: Optional[List[str]] = None,
        timeout: float = 15.0,
        token: Optional[SecretStr] = None,
        http: Optional[HTTPContext] = None,
    ) -> Optional["Work"]:
        """Withdraw work from the buckets backend.

        Args:
            pipeline (Union[str, List[str]]): Name of the pipeline to withdraw work for.
            event (Optional[List[int]]): Unique event ids to withdraw work for.
            site (Optional[str]): Name of the site to withdraw work for.
            priority (Optional[int]): Priority of the work to withdraw.
            user (Optional[str]): Name of the user to withdraw work for.
            tags (Optional[List[str]]): List of tags to withdraw work from.
            parent (Optional[str]): Parent Pipeline ID of the work to withdraw.
            timeout (float, optional): HTTP timeout in seconds. Defaults to 15.0.
            token (Optional[SecretStr], optional): Workflow Access Token.
            http (Optional[HTTPContext], optional): HTTP Context for connecting to
                workflow servers.

        Note:
            `token` and `timeout` arguments can also be provided via the environment,

                - "WORKFLOW_HTTP_TOKEN"
                - "WORKFLOW_TOKEN"
                - "GITHUB_TOKEN"
                - "GITHUB_PAT"
                - "WORKFLOW_HTTP_TIMEOUT"

            The `http` argument can be provided, to avoid creating a new HTTPContext
            object each time the work object interacts with a backend. This is useful
            when doing bulk withdraws from the same backend.

        Returns:
            Optional[Work]: The withdrawn work if successful, None otherwise.
        """
        # Context is used to source environtment variables, which are overwriten
        # by the arguments passed to the function.
        http = http or HTTPContext(timeout=timeout, token=token, backends=["buckets"])
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
        timeout: float = 15.0,
        token: Optional[SecretStr] = None,
        http: Optional[HTTPContext] = None,
    ) -> Union[bool, List[str]]:
        """Deposit work to the buckets backend.

        Args:
            return_ids (bool, optional): Return Database ID. Defaults to False.
            timeout (float, optional): HTTP request timeout in seconds.
            token (Optional[SecretStr], optional): Workflow Access Token.
            http (Optional[HTTPContext], optional): HTTP Context for backend.

        Note:
            Both token and http can be either provided as arguments to the function
            or also inherited from the work object itself.

        Returns:
            Union[bool, List[str]]: True if successful, False otherwise.
        """
        self.token = token or self.token
        self.http = (
            http
            or self.http
            or HTTPContext(timeout=timeout, token=token, backends=["buckets"])
        )
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
