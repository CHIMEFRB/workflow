"""Check if the process is running in a container."""

from typing import Optional


def virtualization() -> Optional[str]:
    """Check if the process is running in a container.

    Returns:
        str: Container type
    """
    try:
        with open("/proc/1/cgroup") as f:
            for line in f.readlines():
                if "docker" in line:
                    return "docker"
                elif "kubepod" in line:
                    return "kubernetes"
    except Exception:
        pass
    return None
