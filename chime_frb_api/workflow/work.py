"""Work Object."""

from json import loads
from os import environ
from pathlib import Path
from time import time
from typing import Any, Dict, List, Literal, Optional, Union
from warnings import warn

from pydantic import BaseModel, Field, StrictFloat, StrictStr, root_validator
from tenacity import retry
from tenacity.stop import stop_after_delay
from tenacity.wait import wait_random

from chime_frb_api.modules.buckets import Buckets


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
        products (Optional[List[StrictStr]]): Data products produced by the work.
        plots (Optional[List[StrictStr]]) Plot files produced by the work.
        id (Optional[StrictStr]): Work ID. Created when work is entered in the database.
        creation (Optional[StrictFloat]): Unix timestamp of when the work was created.
            If none, set to time.time() by default.
        start (Optional[StrictFloat]): Unix timestamp of when the work was started.
        stop (Optional[float]): Unix timestamp of when the work was stopped.
        attempt (StrictInt): Attempt number at performing the work. 0 by default.
        retries (int): Number of retries before giving up. 1 by default.
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
        """Pydantic Config."""

        validate_all = True
        validate_assignment = True

    ###########################################################################
    # Required Attributes. Set by user.
    ###########################################################################
    pipeline: StrictStr = Field(
        ...,
        min_length=1,
        description="Name of the pipeline.",
        example="example-pipeline",
    )
    ###########################################################################
    # Optional attributes, might be provided by the user.
    ###########################################################################
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parameters to pass the pipeline function.",
        example={"event_number": 9385707},
    )
    results: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Results of the work performed, if any.",
        example={"dm": 100.0, "snr": 10.0},
    )
    path: Optional[str] = Field(
        default=environ.get("WORK_PATH", "."),
        description="""
        Base path where the pipeline results are stored.
        Defaults to "." or the value of the WORK_PATH environment variable.
        Used by downstream pipelines to locate work products and plots.
        """,
        example="/arc/projects/chimefrb/",
    )
    event: Optional[List[int]] = Field(
        default=None,
        description="CHIME/FRB Event ID[s] the work was performed against.",
        example=[9385707, 9385708],
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="""
        Searchable tags for the work. Merged with values from env WORK_TAGS.
        """,
        example=["dm-analysis"],
    )
    group: Optional[StrictStr] = Field(
        default=environ.get("WORK_GROUP", None),
        description="""
        CHIME/FRB Working Group. Can be sourced from env WORK_GROUP.
        """,
        example="properties-wg",
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
    products: Optional[List[StrictStr]] = Field(
        default=None,
        description="""
        Name of the non-human-readable data products generated by the pipeline.
        These are direct paths to the data products or paths relative to work.path.
        If archive is True, these data paths will be automatically archived by the
        Datatrail API.
        """,
        example=["spectra.h5", "dm_vs_time.png"],
    )
    plots: Optional[List[StrictStr]] = Field(
        default=None,
        description="""
        Name of visual data products generated by the pipeline.
        These are direct paths to the data products or paths relative to work.path.
        If archive is True, these data paths will be automatically archived by the
        Datatrail API.
        """,
        example=["waterfall.png", "/arc/projects/chimefrb/9385707/9385707.png"],
    )
    site: Literal[
        "chime", "allenby", "kko", "gbo", "hco", "canfar", "cedar", "local", "aro"
    ] = Field(
        default=environ.get("WORK_SITE", "local"),
        description="Site where the work will be performed.",
        example="chime",
    )
    user: Optional[StrictStr] = Field(
        default=None, description="User ID who created the work.", example="shiny"
    )
    archive: bool = Field(
        default=True,
        description="""
        Whether or not to archive the work object, results, plots & products.
        """,
        example=True,
    )

    # Deprecated Attributes to be removed in future versions.
    precursors: Optional[List[Dict[StrictStr, StrictStr]]] = Field(
        default=None,
        deprecated=True,
        description="This field has been deprecated.",
    )
    config: Optional[str] = Field(
        default=None,
        deprecated=True,
        description="This field has been deprecated.",
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
        # Set creation time if not already set
        if values.get("creation") is None:
            values["creation"] = time()
        # Update tags from environment variable WORK_TAGS
        if environ.get("WORK_TAGS"):
            env_tags: List[str] = str(environ.get("WORK_TAGS")).split(",")
            # If tags are already set, append the new ones
            if values.get("tags"):
                values["tags"] = values["tags"] + env_tags
            else:
                values["tags"] = env_tags
            # Remove duplicates
            values["tags"] = list(set(values["tags"]))

        # Check path exists and is a directory
        if values.get("path"):
            path = Path(values.get("path"))  # type: ignore
            assert path.exists(), f"{values.get('path')} does not exist."
            assert path.is_dir(), f"{values.get('path')} is not a directory."

        # Display deprecation warning for precursors & config
        if values.get("precursors") or values.get("config"):
            warn(
                """\n
                The `precursors` & `config` attributes have been deprecated.
                They will be removed in chime-frb-api v3.0.0.
                Please remove them from your code.\n""",
                DeprecationWarning,
                stacklevel=2,
            )
            values["precursors"] = None
            values["config"] = None

        if values.get("site") == "allenby":
            warn(
                """\n
                The `allenby` site name has been deprecated and will be
                removed from chime-frb-api by summer 2023 release.
                Please use site name `kko` instead.\n
                """,
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
        payload: Dict[str, Any] = self.dict()
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
