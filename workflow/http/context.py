"""HTTP client for interacting with the Workflow Servers."""
from typing import Optional

from pydantic import AliasChoices, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from workflow import get_logger
from workflow.http.buckets import Buckets

logger = get_logger("workflow.http.context")


class HTTPContext(BaseSettings):
    """HTTP Context for the Workflow Servers.

    Args:
        BaseSettings (BaseSettings): Pydantic BaseModel with settings.

    Attributes:
        baseurl (str): HTTP baseurl of the buckets backend.
        timeout (float): HTTP Request timeout in seconds.
        token (Optional[SecretStr]): Workflow Access Token.
        buckets (Buckets): Buckets Backend API Client.

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
    baseurl: str = Field(
        default="http://localhost:8004",
        description="HTTP baseurl of the buckets backend.",
        examples=["http://localhost:8004"],
    )
    timeout: float = Field(
        default=15.0,
        ge=1.0,
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
        description="Buckets Backend API Client.",
        exclude=True,
    )

    @model_validator(mode="after")
    def create_buckets_client(self) -> "HTTPContext":
        """Create the buckets client.

        Returns:
            HTTPContext: The current HTTPContext object.
        """
        if not self.buckets:
            try:
                self.buckets = Buckets(
                    baseurl=self.baseurl, token=self.token, timeout=self.timeout
                )
            except Exception as error:
                logger.error("unable to create buckets client")
                raise error
        return self
