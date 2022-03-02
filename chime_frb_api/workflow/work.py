"""Work Object."""

from json import dumps, loads
from os import environ
from time import time
from typing import Any, Dict, List, Optional

from attr import asdict, attrib, attrs
from attr.setters import validate
from attr.validators import in_, instance_of, optional
from jwt import decode

from chime_frb_api.modules.buckets import Buckets

# Validator for the Work.site attribute.
PRIORITIES = range(1, 6)
STATUSES = ["created", "queued", "running", "success", "failure"]
SITES = ["chime", "allenby", "gbo", "hatcreek", "canfar", "cedar", "local"]


@attrs(auto_attribs=True, slots=True, on_setattr=validate)  # type: ignore
class Work:
    """The Work Object.

    Example:
        >>> from chime_frb_api.workflow.work import Work
        >>> work = Work(pipeline="test",)
        >>> work.deposit()

    Args:
        pipeline (str): Pipeline name. Required.
        parameters (Optional[Dict[str, Any]]): Parameters for the pipeline.
        results (Optional[Dict[str, Any]]): Results from the pipeline.
        path (str): Path to the save directory. Defaults to ".".
        event (Optional[List[int]]): Event IDs processed by the pipeline.
        tags (Optional[List[str]]): Tags for the work. Defaults to None.
        group (Optional[str]): Working group for the work. Defaults to None.
        timeout (int): Timeout in seconds. 3600 by default.
        priority (int): Priority of the work. Ranges from 1(lowest) to 5(highest).
            Defaults to 3.
        precursors(Optional[List[Dict[str, str]]]): List of previous works used as input.
            None by default.
        products (Optional[List[str]]): Data products produced by the work.
        plots (Optional[List[str]]) Plot files produced by the work.
        id (Optional[str]): Work ID. Created when work is entered in the database.
        creation (Optional[float]): Unix timestamp of when the work was created.
            If none, set to time.time() by default.
        start (Optional[float]): Unix timestamp of when the work was started.
        stop (Optional[float]): Unix timestamp of when the work was stopped.
        attempt (int): Attempt number at performing the work. 0 by default.
        retries (int): Number of retries before giving up. 1 by default.
        config (Optional[str]): Configuration of the container used to run the work.
        status (str): Status of the work.
            One of "created", "queued", "running", "success", or "failure".
        site (str): Site where the work was performed. "local" by default.
        user (Optional[str]): User ID of the user who performed the work.
        archive(bool): Whether or not to archive the work. True by default.

    Raises:
        TypeError: If any of the arguments are of the wrong type.
        ValueError: If any of the arguments are of the wrong value.

    Returns:
        Work: Work object.
    """

    ###########################################################################
    # Required attributes provided by the user
    ###########################################################################
    # Name of the pipeline. Set by user.
    pipeline: str = attrib(validator=instance_of(str))
    ###########################################################################
    # Optional attributes provided by the user.
    ###########################################################################
    # Parameters to pass the pipeline function. Set by user.
    parameters: Optional[Dict[str, Any]] = attrib(
        default=None, validator=optional(instance_of(dict))
    )
    # Results of the work performed. Set automatically by @pipeline decorator.
    # Can also be set manually by user.
    results: Optional[Dict[Any, Any]] = attrib(
        default=None, validator=optional(instance_of(dict))
    )
    # Base data directory where the pipeline will store its data.
    # Overwritten automatically by work.withdraw() if `.` from  environment
    # variable WORK_PATH. Can also be set manually by user.
    path: str = attrib(default=".", validator=instance_of(str))
    # Name of the CHIME/FRB Event the work was performed against.
    # Set by user.
    event: Optional[List[int]] = attrib(
        default=None, validator=optional(instance_of(list))
    )
    # Searchable tags for the work.
    # Set by user.
    # Automatically appended by work.withdraw() for each unique tag.
    # Value sourced from environment variable TASK_TAGS.
    tags: Optional[List[str]] = attrib(
        default=None, validator=optional(instance_of(list))
    )
    # Name of the working group responsible for managing the work.
    # Automatically overwritten by work.withdraw() when None.
    # Sourced from environment variable WORK_GROUP.
    # Can be set manually by user.
    group: Optional[str] = attrib(default=None, validator=optional(instance_of(str)))
    # Timeout in seconds in which the work needs to be completed.
    # Defaults to 3600 seconds (1 hour).
    # Maximum timeout is 86400 seconds (24 hours).
    timeout: int = attrib(default=3600, validator=in_(range(0, 86400)))
    # Number of times the work has been attempted.
    # Can be set manually by user.
    # Maximum number of retries is 5.
    retries: int = attrib(default=2, validator=in_(range(1, 6)))
    # Priorities of the work. Set by user.
    # Ranges between 1 and 5 (5 being the highest priority.)
    # Default is 1.
    priority: int = attrib(default=3, validator=in_(PRIORITIES))
    # Key, Value ("pipeline-name",id) pairs identifying previous works,
    # used as inputs to the current work. Automatically appended whenever
    # results.get() from Results API is called. Can also be set manually by user.
    precursors: Optional[List[Dict[str, str]]] = attrib(
        default=None, validator=optional(instance_of(list))
    )
    # Name of the non-human-readable data products generated by the pipeline.
    # Relative path from the current working directory.
    # When saving the data products, the Work API will autommatically move them
    # to path + relative path. Set by user.
    products: Optional[List[str]] = attrib(
        default=None, validator=optional(instance_of(list))
    )
    # Name of visual data products generated by the pipeline.
    # Relative path from the current working directory.
    # When saving the plots, the TasksAPI will autommatically move them
    # the path + relative path.
    # Set by user.
    plots: Optional[List[str]] = attrib(
        default=None, validator=optional(instance_of(list))
    )
    ###########################################################################
    # Automaticaly set attributes
    ###########################################################################
    # ID of the work performed.
    # Created only when the work is added into the database upon conclusion.
    id: Optional[str] = attrib(default=None, validator=optional(instance_of(str)))
    # Time the work was created, in seconds since the epoch.
    # Set automatically when work is created.
    creation: Optional[float] = attrib(
        default=None, validator=optional(instance_of(float))
    )
    # Time when work was started, in seconds since the epoch.
    # Automatically set by the buckets backend.
    start: Optional[float] = attrib(
        default=None, validator=optional(instance_of(float))
    )
    # Stop time of the work, in seconds since the epoch.
    # If the work is still running, this will be None.
    # Automatically set by the buckets backend.
    stop: Optional[float] = attrib(default=None, validator=optional(instance_of(float)))
    # Configuration of the pipeline used to perform the work.
    # Automatically overwritten by work.withdraw()
    # Value sourced from environment variable WORK_CONFIG.
    config: Optional[str] = attrib(
        default=environ.get("WORK_CONFIG", None), validator=optional(instance_of(str))
    )
    # Numbered attempt at performing the work.
    # Cannot be set manually.
    attempt: int = attrib(default=0, validator=instance_of(int))
    # Status of the work.
    # Default is "created"
    # Automatically set by the buckets backend at
    #   work.deposit to queued
    #   Work.withdraw(...) to running
    # Set by the pipelines decorator to "success" or "failure"
    # Can be set manually by user.
    status: str = attrib(default="created", validator=(in_(STATUSES)))
    # Name of the site where pipeline was executed.
    # Automatically overwritten by Work.withdraw(...)
    # Value sourced from environment variable WORK_SITE.
    site: str = attrib(default=environ.get("WORK_SITE", "local"), validator=in_(SITES))
    # Name of the user who submitted the work.
    # Set by work.deposit() and based on the access token.
    # Can be set manually by user.
    user: Optional[str] = attrib(default=None, validator=optional(instance_of(str)))
    # Whether the work will be archived in the Results Backend after completion.
    #  Default is True.
    archive: bool = attrib(default=True, validator=instance_of(bool))

    ###########################################################################
    # Validators for the work attributes
    ###########################################################################

    @pipeline.validator
    def _check_pipeline(self, attribute, value):
        """Check if pipeline is str."""
        if not value:
            raise ValueError("pipeline must not be empty.")

    @attempt.validator
    def _check_attempt(self, attribute, value):
        """Check if any attempts are left."""
        if value > self.retries:
            raise ValueError("No more attempts left.")

    ###########################################################################
    # Attribute setters for the work attributes
    ###########################################################################
    def __attrs_post_init__(self):
        """Set default values for the work attributes."""
        if not self.creation:
            self.creation = time()
        if self.path == ".":
            self.path = environ.get("WORK_PATH", self.path)
        # Update group from WORK_GROUP.
        if not self.group:
            self.group = environ.get("WORK_GROUP", self.group)
        # Update tags from WORK_TAGS.
        if environ.get("WORK_TAGS"):
            tags = environ.get("WORK_TAGS").split(",")
            # If tags are already set, append the new ones.
            if self.tags:
                self.tags.append(tags)
            else:
                self.tags = tags
            self.tags = list(set(self.tags))

    ###########################################################################
    # Work methods
    ###########################################################################

    @property
    def payload(self) -> Dict[str, Any]:
        """Return the dictioanary representation of the work.

        Returns:
            Dict[str, Any]: The payload of the work.
        """
        return asdict(self)

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
    def withdraw(cls, pipeline: str, **kwargs: Dict[str, Any]) -> Optional["Work"]:
        """Withdraw work from the buckets backend.

        Args:
            pipeline (str): Name of the pipeline.
            **kwargs (Dict[str, Any]): Keyword arguments for the Buckets API.

        Returns:
            Work: Work object.
        """
        buckets = Buckets(**kwargs)  # type: ignore
        payload = buckets.withdraw(pipeline)
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
