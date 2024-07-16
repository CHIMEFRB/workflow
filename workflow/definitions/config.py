"""Work Object Configuration."""

from typing import List, Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Archive(BaseSettings):
    """Archive Configuration.

    This class is used to configure the archive strategy for the work.

    Args:
        BaseModel (BaseModel): Pydantic BaseModel.

    Attributes:
        results (bool): Archive results for the work.
        products (str): Archive strategy for the products.
        plots (str): Archive strategy for the plots.
        logs (str): Archive strategy for the logs.
    """

    model_config = SettingsConfigDict(
        title="Workflow Archive Object",
        validate_default=True,
        validate_assignment=True,
        validate_return=True,
        revalidate_instances="always",
        env_prefix="WORKFLOW_CONFIG_ARCHIVE_",
        secrets_dir="/run/secrets",
        extra="ignore",
    )

    results: bool = Field(
        default=True,
        description="Whether to archive the results of the work.",
        examples=[True],
    )
    products: str = Field(
        default="copy",
        description="Archive strategy for the products.",
        examples=["copy"],
    )
    plots: str = Field(
        default="copy",
        description="Archive strategy for the plots.",
        examples=["move"],
    )

    @field_validator("products", "plots")
    def validate_archive(cls, value: str) -> str:
        """Validate the archive strategy.

        Args:
            value (str): Archive strategy.

        Raises:
            ValueError: If the archive strategy is not valid.

        Returns:
            str: The archive strategy.
        """
        strategy = ["bypass", "copy", "delete", "move"]
        if value not in strategy:
            raise ValueError(f"archive strategy must be one of {strategy}")
        return value


class Config(BaseSettings):
    """Workflow Configuration Object.

    Args:
        BaseSettings (BaseSettings): Pydantic BaseModel with settings.

    Attributes:
        archive (Archive): Archive Configuration.
        metrics (bool): Generate metrics from work lifecycle.
        parent (Optional[str]): Parent Pipeline ID. None implies no parent.
        orgs (List[str]): GitHub organization[s] the work belongs to.
        teams (Optional[List[str]]): GitHub Team[s] with access to the work.
    """

    model_config = SettingsConfigDict(
        title="Workflow Config Object",
        validate_default=True,
        validate_assignment=True,
        validate_return=True,
        revalidate_instances="always",
        env_prefix="WORKFLOW_CONFIG_",
        secrets_dir="/run/secrets",
        extra="ignore",
    )

    archive: Archive = Archive()
    metrics: bool = Field(
        default=False,
        description="Metrics for the workflow lifecycle.",
    )
    parent: Optional[str] = Field(
        default=None,
        description="Parent Pipeline ID. None implies no parent.",
        examples=["5f9b5c5d7b54b5a9c5e5b5c5"],
    )
    orgs: List[str] = Field(
        default=["chimefrb"],
        description="""
        GitHub organization[s] the work belongs to. If authentication is enabled,
        this must be a subset of the authenticated user's organizations.""",
        examples=[["octocat", "chimefrb"]],
    )
    teams: Optional[List[str]] = Field(
        default=None,
        description="""
        GitHub Team[s] with access to the work. If authentication is enabled,
        this must be a subset of the authenticated user's teams.
        """,
        examples=[["developers", "admins"]],
    )
    strategy: Literal["strict", "relaxed"] = Field(
        default="strict",
        description="Validation strategy for the work.",
        examples=["strict"],
        exclude=True,
    )
