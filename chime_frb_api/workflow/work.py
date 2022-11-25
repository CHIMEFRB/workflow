"""Work Object."""

from json import dumps, loads
from os import environ
from time import time
from typing import Any, Dict, List, Optional

from pydantic import (
    BaseModel,
    Field,
    DirectoryPath,
    validator,
    StrictStr,
    StrictFloat,
    StrictInt,
    ValidationError,
    root_validator,
    conint,
)
from pydantic.tools import parse_obj_as
from jwt import decode

from chime_frb_api.modules.buckets import Buckets

# Validator for the Work.site attribute.
PRIORITIES = range(1, 6)
STATUSES = ["created", "queued", "running", "success", "failure"]
SITES = ["chime", "allenby", "gbo", "hatcreek", "canfar", "cedar", "local"]


class Work(BaseModel):
    """The Work Object.

    Example:
        ```python
        from chime_frb_api.workflow.work import Work

        work = Work(
            pipeline="test",
        )
        work.deposit()
        ```

    Args:
        pipeline (StrictStr): Pipeline name. Required.
        parameters (Optional[Dict[str, Any]]): Parameters for the pipeline.
        results (Optional[Dict[str, Any]]): Results from the pipeline.
        path (Optional[DirectoryPath]): Path to the save directory. Defaults to ".".
        event (Optional[List[int]]): Event IDs processed by the pipeline.
        tags (Optional[List[str]]): Tags for the work. Defaults to None.
        group (Optional[StrictStr]): Working group for the work. Defaults to None.
        timeout (int): Timeout in seconds. 3600 by default.
        priority (int): Priority of the work. Ranges from 1(lowest) to 5(highest).
            Defaults to 3.
        precursors(Optional[List[Dict[StrictStr, StrictStr]]]): List of previous works used as input.
            None by default.
        products (Optional[List[StrictStr]]): Data products produced by the work.
        plots (Optional[List[StrictStr]]) Plot files produced by the work.
        id (Optional[StrictStr]): Work ID. Created when work is entered in the database.
        creation (Optional[StrictFloat]): Unix timestamp of when the work was created.
            If none, set to time.time() by default.
        start (Optional[StrictFloat]): Unix timestamp of when the work was started.
        stop (Optional[float]): Unix timestamp of when the work was stopped.
        attempt (StrictInt): Attempt number at performing the work. 0 by default.
        retries (int): Number of retries before giving up. 1 by default.
        config (Optional[StrictStr]): Configuration of the container used to run the work.
        status (StrictStr): Status of the work.
            One of "created", "queued", "running", "success", or "failure".
        site (StrictStr): Site where the work was performed. "local" by default.
        user (Optional[StrictStr]): User ID of the user who performed the work.
        archive(bool): Whether or not to archive the work. True by default.

    Raises:
        pydantic.ValidationError: If any of the arguments are of wrong tipe or value.

    Returns:
        Work: Work object.
    """

    class Config:
        validate_all = True
        validate_assignment = True

    ###########################################################################
    # Required attributes provided by the user
    ###########################################################################
    # Name of the pipeline. Set by user.
    pipeline: StrictStr = Field(...)
    ###########################################################################
    # Optional attributes provided by the user.
    ###########################################################################
    # Parameters to pass the pipeline function. Set by user.
    parameters: Optional[Dict[str, Any]] = Field(default=None)
    # Results of the work performed. Set automatically by @pipeline decorator.
    # Can also be set manually by user.
    results: Optional[Dict[str, Any]] = Field(default=None)
    # Base data directory where the pipeline will store its data.
    # Overwritten automatically by work.withdraw() if `.` from  environment
    # variable WORK_PATH. Can also be set manually by user.
    path: Optional[DirectoryPath] = Field(default=".", type=DirectoryPath)
    # Name of the CHIME/FRB Event the work was performed against.
    # Set by user.
    event: Optional[List[int]] = Field(default=None)
    # Searchable tags for the work.
    # Set by user.
    # Automatically appended by work.withdraw() for each unique tag.
    # Value sourced from environment variable TASK_TAGS.
    tags: Optional[List[str]] = Field(default=None)
    # Name of the working group responsible for managing the work.
    # Automatically overwritten by work.withdraw() when None.
    # Sourced from environment variable WORK_GROUP.
    # Can be set manually by user.
    group: Optional[StrictStr] = Field(default=None)
    # Timeout in seconds in which the work needs to be completed.
    # Defaults to 3600 seconds (1 hour).
    # Maximum timeout is 86400 seconds (24 hours).
    timeout: int = Field(default=3600, lt=86401)
    # Number of times the work has been attempted.
    # Can be set manually by user.
    # Maximum number of retries is 5.
    retries: int = Field(default=2, lt=6)
    # Priorities of the work. Set by user.
    # Ranges between 1 and 5 (5 being the highest priority.)
    # Default is 1.
    priority: int = Field(default=3)
    # Key, Value ("pipeline-name",id) pairs identifying previous works,
    # used as inputs to the current work. Automatically appended whenever
    # results.get() from Results API is called. Can also be set manually by user.
    precursors: Optional[List[Dict[StrictStr, StrictStr]]] = Field(default=None)
    # Name of the non-human-readable data products generated by the pipeline.
    # Relative path from the current working directory.
    # When saving the data products, the Work API will autommatically move them
    # to path + relative path. Set by user.
    products: Optional[List[StrictStr]] = Field(default=None)
    # Name of visual data products generated by the pipeline.
    # Relative path from the current working directory.
    # When saving the plots, the TasksAPI will autommatically move them
    # the path + relative path.
    # Set by user.
    plots: Optional[List[StrictStr]] = Field(default=None)

    ###########################################################################
    # Automaticaly set attributes
    ###########################################################################
    # ID of the work performed.
    # Created only when the work is added into the database upon conclusion.
    id: Optional[StrictStr] = Field(default=None)
    # Time the work was created, in seconds since the epoch.
    # Set automatically when work is created.
    creation: Optional[StrictFloat] = Field(default=None)
    # Time when work was started, in seconds since the epoch.
    # Automatically set by the buckets backend.
    start: Optional[StrictFloat] = Field(default=None)
    # Stop time of the work, in seconds since the epoch.
    # If the work is still running, this will be None.
    # Automatically set by the buckets backend.
    stop: Optional[StrictFloat] = Field(default=None)
    # Configuration of the pipeline used to perform the work.
    # Automatically overwritten by work.withdraw()
    # Value sourced from environment variable WORK_CONFIG.
    config: Optional[StrictStr] = Field(default=environ.get("WORK_CONFIG", None))
    # Numbered attempt at performing the work.
    # Cannot be set manually.
    attempt: StrictInt = Field(default=None)
    # Status of the work.
    # Default is "created"
    # Automatically set by the buckets backend at
    #   work.deposit to queued
    #   Work.withdraw(...) to running
    # Set by the pipelines decorator to "success" or "failure"
    # Can be set manually by user.
    status: StrictStr = Field(default="created")
    # Name of the site where pipeline was executed.
    # Automatically overwritten by Work.withdraw(...)
    # Value sourced from environment variable WORK_SITE.
    site: StrictStr = Field(default=environ.get("WORK_SITE", "local"))
    # Name of the user who submitted the work.
    # Set by work.deposit() and based on the access token.
    # Can be set manually by user.
    user: Optional[StrictStr] = Field(default=None)
    # Whether the work will be archived in the Results Backend after completion.
    #  Default is True.
    archive: bool = Field(default=True)

    ###########################################################################
    # Validators for the work attributes
    ###########################################################################

    @validator("pipeline", pre=True)
    def pipeline_not_none(cls, value):
        """Check that pipeline field is not None."""
        if not value:
            raise ValidationError("pipeline must not be empty.")
        return value

    @validator("parameters")
    def parameters_is_dict_instance(cls, value):
        """Check that parameters field is dict() instance."""
        if value and not isinstance(value, dict):
            print("raising")
            raise ValidationError("parameters must be a dict() object.")
        return value

    @validator("results", pre=True)
    def results_is_dict_instance(cls, value):
        """Check that results field is dict() instance"""
        if value and not isinstance(value, dict):
            raise ValidationError("results must be a dict() object.")
        return value

    @validator("priority", pre=True)
    def priority_under_right_value_range(cls, value):
        """Check that priority field is in range defined on PRIORITIES variable."""
        if value not in PRIORITIES:
            raise ValidationError(
                f"priority must be between {PRIORITIES[0]}-{PRIORITIES[-1]}"
            )
        return value

    @validator("status", pre=True)
    def status_is_valid(cls, value):
        """Check that status value is on the predefined values on STATUSES"""
        if value not in STATUSES:
            raise ValidationError(
                f"bad status value, please select one of the following {STATUSES}"
            )
        return value

    @validator("site", pre=True)
    def site_is_valid(cls, value):
        """Check that site value is on the predefined values on SITES"""
        if value not in SITES:
            raise ValidationError(
                f"bad site value, please select one of the following {SITES}"
            )
        return value

    ###########################################################################
    # Attribute setters for the work attributes
    ###########################################################################
    @root_validator
    def post_init(cls, values):
        """Set default values for the work attributes."""
        if not values["creation"]:
            values["creation"] = time()
        if values["path"] == ".":
            values["path"] = environ.get("WORK_PATH", values["path"])
        # Update group from WORK_GROUP.
        if not values["group"]:
            values["group"] = environ.get("WORK_GROUP", values["group"])
        # Update tags from WORK_TAGS
        if environ.get("WORK_TAGS"):
            tags = environ.get("WORK_TAGS").split(",")
            # If tags are already set, append the new ones
            if values["tags"] and isinstance(values["tags"], list):
                values["tags"].append(tags)
            else:
                values["tags"] = tags
            values["tags"] = list(set(values["tags"]))
        return values

    ###########################################################################
    # Work methods
    ###########################################################################

    @property
    def payload(self) -> Dict[str, Any]:
        """Return the dictioanary representation of the work.

        Returns:
            Dict[str, Any]: The payload of the work.
        """
        payload: dict = self.dict()
        for k, v in payload.items():
            try:
                dumps(v)  # There could be some field that are not JSON serializable
            except TypeError:
                payload[k] = str(v)
            else:
                payload[k] = v
        return payload

    @property
    def json(self) -> str:
        """Return the json representation of the work.

        Returns:
            str: The json representation of the work.
        """
        return dumps(self.payload)

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

    def deposit(self, **kwargs: Dict[str, Any]) -> bool:
        """Deposit work to the buckets backend.

        Args:
            **kwargs (Dict[str, Any]): Keyword arguments for the Buckets API.

        Returns:
            bool: True if successful, False otherwise.
        """
        buckets = Buckets(**kwargs)  # type: ignore
        token = buckets.access_token
        if token:
            # Try and decode the token for the user.
            try:
                self.user = decode(token, options={"verify_signature": False}).get(
                    "user_id", None
                )
            except Exception:
                pass
        return buckets.deposit([self.payload])

    def update(self, **kwargs: Dict[str, Any]) -> bool:
        """Update work in the buckets backend.

        Args:
            **kwargs (Dict[str, Any]): Keyword arguments for the Buckets API.

        Returns:
            bool: True if successful, False otherwise.
        """
        buckets = Buckets(**kwargs)  # type: ignore
        return buckets.update([self.payload])

    def delete(self, **kwargs: Dict[str, Any]) -> bool:
        """Delete work from the buckets backend.

        Args:
            ids (List[str]): List of ids to delete.

        Returns:
            bool: True if successful, False otherwise.
        """
        buckets = Buckets(**kwargs)  # type: ignore
        return buckets.delete_ids([str(self.id)])
