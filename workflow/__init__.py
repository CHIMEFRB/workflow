"""Top-level imports for Tasks API."""
from logging import getLogger
from pathlib import Path

import toml
from pkg_resources import DistributionNotFound, get_distribution

# Root path to the Skaha Project
BASE_PATH: Path = Path(__file__).absolute().parent.parent
__version__: str = "unknown"

logger = getLogger(__name__)

try:
    __version__ = get_distribution("workflow").version
except DistributionNotFound as error:  # pragma: no cover
    logger.warning(error)
    pyproject = toml.load(BASE_PATH / "pyproject.toml")
    __version__ = pyproject["tool"]["poetry"]["version"]
except Exception as error:  # pragma: no cover
    logger.warning(error)
    logger.warning("unable to find workflow client version")

from workflow.utils.logger import get_logger  # noqa: F401, E402 isort:skip
from workflow.definitions.work import Work  # noqa: F401, E402
