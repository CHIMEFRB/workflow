"""Top-level imports for Tasks API."""

from pathlib import Path
from warnings import filterwarnings

# Ignore UserWarnings from pydantic_settings module
# These usually come when no docker secrets are found
filterwarnings("ignore", category=UserWarning, module="pydantic_settings")

# Root path to the Workflow Module
MODULE_PATH: Path = Path(__file__).absolute().parent.parent
# Path to local configurations
CONFIG_PATH: Path = Path.home() / ".config" / "workflow"
# Active Workspace Path
DEFAULT_WORKSPACE_PATH: Path = CONFIG_PATH / "workspace.yml"
# Workflow Client Version
__version__ = "1.4.0"  # {x-release-please-version}
