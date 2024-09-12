"""Functions to render objects to rich.console."""

import datetime as dt
import re
from json import dumps as json_dumps
from typing import Any, Dict

from rich.text import Text

from workflow.http.context import HTTPContext
from workflow.utils.variables import status_colors, status_symbols


def render_timestamp(timestamp: float) -> str:
    """Converts a timestamp into a readable string.

    Parameters
    ----------
    timestamp : float
        Timestamp.

    Returns
    -------
    str
        Formatted timestamp.
    """
    from_dt: dt.datetime = dt.datetime.fromtimestamp(timestamp)
    formatted_dt: str = dt.datetime.strftime(from_dt, "%m-%d-%Y, %H:%M:%S")
    return formatted_dt


def render_pipeline(payload: Dict[str, Any], history: bool = False) -> Text:
    """Renders a pipeline to rich.Text().

    Parameters
    ----------
    payload : Dict[str, Any]
        Pipeline payload.
    history : bool
        If history field needs to be rendered.

    Returns
    -------
    Text
        Rendered text.
    """
    steps_field = "steps"
    history_field = "history"
    time_fields = ["creation", "start", "stop"]
    text = Text()
    for k, v in payload.items():
        if k == "history" and not history:
            continue
        if not v:
            continue
        key_value_text = Text()
        if k in time_fields and v:
            v = render_timestamp(float(v))
        if k == steps_field:
            key_value_text = Text(f"{k}: \n", style="bright_blue")
            for step in v:
                key_value_text.append(f"  {step['name']}:")
                key_value_text.append(f"{status_symbols[step['status']]}\n")
        elif k == history_field:
            key_value_text = Text(f"{k}: \n", style="bright_blue")
            for timestamp in v.keys():
                rendered = render_timestamp(float(timestamp))
                key_value_text.append(f"  {rendered}:\n", style="bright_green")
                for execution in v[timestamp].keys():
                    key_value_text.append(f"{' ' * 4}{execution}:\n")
                    for work in v[timestamp][execution]:
                        key_value_text.append(f"{' ' * 6}{work}\n", style="white")
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
    time_fields = ["creation", "start", "stop"]
    query = json_dumps({"id": {"$in": payload["pipelines"]}})
    projection = json_dumps({"id": 1, "status": 1})
    pipelines_statuses = http.pipelines.get_pipelines(
        name=payload["name"],
        query=query,
        projection=projection,
    )

    for k, v in payload.items():
        if k in hidden_keys:
            continue
        key_value_text = Text()
        if k in time_fields and v:
            v = render_timestamp(float(v))
        if k == "pipelines":
            key_value_text.append(f"{k}: \n", style="bright_blue")
            for status in pipelines_statuses:
                key_value_text.append(
                    f"\t{status['id']}: ",  # type: ignore
                    style=f"{status_colors[status['status']]}",  # type: ignore
                )
                key_value_text.append(
                    f"{status_symbols[status['status']]}\n",  # type: ignore
                    style=status_colors[status["status"]],  # type: ignore
                )
            text.append_text(key_value_text)
            continue
        if k == "deployments":
            key_value_text.append(f"{k}: \n", style="bright_blue")
            if v:
                for deployment in v:
                    key_value_text.append_text(render_dict(deployment))
                    key_value_text.append("\n")
                text.append_text(key_value_text)
                continue
            continue
        key_value_text.append(f"{k}: ", style="bright_blue")
        key_value_text.append(f"{v}\n", style="white")
        text.append_text(key_value_text)

    return text


def render_dict(payload: Dict[str, Any], listing: bool = True) -> Text:
    """TODO: Missing docstring.

    Args:
        payload: [TODO:description]
        listing: [TODO:description]

    Returns:
        [TODO:return]
    """
    text = Text(" - " if listing else "")
    for i_k, i_v in payload.items():
        if isinstance(i_v, dict):
            text.append(render_dict(i_v, listing=False))
            continue
        text.append(f"\t{i_k}: ", style="bright_green")
        text.append(f"{i_v}\n")
    return text


def clean_output(message: str) -> str:
    """Cleans strings from Click.command output.

    Parameters
    ----------
    message : str
        String to be cleaned.

    Returns
    -------
    str
        Escaped string.
    """
    ansi_escape = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", message)
