"""Work Object."""

from json import dumps, loads
from time import time
from typing import Any, Dict, List, Optional

from attr import asdict, attrib, attrs
from attr.setters import validate
from attr.validators import in_, instance_of, optional

# Validator for the Work.site attribute.
PRIORITIES = range(1, 6)
STATUSES = ["created", "queued", "running", "success", "failure"]
SITES = ["chime", "allenby", "gbo", "hatcreek", "canfar", "cedar", "local"]


@attrs(auto_attribs=True, slots=True, on_setattr=validate)  # type: ignore
class Work:
    """Work Object.

    Parameters
    ----------
        pipeline : str
            Name of the pipeline. Required.
        parameters : Optional[Dict[str, Any]]
            Parameters to pass to the pipeline. None by default.
        results : Optional[Dict[str, Any]]
            Results from the pipeline. None by default.
        path : str
            Base data path where the results will be stored. "." by default.
        events : Optional[List[int]]
            List of CHIME/FRB event numbers related to work. None by default.
        tags : Optional[List[str]]
            List of searchable tags related to work. None by default.
        group : Optional[str]
            Name of the working group. None by default.
        timeout : int
            Timeout in seconds. 3600 by default.
        priority : int
            Priority of the work. Ranges from 1(lowest) to 5(highest).
            3 by default.
        precursors : Optional[List[Dict[str, str]]]
            List of precursors work ids used as input. None by default.
        products : Optional[List[str]]
            Data products produced by the work. None by default.
        plots : Optional[List[str]]
            Plot files produced by the work. None by default.
        id : Optional[str]
            Work ID. Created when work is entered in the database. None by default.
        creation: float
            Unix timestamp of when the work was created. time.time() by default.
        start : Optional[float]
            Start time of the work. None by default.
        stop : Optional[float]
            Stop time of the work. None by default.
        attempt: int
            Attempt number at performing the work. 0 by default.
        retries: int
            Number of tries before the work is considered failed. 1 by default.
        config : Optional[str]
            Configuration ID of the pipeline. None by default.
        status : str
            Status of the work. "created" by default.
            Valid values: "created", "queued", "running", "success", "failure"
        site : str
            Site where the work is being run. "local" by default.
        user : Optional[str]
            User who submitted the work. None by default.
        archive : bool
            Whether or not to archive the work. True by default.

    Raises
    ------
        TypeError
            If any of the parameters are not of the correct type.
        ValueError
            If any of the parameters are not of the correct value.

    Returns
    -------
        work : Work
            Work object.
    """

    ###########################################################################
    # Required attributes provided by the user
    ###########################################################################
    # Name of the pipeline. Set by user.
    pipeline: str = attrib(validator=instance_of(str))
    ###########################################################################
    # Optional attributes provided by the user.
    ###########################################################################
    # Parameters to pass the pipeline. Set by user.
    parameters: Optional[Dict[str, Any]] = attrib(
        default=None, validator=optional(instance_of(dict))
    )
    # Results of the work performed.
    # Set automatically by @pipeline decorator.
    # Can also be set manually by user.
    results: Optional[Dict[Any, Any]] = attrib(
        default=None, validator=optional(instance_of(dict))
    )
    # Base data directory where the pipeline will store its data.
    # Overwritten automatically by tasks.fetch() when default.
    # Value sourced from environment variable TASK_PATH.
    # Can also be set manually by user.
    path: str = attrib(default=".", validator=instance_of(str))
    # Name of the CHIME/FRB Event the work was performed against.
    # Set by user.
    event: Optional[List[int]] = attrib(
        default=None, validator=optional(instance_of(list))
    )
    # Searchable tags for the work.
    # Set by user.
    # Automatically appended by tasks.fetch() for each unique tag.
    # Value sourced from environment variable TASK_TAGS.
    tags: Optional[List[str]] = attrib(
        default=None, validator=optional(instance_of(list))
    )
    # Name of the working group responsible for managing the work.
    # Automatically overwritten by tasks.fetch() when default.
    # Can be set manually by user.
    # Value sourced from environment variable TASK_GROUP.
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
    # used as inputs to the current work.
    # Automatically appended whenever results.get() from ResultsAPI is called.
    # Can also be set manually by user.
    precursors: Optional[List[Dict[str, str]]] = attrib(
        default=None, validator=optional(instance_of(list))
    )
    # Name of the non-human-readable data products generated by the pipeline.
    # Relative path from the current working directory.
    # When saving the data products, the TasksAPI will autommatically move them
    # to path + relative path.
    # Set by user.
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
    # Automatically set by task.fetch()
    start: Optional[float] = attrib(
        default=None, validator=optional(instance_of(float))
    )
    # Stop time of the work, in seconds since the epoch.
    # If the work is still running, this will be None.
    # Automatically set by tasks.complete().
    stop: Optional[float] = attrib(default=None, validator=optional(instance_of(float)))
    # Configuration of the pipeline used to perform the work.
    # Automatically overwritten by tasks.fetch()
    # Value sourced from environment variable TASK_CONFIG.
    config: Optional[str] = attrib(default=None, validator=optional(instance_of(str)))
    # Numbered attempt at performing the work.
    # Cannot be set manually.
    attempt: int = attrib(default=0, validator=instance_of(int))
    # Status of the work.
    # Default is "created"
    # Automatically set by the buckets backend at
    #   work.deposit to queued
    #   Work.withdraw(pipeline="name") to running
    #   work.finish(status=True|False) to success | failure
    status: str = attrib(default="created", validator=(in_(STATUSES)))
    # Name of the site where pipeline was executed.
    # Automatically overwritten by tasks.fetch()
    # Value sourced from environment variable TASK_SITE.
    site: str = attrib(default="local", validator=in_(SITES))
    # Name of the user who submitted the work.
    # Set by tasks.deposit() and based on the access token.
    user: Optional[str] = attrib(default=None, validator=optional(instance_of(str)))
    # Whether the work will be archived after completion.
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

    ###########################################################################
    # Work methods
    ###########################################################################

    @property
    def payload(self) -> Dict[str, Any]:
        """Return dictionary representation of the work object."""
        return asdict(self)

    @property
    def json(self) -> str:
        """Return json representation of the work object."""
        return dumps(self.payload)

    @classmethod
    def from_json(cls, json_str: str) -> "Work":
        """Return Work object created from json string."""
        return cls(**loads(json_str))

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Work":
        """Return Work object created from dictionary."""
        return cls(**payload)

    ###########################################################################
    # HTTP Methods
    ###########################################################################

    @classmethod
    def fetch(cls, pipeline: str) -> "Work":
        """Fetch work from task queue and return a work object."""
        pass

    def deposit(self) -> bool:
        """Deposits work payload into the task queue."""
        pass

    def complete(self, status: str) -> bool:
        """Complete work."""
        pass
