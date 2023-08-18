"""Example Workflow Settings."""
from typing import Optional

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich import print


class ExampleSettings(BaseSettings):
    """Example Workflow Settings.

    Args:
        BaseSettings (BaseSettings): Pydantic BaseSettings.

    Note:
        In case a value is specified in multiple places, the priority is:
            1. Arguments passed to the `Settings` constructor.
            2. Environment variables.
            3. Variables loaded from the secrets directory.
            4. The default values in the Settings class.

    Returns:
        Settings: Workflow settings.
    """

    model_config = SettingsConfigDict(
        title="Example Workflow Settings",
        env_prefix="WORKFLOW_",
        secrets_dir="/run/secrets",
        validate_assignment=True,
        extra="ignore",
    )

    token: Optional[SecretStr] = Field(
        default=None,
        validation_alias=AliasChoices(
            "WORKFLOW_TOKEN",
            "WORKFLOW_ACCESS_TOKEN",
            "GITHUB_TOKEN",
            "GITHUB_ACCESS_TOKEN",
            "GITHUB_PAT",
            "GITHUB_PERSONAL_ACCESS_TOKEN",
            "GITHUB_OAUTH_TOKEN",
            "GITHUB_OAUTH_ACCESS_TOKEN",
        ),
    )

    buckets_baseurl: Optional[str] = Field(
        default="http://localhost:8004",
        validation_alias=AliasChoices(
            "WORKFLOW_BUCKETS_BASEURL",
        ),
    )

    results_baseurl: Optional[str] = Field(
        default="http://localhost:8005",
        validation_alias=AliasChoices(
            "WORKFLOW_RESULTS_BASEURL",
        ),
    )

    pipelines_baseurl: Optional[str] = Field(
        default="http://localhost:8006",
        validation_alias=AliasChoices(
            "WORKFLOW_PIPELINES_BASEURL",
        ),
    )

    loki_baseurl: Optional[str] = Field(
        default="http://localhost:8007",
        validation_alias=AliasChoices(
            "WORKFLOW_LOKI_BASEURL",
        ),
    )


if __name__ == "__main__":
    print(ExampleSettings().model_dump())  # type: ignore
