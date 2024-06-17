"""Definition of Workflow Workspace Configuration."""

from typing import Dict, List, Literal, Union

from pydantic import BaseModel, Field


class Workspace(BaseModel):
    """Definition of Workflow Workspace Configuration.

    Args:
        BaseModel (BaseModel): Pydantic BaseModel.

    Attributes:
        workspace (str): Name of the workflow workspace.
        sites (List[str]): Valid sites for workflow.
        http (Dict): Workflow HTTP URLs.
    """

    workspace: str = Field(
        ...,
        title="Name of the workflow workspace.",
        description="Name describing the purpose/usecase of the workspace.",
        examples=["chimefrb", "champss"],
    )
    sites: List[str] = Field(
        ...,
        title="Valid sites for workflow.",
        description="""
        List of valid sites where work belonging to a workspace can be performed.
        """,
        examples=[["chime", "hco", "frb"]],
    )
    http: Dict[
        Literal["baseurls"],
        Dict[
            Literal[
                "buckets",
                "results",
                "schedules",
                "pipelines",
                "configs",
                "loki",
                "products",
            ],
            Union[str, List[str]],
        ],
    ] = Field(
        ...,
        title="Workflow HTTP URLs",
        description="Baseurls define, the backend services for the workflow system.",
    )

    class Config:
        """Pydantic configuration for the Workspace model."""

        allow_population_by_field_name = True
        # Allow extra fields in the model.
        extra = "allow"
