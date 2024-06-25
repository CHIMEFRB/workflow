"""HTTP client for interacting with the Workflow Servers."""

import os
from typing import Any, Dict, List, Optional

from pydantic import (
    AliasChoices,
    Field,
    FilePath,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

from workflow import DEFAULT_WORKSPACE_PATH
from workflow.http.buckets import Buckets
from workflow.http.configs import Configs
from workflow.http.pipelines import Pipelines
from workflow.http.results import Results
from workflow.http.schedules import Schedules
from workflow.utils import read
from workflow.utils.logger import get_logger

logger = get_logger("workflow.http.context")


class HTTPContext(BaseSettings):
    """HTTP Context for the Workflow Servers.

    Args:
        BaseSettings (BaseSettings): Pydantic BaseModel with settings.

    Attributes:
        baseurl (str): HTTP baseurl of the buckets backend.
        timeout (float): HTTP Request timeout in seconds.
        token (Optional[SecretStr]): Workflow Access Token.

    Returns:
        HTTPContext: The current HTTPContext object.
    """

    model_config = SettingsConfigDict(
        title="Workflow Local Context",
        arbitrary_types_allowed=True,
        env_prefix="WORKFLOW_HTTP_",
        secrets_dir="/run/secrets",
        validate_assignment=True,
        extra="ignore",
    )
    workspace: FilePath = Field(
        default=DEFAULT_WORKSPACE_PATH,
        frozen=True,
        description="Path to the workspace configuration.",
        examples=[DEFAULT_WORKSPACE_PATH.as_posix()],
    )
    timeout: float = Field(
        default=15.0,
        ge=0.5,
        le=60.0,
        description="HTTP Request timeout in seconds",
        examples=[15.0],
    )
    token: Optional[SecretStr] = Field(
        default=None,
        validation_alias=AliasChoices(
            "WORKFLOW_HTTP_TOKEN",
            "WORKFLOW_TOKEN",
            "GITHUB_TOKEN",
            "GITHUB_PAT",
        ),
        description="Workflow Access Token.",
        examples=["ghp_1234567890abcdefg"],
    )
    backends: List[str] = Field(
        default=["buckets", "results", "pipelines", "schedules", "configs"],
        description="List of backend services to create clients for.",
        examples=[["buckets", "results", "pipelines", "schedules", "configs"]],
    )
    buckets: Buckets = Field(
        default=None,
        validate_default=False,
        description="Buckets API Client.",
        exclude=True,
    )

    results: Results = Field(
        default=None,
        validate_default=False,
        description="Results API Client.",
        exclude=True,
    )

    configs: Configs = Field(
        default=None,
        validate_default=False,
        description="Configs API Client.",
        exclude=True,
    )

    pipelines: Pipelines = Field(
        default=None,
        validate_default=False,
        description="Pipelines API Client.",
        exclude=True,
    )

    schedules: Schedules = Field(
        default=None,
        validate_default=False,
        description="Schedules API Client.",
        exclude=True,
    )

    @field_validator("workspace", mode="before")
    @classmethod
    def check_workspace_is_set(cls, value: str) -> str:
        """Check that workspace field has a valid filepath.

        Args:
            value (str): FilePath str value.

        Raises:
            ValueError: If path is not a valid file.

        Returns:
            str: FilePath str value.
        """
        if not os.path.isfile(value):
            logger.error("No workspace set.")
            raise ValueError("No workspace set.")
        return value

    @model_validator(mode="after")
    def create_clients(self) -> Self:
        """Create the HTTP Clients for the Workflow Servers.

        Returns:
            Self: The current HTTPContext object.
        """
        clients: Dict[str, Any] = {
            "buckets": Buckets,
            "results": Results,
            "pipelines": Pipelines,
            "schedules": Schedules,
            "configs": Configs,
        }
        logger.debug(f"creating http clients for {self.backends}.")
        config: Dict[str, Any] = read.workspace(self.workspace)
        baseurls = config.get("http", {}).get("baseurls", {})
        logger.debug(f"baseurls: {baseurls}")
        for backend in self.backends:
            baseurl = baseurls.get(backend, None)
            client = getattr(self, backend)
            logger.debug(f"creating {backend} client @ {baseurl}.")
            if baseurl and not client:
                try:
                    setattr(
                        self,
                        backend,
                        clients[backend](
                            baseurl=baseurl, token=self.token, timeout=self.timeout
                        ),
                    )
                    logger.debug(f"created {backend} client @ {baseurl}.")
                except Exception as error:
                    logger.error(f"failed to create {backend} client @ {baseurl}.")
                    logger.error(error)
        return self
