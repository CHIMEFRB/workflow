"""Auth Providers for Workflow."""
from pathlib import Path

from requests import Session

from workflow.utils import read

GITHUB_TOKEN_LOCATION = f"{Path.home()}/.config/gh/hosts.yml"


def select_provider_method(provider: str, method: str, session: Session):
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
            return github(method, session)
        case _:
            return {}
        # Other methods


def github(method: str, session: Session) -> None:
    """Handles the authentication methods for GitHub.

    Parameters
    ----------
    method : str
        Method name.
    session : Session
        Session object.
    """
    if method == "token":
        hosts = read.filename(GITHUB_TOKEN_LOCATION)
        session.headers.update({"x-access-token": hosts["github.com"]["oauth_token"]})
