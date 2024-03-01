"""HTTP client for interacting with the Workflow Servers."""

from typing import Any, Dict, Optional

from pydantic import AliasChoices, Field, FilePath, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from workflow import DEFAULT_WORKSPACE_PATH
from workflow.http.buckets import Buckets
from workflow.http.pipelines import Pipelines
from workflow.http.results import Results
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
        description="Path to the active workspace configuration.",
        examples=["/path/to/workspace/config.yaml"],
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

    pipelines: Pipelines = Field(
        default=None,
        validate_default=False,
        description="Pipelines API Client.",
        exclude=True,
    )

    @model_validator(mode="after")
    def create_clients(self) -> "HTTPContext":
        """Create the HTTP Clients for the Workflow Servers.

        Returns:
            HTTPContext: The current HTTPContext object.
        """
        clients: Dict[str, Any] = {
            "buckets": Buckets,
            "results": Results,
            "pipelines": Pipelines,
        }
        logger.debug(f"creating http clients for {list(clients.keys())}")
        config: Dict[str, Any] = read.workspace(self.workspace)
        baseurls = config.get("http", {}).get("baseurls", {})
        logger.debug(f"baseurls: {baseurls}")
        for _name, _class in clients.items():
            baseurl = baseurls.get(_name, None)
            client = getattr(self, _name)
            if baseurl and not client:
                try:
                    setattr(
                        self,
                        _name,
                        _class(baseurl=baseurl, token=self.token, timeout=self.timeout),
                    )
                    logger.debug(f"created {_name} client @ {baseurl}.")
                except Exception as error:
                    logger.error(f"failed to create {_name} client @ {baseurl}.")
                    logger.exception(error)
                    raise error
        return self
