"""Auth Providers for Workflow."""
import os
from pathlib import Path
from typing import Optional

from requests import Session
from pydantic import SecretStr

from workflow.utils import read


def select_provider_method(
    provider: str, method: str, session: Session, token: Optional[SecretStr]
):
    """Selects the authentication provider.

    Parameters
    ----------
    provider : str
        Provider name.
    method : str
        Method name.
    session : Session
        Session object.
       _description_
    """
    match provider:
        case "github":
            return github(method, session, token)
        case _:
            return {}
        # Other methods


def github(method: str, session: Session, token: Optional[SecretStr]) -> None:
    """Handles the authentication methods for GitHub.

    Parameters
    ----------
    method : str
        Method name.
    session : Session
        Session object.
    """
    # ? Take token from OS env
    if method == "token":
        choices = [
            "WORKFLOW_HTTP_TOKEN",
            "WORKFLOW_TOKEN",
            "GITHUB_TOKEN",
            "GITHUB_PAT",
        ]
        for name in choices:
            if name in os.environ.keys():
                session.headers.update({"x-access-token": os.environ[name]})
                break
        else:
            raise ValueError("Could not found GitHub Token.")
