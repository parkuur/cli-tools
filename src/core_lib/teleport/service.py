"""Service layer for teleport functionality.

This module exposes ``TeleportService``, a thin service wrapper around the
lower-level :mod:`core_lib.teleport.actions` helpers. It runs database
migrations on initialization and provides convenience methods used by the CLI
and tests.
"""

import logging
import sqlite3
from pathlib import Path

from core_lib.common import exceptions, utils
from core_lib.common import metadata as meta
from core_lib.common.db import open_db, run_tool_migrations
from core_lib.teleport import actions, migrations
from core_lib.teleport.models import Alias

logger = logging.getLogger("teleport")


class TeleportService:
    """Service for manipulating teleport aliases.

    The class uses short-lived sqlite connections for each operation and runs
    migrations on construction to ensure the schema is present.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        # Run migrations at init using a short-lived connection
        conn = open_db(self.db_path)
        try:
            run_tool_migrations(conn, "teleport", migrations.MIGRATIONS)
        finally:
            conn.close()

    def _conn(self) -> sqlite3.Connection:
        """Open a short-lived DB connection for a single operation."""
        return open_db(self.db_path)

    def pin(self, alias: str, path: Path, *, overwrite: bool = False) -> Alias:
        """Create or update an alias for the provided path.

        Relative paths are resolved to absolute ones. If ``overwrite`` is
        False and the alias already exists, :class:`AliasConflictError` is
        raised.
        """
        alias_s = alias
        path_s = str(path)
        utils.validate_path(path_s)
        resolved = str(Path(path).resolve())

        conn = self._conn()
        try:
            existing = actions.get_alias(conn, alias_s)
            if existing and not overwrite:
                raise exceptions.AliasConflictError(f"Alias {alias_s} exists")

            if not Path(resolved).exists():
                logger.warning("Pinning non-existent path: %s", resolved)

            if existing and overwrite:
                return actions.update_alias(conn, alias_s, resolved)
            return actions.insert_alias(conn, alias_s, resolved)
        finally:
            conn.close()

    def unpin(self, alias: str) -> None:
        """Remove an alias from the database.

        Raises :class:`AliasNotFoundError` if the alias does not exist.
        """
        conn = self._conn()
        try:
            existing = actions.get_alias(conn, alias)
            if not existing:
                raise exceptions.AliasNotFoundError(alias)
            actions.delete_alias(conn, alias)
        finally:
            conn.close()

    def resolve(self, alias: str, cwd: Path) -> Path | None:
        """Resolve an alias to a filesystem path.

        Records the current ``cwd`` as the previous path, increments visit
        counts and records a history entry. Returns the resolved :class:`Path`
        or ``None`` when the alias is not found.
        """
        conn = self._conn()
        try:
            a = actions.get_alias(conn, alias)
            if a is None:
                return None

            # store previous path metadata
            meta.set_metadata(conn, "teleport", "previous_path", str(cwd))

            # increment visit count and record history
            # a.id is Optional[int] in the model; ensure not None before calling
            if a.id is not None:
                actions.increment_visit_count(conn, a.id)
            actions.insert_history(conn, a.id, a.path, "jump")
            actions.prune_history(conn, limit=1000)
            return a.as_path()
        finally:
            conn.close()

    def list_aliases(self) -> list[Alias]:
        """Return all aliases stored in the database."""
        conn = self._conn()
        try:
            return actions.list_aliases(conn)
        finally:
            conn.close()

    def previous(self) -> Path | None:
        """Return the last recorded previous path, or ``None`` if unset."""
        conn = self._conn()
        try:
            val = meta.get_metadata(conn, "teleport", "previous_path")
            return None if val is None else Path(val)
        finally:
            conn.close()

    def show(self, alias: str | None = None) -> list[Alias]:
        """Show information about aliases.

        When ``alias`` is ``None``, return all aliases; otherwise return a
        single-element list with the matching alias or raise
        :class:`AliasNotFoundError` when not present.
        """
        conn = self._conn()
        try:
            if alias is None:
                return actions.list_aliases(conn)
            a = actions.get_alias(conn, alias)
            if a is None:
                raise exceptions.AliasNotFoundError(alias)
            return [a]
        finally:
            conn.close()
