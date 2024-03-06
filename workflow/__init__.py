"""Top-level imports for Tasks API."""

from pathlib import Path

# Root path to the Workflow Module
MODULE_PATH: Path = Path(__file__).absolute().parent.parent
# Path to local configurations
CONFIG_PATH: Path = Path.home() / ".workflow"
# Active Workspace Path
DEFAULT_WORKSPACE_PATH: Path = CONFIG_PATH / "workspaces" / "active.yml"
# Workflow Client Version
__version__ = "0.3.0"  # {x-release-please-version}
