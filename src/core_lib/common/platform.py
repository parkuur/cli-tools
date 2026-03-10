"""Platform helpers for locating data directories and DB path.

This module provides small helpers to determine the per-user data directory
and the path to the sqlite database used by the CLI tools.
"""

import os
import sys
from pathlib import Path


def get_data_dir() -> Path:
    """Return a per-user data directory for storing CLI state.

    The directory is created with restrictive permissions where possible and
    can be overridden using the ``CLI_TOOLS_DATA_DIR`` environment variable.
    """
    env = os.environ.get("CLI_TOOLS_DATA_DIR")
    if env:
        p = Path(env)
        p.mkdir(parents=True, exist_ok=True)
        try:
            p.chmod(0o700)
        except OSError:
            # chmod may fail on some platforms or permissions; ignore.
            pass
        return p

    if sys.platform == "darwin":
        p = Path.home() / "Library" / "Application Support" / "cli-tools"
    elif sys.platform.startswith("linux"):
        xdg = os.environ.get("XDG_DATA_HOME")
        if xdg:
            p = Path(xdg) / "cli-tools"
        else:
            p = Path.home() / ".local" / "share" / "cli-tools"
    elif sys.platform.startswith("win"):
        local = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or Path.home()
        p = Path(local) / "cli-tools"
    else:
        p = Path.home() / ".local" / "share" / "cli-tools"

    p.mkdir(parents=True, exist_ok=True)
    try:
        p.chmod(0o700)
    except OSError:
        # ignore chmod failures
        pass
    return p


def get_db_path() -> Path:
    """Return the path to the sqlite database used by the CLI tools."""
    return get_data_dir() / "cli-tools.db"
