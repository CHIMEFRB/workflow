"""Notification Configuration."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, StrictStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Slack(BaseSettings):
    """Slack Configuration.

    This class is used to configure the slack notification strategy for the work.

    Args:
        BaseModel (BaseModel): Pydantic BaseModel.

    Attributes:
        channel_id (str): Slack channel to send notifications to.
        member_ids (List[str]): Slack members to send notifications to.
        message (str): Slack message to send notifications with.
        results (bool): Send slack notifications with the work results.
        products (bool): Send slack notifications with the work product links.
        plots (bool): Send slack notifications with the work plot links.
        blocks (Dict[str, Any]): Slack blocks to send notifications with.
        reply (Dict[str, Any]): Status of the slack notification.
    """

    model_config = SettingsConfigDict(
        title="Workflow Notify Object",
        validate_default=True,
        validate_assignment=True,
        validate_return=True,
        revalidate_instances="always",
        env_prefix="WORKFLOW_NOTIFY_SLACK_",
        secrets_dir="/run/secrets",
        extra="forbid",
    )

    channel_id: Optional[StrictStr] = Field(
        default=None,
        description="Slack channel to send notifications to.",
        examples=["C01JYQZQX0Y"],
    )
    member_ids: Optional[List[StrictStr]] = Field(
        default=None,
        description="Slack members to send notifications to.",
        examples=[["U01JYQZQX0Y"]],
    )
    message: Optional[StrictStr] = Field(
        default=None,
        description="Slack message to send notifications with.",
        examples=["Hello World!"],
    )
    results: Optional[bool] = Field(
        default=None,
        description="Send slack notifications with the work results.",
    )
    products: Optional[bool] = Field(
        default=None,
        description="Send slack notifications with the work product links.",
    )
    plots: Optional[bool] = Field(
        default=None,
        description="Send slack notifications with the work plot links.",
    )
    blocks: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Slack blocks to send notifications with.",
    )
    reply: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Status of the slack notification.",
        examples=[{"ok": True}],
    )


class Notify(BaseModel):
    """Work Object Notification Configuration.

    Args:
        BaseModel (BaseModel): Pydantic BaseModel.

    Attributes:
        slack (Slack): Send slack notifications for the work.
    """

    slack: Slack = Field(
        default_factory=Slack,
        description="Send slack notifications for the work.",
        examples=[Slack()],
    )
