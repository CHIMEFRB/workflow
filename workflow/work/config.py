"""Work Object Configuration."""
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class Archive(BaseModel):
    """Archive Configuration.

    This class is used to configure the archive strategy for the work.

    Args:
        BaseModel (BaseModel): Pydantic BaseModel.

    Attributes:
        results (bool): Archive results for the work.
        products (Literal["pass", "copy", "move", "delete", "upload"]):
            Archive strategy for the products.
        plots (Literal["pass", "copy", "move", "delete", "upload"]):
            Archive strategy for the plots.
        logs (Literal["pass", "copy", "move", "delete", "upload"]):
            Archive strategy for the logs.
    """

    model_config = ConfigDict(validate_default=True, validate_assignment=True)

    results: bool = Field(
        default=True,
        description="Archive results for the work.",
    )
    products: Literal["pass", "copy", "move", "delete", "upload"] = Field(
        default="copy",
        description="Archive strategy for the products.",
    )
    plots: Literal["pass", "copy", "move", "delete", "upload"] = Field(
        default="copy",
        description="Archive strategy for the plots.",
    )
    logs: Literal["pass", "copy", "move", "delete", "upload"] = Field(
        default="move",
        description="Archive strategy for the logs.",
    )


class Config(BaseModel):
    """Work Object Configuration.

    This class is used to configure the work object.

    Args:
        BaseModel (BaseModel): Pydantic BaseModel.
    """

    model_config = ConfigDict(validate_default=True, validate_assignment=True)

    archive: Archive = Archive()
    metrics: bool = Field(
        default=False,
        description="Generate metrics from work lifecycle.",
    )
    parent: Optional[str] = Field(
        default=None,
        description="ID of the parent workflow pipeline.",
        json_schema_extra={"examples": ["5f9b5c5d7b54b5a9c5e5b5c5"]},
    )
    orgs: List[str] = Field(
        default=["chimefrb"],
        description="""
        List of organization[s] the work belongs to.
        Maps to the Github organization.
        """,
        json_schema_extra={"examples": ["chimefrb", "chime-sps"]},
    )
    teams: Optional[List[str]] = Field(
        default=None,
        description="""
        List of team[s] the work belongs to.
        Maps to the Github team within the organization.
        """,
        json_schema_extra={"example": ["frb-tsars", "frb-ops"]},
    )
