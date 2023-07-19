"""Workflow Settings."""
from typing import List, Optional

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Workflow Settings.

    Args:
        BaseSettings (BaseSettings): Pydantic BaseSettings.

    Returns:
        Settings: Workflow settings.
    """

    model_config = SettingsConfigDict(
        env_prefix="WORKFLOW_",
        env_file="workflow.env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        secrets_dir="/run/secrets",
        str_to_lower=True,
        case_sensitive=True,
        extra="ignore",
    )

    token: Optional[SecretStr] = Field(
        default=None,
        validation_alias=AliasChoices(
            "WORKFLOW_TOKEN",
            "GITHUB_TOKEN",
            "GITHUB_PAT",
            "GITHUB_ACCESS_TOKEN",
            "GITHUB_PERSONAL_ACCESS_TOKEN",
        ),
    )

    sites: Optional[List[str]] = Field(
        default=None,
        validation_alias=AliasChoices(
            "SITES",
            "WORKFLOW_SITES",
        ),
    )

    tags: Optional[List[str]] = Field(
        default=None,
        validation_alias=AliasChoices(
            "TAGS",
            "WORKFLOW_TAGS",
        ),
    )

    @field_validator("sites", mode="before")
    def sites_validator(cls, sites: str) -> List[str]:
        """Sites Validator.

        Args:
            sites (str): Value of the sites setting.

        Returns:
            List[str]: List of sites.
        """
        return sites.split(",")


if __name__ == "__main__":
    print(Settings().model_dump())  # type: ignore
