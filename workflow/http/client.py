"""HTTP client for interacting with the Workflow Servers."""
from platform import machine, platform, python_version, release, system
from time import asctime, gmtime
from typing import Optional
from warnings import warn

from pydantic import (
    AliasChoices,
    AnyHttpUrl,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from requests import Session, head
from requests.exceptions import RequestException
from requests.models import Response

from workflow import __version__ as version
from workflow import get_logger

logger = get_logger("workflow.http.client")


class Client(BaseSettings):
    """A client for interacting with the Workflow Servers.

    Args:
        BaseModel (BaseModel): Pydantic base model.

    Attributes:
        baseurl (str): Base URLs for the server.
        token (Optional[SecretStr]): Authentication token.
        timeout (float): Request timeout in seconds.
        session (requests.Session): HTTP request session.

    Returns:
        Client: A client for interacting with the Workflow Servers.
    """

    model_config = SettingsConfigDict(
        title="Workflow HTTP Client",
        arbitrary_types_allowed=True,
        env_prefix="WORKFLOW_HTTP_",
        secrets_dir="/run/secrets",
        validate_assignment=True,
        extra="ignore",
    )
    baseurl: str = Field(..., description="Base URLs for the server")
    timeout: float = Field(default=15.0, description="Request timeout in seconds")
    token: Optional[SecretStr] = Field(
        default=None,
        validation_alias=AliasChoices(
            "WORKFLOW_HTTP_TOKEN",
            "WORKFLOW_TOKEN",
            "GITHUB_TOKEN",
            "GITHUB_PAT",
        ),
        description="Authentication token",
    )
    session: Session = Field(
        default=Session(), description="Requests session", exclude=True
    )

    @model_validator(mode="after")
    def configure_session(self) -> "Client":
        """Validates the model after initialization.

        Returns:
            Client: The validated client instance.

        """
        self.session.headers.update({"Content-Type": "application/json; charset=utf-8"})
        self.session.headers.update({"Accept": "*/*"})
        self.session.headers.update({"User-Agent": "workflow-client"})
        self.session.headers.update({"Date": asctime(gmtime())})
        self.session.headers.update({"X-Workflow-Core-Version": version})
        self.session.headers.update(
            {"X-Workflow-Client-Python-Version": python_version()}
        )
        self.session.headers.update({"X-Workflow-Client-Arch": machine()})
        self.session.headers.update({"X-Workflow-Client-OS": system()})
        self.session.headers.update({"X-Workflow-Client-OS-Version": release()})
        self.session.headers.update({"X-Workflow-Client-Platform": platform()})
        if self.token:
            self.session.headers.update(
                {"Authorization": f"Bearer {self.token.get_secret_value()}"}
            )
        logger.debug(f"Configured Session: {self.session.headers}")
        return self

    @field_validator("baseurl")
    def validate_baseurl(cls, baseurl: str) -> str:
        """Validate the baseurl.

        Args:
            baseurl (str): The baseurl to validate.

        Raises:
            AttributeError: The baseurl is not a valid URL.
            RequestException: The baseurl is not reachable.

        Returns:
            str: The validated baseurl.
        """
        try:
            AnyHttpUrl(baseurl)
            response: Response = head(f"{baseurl}/version", timeout=5)
            response.raise_for_status()
        except AttributeError as error:
            logger.exception(error)
            logger.error(f"Invalid baseurl: {baseurl}")
            raise error
        except RequestException as error:
            logger.exception(error)
            raise error
        return baseurl

    @field_validator("token", mode="after", check_fields=True)
    def validate_token(cls, token: Optional[str]) -> Optional[str]:
        """Validate the token.

        Args:
            token (Optional[str]): Token to use for authentication.

        Returns:
            Optional[str]: Token to use for authentication.
        """
        if not token:
            msg = "WORKFLOW_TOKEN missing. Token auth will be required in the future."
            warn(msg, FutureWarning, stacklevel=2)
        return token
