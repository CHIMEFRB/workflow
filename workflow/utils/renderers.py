"""Functions to render objects to rich.console."""

import datetime as dt
from json import dumps
from typing import Any, Dict

from rich.text import Text

from workflow.http.context import HTTPContext
from workflow.utils.variables import status_colors, status_symbols


def render_pipeline(payload: Dict[str, Any]) -> Text:
    """Renders a pipeline to rich.Text().

    Parameters
    ----------
    payload : Dict[str, Any]
        Pipeline payload.

    Returns
    -------
    Text
        Rendered text.
    """
    steps_field = "steps"
    time_fields = ["creation", "start", "stop"]
    text = Text()
    for k, v in payload.items():
        key_value_text = Text()
        if not v:
            continue
        if k in time_fields and v:
            v = dt.datetime.fromtimestamp(v)
        if k == steps_field:
            key_value_text = Text(f"{k}: \n", style="bright_blue")
            for step in v:
                key_value_text.append(f"  {step['name']}:")
                key_value_text.append(f"{status_symbols[step['status']]}\n")
        else:
            key_value_text = Text(f"{k}: ", style="bright_blue")
            key_value_text.append(
                f"{v}\n", style="white" if k != "status" else status_colors[v]
            )
        text.append_text(key_value_text)
    return text


def render_config(http: HTTPContext, payload: Dict[str, Any]) -> Text:
    """Renders a config to rich.Text().

    Parameters
    ----------
    http : HTTPContext
        Workflow Http context.
    payload : Dict[str, Any]
        Config payload.

    Returns
    -------
    Text
        Rendered text.
    """
    text = Text()
    hidden_keys = ["yaml", "services", "name"]
    query = dumps({"id": {"$in": payload["children"]}})
    projection = dumps({"id": 1, "status": 1})
    children_statuses = http.configs.get_configs(
        database="pipelines",
        config_name=payload["name"],
        query=query,
        projection=projection,
    )

    for k, v in payload.items():
        if k in hidden_keys:
            continue
        key_value_text = Text()
        if k == "children":
            key_value_text.append(f"{k}: \n", style="bright_blue")
            for child in children_statuses:
                key_value_text.append(
                    f"\t{child['id']}: ", style=status_colors[child["status"]]
                )
                key_value_text.append(
                    f"{status_symbols[child['status']]}\n",
                    style=status_colors[child["status"]],
                )
            text.append_text(key_value_text)
            continue
        key_value_text.append(f"{k}: ", style="bright_blue")
        key_value_text.append(f"{v}\n", style="white")
        text.append_text(key_value_text)

    return text
