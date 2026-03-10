# Teleport — Test Specification

Last updated: 2026-03-10  
Status: **Active**

This document enumerates every test that must exist and pass before the teleport tool is considered complete. Tests are written before the implementation code they cover (red → green → refactor). The test structure mirrors the implementation layers described in `teleport.spec.md`.

---

## 1. Approach

- **TDD**: each implementation step in §12 of `teleport.spec.md` begins by writing the tests in this document. The implementation is complete when all tests for that step are green.
- **Real on-disk SQLite** for all DB tests: use `pytest`'s `tmp_path` fixture. Never use `:memory:` — in-memory DBs hide WAL and `PRAGMA` edge cases.
- **No mocking of sqlite3**: test behaviour through the real DB. Mock only `os` calls (e.g., `os.getcwd()`) and env vars via `monkeypatch`.
- **subprocess for CLI tests**: invoke `uv run tp-cli` with `CLI_TOOLS_DATA_DIR` pointing to a temp dir. Check stdout, stderr, and exit code exactly.
- **Markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.shell`. CI runs unit and integration on all platforms; shell tests run on Linux only.

---

## 2. Tooling & configuration

`pyproject.toml` test configuration:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
markers = [
    "unit: unit tests (fast, no subprocess)",
    "integration: integration tests via subprocess",
    "shell: shell wrapper tests (Linux only)",
]
```

Run commands:
- All tests: `uv run pytest`
- Unit only: `uv run pytest -m unit`
- Integration only: `uv run pytest -m integration`
- With coverage: `uv run pytest --cov=src --cov-report=term-missing`

---

## 3. Shared fixtures (`tests/conftest.py`)

```python
import pytest
from pathlib import Path
from core_lib.common.db import open_db, ensure_common_schema, run_tool_migrations
from core_lib.teleport.migrations import MIGRATIONS
from core_lib.teleport.service import TeleportService

@pytest.fixture()
def tmp_db_path(tmp_path: Path) -> Path:
    """Return path to a fresh, schema-initialised cli-tools.db in a temp dir."""
    db = tmp_path / "cli-tools.db"
    conn = open_db(db)
    ensure_common_schema(conn)
    conn.close()
    return db

@pytest.fixture()
def tmp_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set CLI_TOOLS_DATA_DIR to a temp dir and return it."""
    monkeypatch.setenv("CLI_TOOLS_DATA_DIR", str(tmp_path))
    return tmp_path

@pytest.fixture()
def teleport_service(tmp_db_path: Path) -> TeleportService:
    """Return a TeleportService backed by a fresh temp DB."""
    return TeleportService(tmp_db_path)
```

---

## 4. Unit tests — `core_lib/common`

### 4.1 `tests/unit/core/common/test_db.py`

**`open_db`**

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| DB-01 | `test_open_db_returns_connection` | `open_db(path)` returns a `sqlite3.Connection` without raising |
| DB-02 | `test_open_db_wal_mode` | `PRAGMA journal_mode` on a new connection returns `"wal"` |
| DB-03 | `test_open_db_foreign_keys` | `PRAGMA foreign_keys` returns `1` |
| DB-04 | `test_open_db_row_factory` | Rows returned by queries are `sqlite3.Row` instances (subscriptable by column name) |
| DB-05 | `test_open_db_creates_file` | The `.db` file is created on disk if it did not exist |

**`ensure_common_schema`**

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| DB-06 | `test_ensure_common_schema_creates_migrations_table` | `_migrations` table exists after call |
| DB-07 | `test_ensure_common_schema_creates_metadata_table` | `metadata` table exists with `(tool, key)` primary key |
| DB-08 | `test_ensure_common_schema_idempotent` | Calling twice does not raise and tables remain intact |

**`run_tool_migrations`**

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| DB-09 | `test_run_tool_migrations_applies_pending` | A fresh migration list is applied; rows appear in `_migrations` |
| DB-10 | `test_run_tool_migrations_records_version_and_name` | `_migrations` row has correct `tool`, `version`, `name` values |
| DB-11 | `test_run_tool_migrations_idempotent` | Running same migrations twice does not re-apply or raise |
| DB-12 | `test_run_tool_migrations_partial_resume` | If version 1 was already applied, only version 2 is applied |
| DB-13 | `test_run_tool_migrations_tool_isolation` | Migrations for tool A do not affect `_migrations` rows for tool B |
| DB-14 | `test_run_tool_migrations_failure_rolls_back` | A migration whose `forward` raises leaves the DB unmodified and raises `MigrationError` |
| DB-15 | `test_run_tool_migrations_empty_list` | Passing an empty `MIGRATIONS` list is a no-op (no error, no rows inserted) |

---

### 4.2 `tests/unit/core/common/test_platform.py`

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| PL-01 | `test_get_data_dir_env_override` | When `CLI_TOOLS_DATA_DIR=/tmp/x` is set, `get_data_dir()` returns `Path("/tmp/x")` |
| PL-02 | `test_get_data_dir_macos_default` | On macOS (mocked `sys.platform="darwin"`), returns `~/Library/Application Support/cli-tools` |
| PL-03 | `test_get_data_dir_linux_xdg` | On Linux with `XDG_DATA_HOME` set, returns `$XDG_DATA_HOME/cli-tools` |
| PL-04 | `test_get_data_dir_linux_fallback` | On Linux without `XDG_DATA_HOME`, returns `~/.local/share/cli-tools` |
| PL-05 | `test_get_data_dir_windows_localappdata` | On Windows (mocked), returns `%LOCALAPPDATA%\cli-tools` |
| PL-06 | `test_get_db_path_appends_filename` | `get_db_path()` returns `get_data_dir() / "cli-tools.db"` |
| PL-07 | `test_get_data_dir_creates_directory` | The returned directory is created on disk when it does not yet exist |
| PL-08 | `test_get_data_dir_posix_permissions` | On POSIX, the created directory has mode `0o700` |

---

### 4.3 `tests/unit/core/common/test_metadata.py`

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| MT-01 | `test_get_metadata_returns_none_when_absent` | Returns `None` for an unknown `(tool, key)` pair |
| MT-02 | `test_set_and_get_metadata_roundtrip` | After `set_metadata(conn, "tp", "k", "v")`, `get_metadata(conn, "tp", "k")` returns `"v"` |
| MT-03 | `test_set_metadata_upserts` | Calling `set_metadata` twice with different values overwrites; returns new value |
| MT-04 | `test_metadata_namespaced_by_tool` | `set_metadata(conn, "tp", "k", "v1")` and `set_metadata(conn, "bm", "k", "v2")` are independent |
| MT-05 | `test_metadata_value_can_be_empty_string` | Storing `""` is distinct from `None` |

---

### 4.4 `tests/unit/core/common/test_exceptions.py`

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| EX-01 | `test_all_exceptions_inherit_cli_tools_error` | `AliasNotFoundError`, `AliasConflictError`, `StorageError`, `InvalidPathError` are all subclasses of `CliToolsError` |
| EX-02 | `test_migration_error_inherits_storage_error` | `MigrationError` is a subclass of `StorageError` |
| EX-03 | `test_catch_base_exception` | A `try/except CliToolsError` block catches instances of all subclasses |

---

### 4.5 `tests/unit/core/common/test_utils.py`

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| UT-01 | `test_validate_path_accepts_normal_path` | A regular absolute path string passes without raising |
| UT-02 | `test_validate_path_rejects_newline` | A path containing `\n` raises `InvalidPathError` |
| UT-03 | `test_validate_path_rejects_carriage_return` | A path containing `\r` raises `InvalidPathError` |
| UT-04 | `test_sanitize_alias_strips_whitespace` | Leading/trailing whitespace is stripped |
| UT-05 | `test_sanitize_alias_rejects_empty` | An empty string (after stripping) raises `ValueError` |
| UT-06 | `test_sanitize_alias_rejects_slash` | An alias containing `/` raises `ValueError` |

---

## 5. Unit tests — `core_lib/teleport`

### 5.1 `tests/unit/core/teleport/test_migrations.py`

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| MG-01 | `test_migrations_list_not_empty` | `MIGRATIONS` has at least one entry |
| MG-02 | `test_migrations_versions_sequential` | Versions are `[1, 2, …]` with no gaps |
| MG-03 | `test_v001_creates_tp_aliases` | After applying v001 forward, `tp_aliases` table exists |
| MG-04 | `test_v001_creates_tp_history` | After applying v001 forward, `tp_history` table exists |
| MG-05 | `test_v001_creates_index` | `idx_tp_alias_path` index exists |
| MG-06 | `test_v001_idempotent` | Applying v001 twice does not raise (uses `CREATE TABLE IF NOT EXISTS`) |

---

### 5.2 `tests/unit/core/teleport/test_models.py`

**`Alias`**

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| AL-01 | `test_alias_valid_construction` | Constructing `Alias` with valid fields succeeds |
| AL-02 | `test_alias_path_rejects_newline` | `Alias(path="foo\nbar", …)` raises `ValidationError` |
| AL-03 | `test_alias_path_rejects_carriage_return` | `Alias(path="foo\rbar", …)` raises `ValidationError` |
| AL-04 | `test_alias_as_path_returns_path_object` | `alias.as_path()` returns a `pathlib.Path` equal to `Path(alias.path)` |
| AL-05 | `test_alias_model_validate_from_dict` | `Alias.model_validate({"alias": "x", "path": "/tmp", …})` succeeds |
| AL-06 | `test_alias_visit_count_defaults_to_zero` | `Alias` created without `visit_count` has `visit_count == 0` |

**`HistoryEntry`**

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| HE-01 | `test_history_entry_valid_construction` | Constructing `HistoryEntry` with valid fields succeeds |
| HE-02 | `test_history_entry_action_values` | `action` field accepts `"jump"`, `"pin"`, `"unpin"` without error |

---

### 5.3 `tests/unit/core/teleport/test_actions.py`

All tests use a `tmp_db_path` fixture with teleport migrations applied (`run_tool_migrations(conn, "teleport", MIGRATIONS)`).

**`insert_alias` / `get_alias`**

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| AC-01 | `test_insert_and_get_alias` | Inserted alias is retrievable by name; returned `Alias` fields match |
| AC-02 | `test_get_alias_returns_none_when_absent` | `get_alias(conn, "missing")` returns `None` |
| AC-03 | `test_insert_alias_case_insensitive_unique` | Inserting `"Work"` then `"work"` raises `sqlite3.IntegrityError` |

**`update_alias`**

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| AC-04 | `test_update_alias_path` | After `update_alias`, `get_alias` returns new path |
| AC-05 | `test_update_alias_updates_updated_at` | `updated_at` is strictly after `created_at` after update |

**`delete_alias`**

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| AC-06 | `test_delete_alias_removes_row` | After `delete_alias`, `get_alias` returns `None` |
| AC-07 | `test_delete_alias_sets_history_alias_id_null` | Related `tp_history` rows have `alias_id = NULL` after delete (FK `ON DELETE SET NULL`) |

**`list_aliases`**

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| AC-08 | `test_list_aliases_empty` | Returns `[]` when no aliases exist |
| AC-09 | `test_list_aliases_ordered_by_name` | Returns aliases in case-insensitive alphabetical order |
| AC-10 | `test_list_aliases_returns_all` | All inserted aliases are returned |

**`increment_visit_count`**

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| AC-11 | `test_increment_visit_count` | After calling once, `visit_count` is 1; after calling twice, it is 2 |

**`insert_history` / `prune_history`**

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| AC-12 | `test_insert_history_row` | Inserted history row is readable with correct fields |
| AC-13 | `test_prune_history_keeps_1000_rows` | After inserting 1001 rows, exactly 1000 remain (the newest 1000) |
| AC-14 | `test_prune_history_keeps_newest` | The oldest row (lowest `id`) is the one removed |
| AC-15 | `test_prune_history_noop_below_limit` | With 500 rows, prune does nothing |

---

### 5.4 `tests/unit/core/teleport/test_service.py`

All tests use the `teleport_service` fixture (fresh `TeleportService` backed by a temp DB).

**`pin`**

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| SV-01 | `test_pin_stores_alias` | After `pin("work", path)`, `show("work")` returns an `Alias` with that path |
| SV-02 | `test_pin_resolves_path` | Stored path equals `path.resolve()` even if input is relative |
| SV-03 | `test_pin_raises_conflict_on_duplicate` | `pin("work", …)` twice raises `AliasConflictError` |
| SV-04 | `test_pin_overwrite_replaces_path` | `pin("work", new_path, overwrite=True)` updates the stored path |
| SV-05 | `test_pin_warns_nonexistent_path` | Pinning a non-existent path does not raise but emits a `WARNING` log (captured via `caplog`) |
| SV-06 | `test_pin_raises_invalid_path_on_newline` | A path string containing `\n` raises `InvalidPathError` |
| SV-07 | `test_pin_returns_alias_model` | Return value is an `Alias` instance |

**`unpin`**

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| SV-08 | `test_unpin_removes_alias` | After `unpin("work")`, `list_aliases()` returns `[]` |
| SV-09 | `test_unpin_raises_not_found` | `unpin("missing")` raises `AliasNotFoundError` |

**`resolve`**

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| SV-10 | `test_resolve_returns_path` | `resolve("work")` returns the pinned `Path` |
| SV-11 | `test_resolve_returns_none_for_unknown` | `resolve("missing")` returns `None` |
| SV-12 | `test_resolve_increments_visit_count` | After calling `resolve("work")` twice, `show("work")[0].visit_count == 2` |
| SV-13 | `test_resolve_records_jump_history` | A `tp_history` row with `action='jump'` exists after `resolve` |
| SV-14 | `test_resolve_stores_previous_path` | After `resolve("work", cwd=Path("/from"))`, `previous()` returns `Path("/from")` |
| SV-15 | `test_resolve_previous_path_updates_on_each_jump` | Second jump sets `previous_path` to the CWD of the second call |

**`previous`**

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| SV-16 | `test_previous_returns_none_initially` | `previous()` returns `None` before any jump |
| SV-17 | `test_previous_returns_last_cwd` | Returns the CWD passed to the most recent `resolve` call |

**`list_aliases`**

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| SV-18 | `test_list_aliases_empty` | Returns `[]` with no aliases pinned |
| SV-19 | `test_list_aliases_sorted` | Multiple aliases returned in alphabetical order |

**`show`**

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| SV-20 | `test_show_single_alias` | `show("work")` returns a list with one matching `Alias` |
| SV-21 | `test_show_all_aliases` | `show()` returns all aliases |
| SV-22 | `test_show_raises_not_found` | `show("missing")` raises `AliasNotFoundError` |
| SV-23 | `test_show_does_not_record_history` | `tp_history` is empty after calling `show` |

**Migration auto-run**

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| SV-24 | `test_service_init_creates_schema` | Constructing `TeleportService` on a fresh DB creates `tp_aliases` and `tp_history` tables |
| SV-25 | `test_service_init_idempotent` | Constructing `TeleportService` twice on the same DB does not raise or duplicate migration records |

---

## 6. Integration tests — `cli_layer`

All integration tests invoke `uv run tp-cli <args>` via `subprocess.run`. The `tmp_data_dir` fixture sets `CLI_TOOLS_DATA_DIR` in the subprocess environment.

Helper fixture (add to `tests/conftest.py`):

```python
import subprocess, os
from pathlib import Path

@pytest.fixture()
def run_tp(tmp_data_dir: Path):
    """Return a callable that runs tp-cli with the temp data dir and returns
    a CompletedProcess with decoded stdout/stderr."""
    def _run(*args: str, input: str | None = None) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "CLI_TOOLS_DATA_DIR": str(tmp_data_dir)}
        return subprocess.run(
            ["uv", "run", "tp-cli", *args],
            capture_output=True, text=True, env=env, input=input,
        )
    return _run
```

---

### 6.1 `tests/integration/test_cli_pin.py`

| ID | Test name | Invocation | Expected outcome |
|----|-----------|-----------|-----------------|
| CI-01 | `test_pin_current_dir` | `tp-cli -p work` | exit 0; stderr contains confirmation; `tp-cli -s work` stdout = cwd |
| CI-02 | `test_pin_explicit_path` | `tp-cli -p work /tmp` | exit 0; `tp-cli -s work` stdout = resolved `/tmp` |
| CI-03 | `test_pin_conflict` | Pin `work`, pin `work` again | exit 3; stderr contains "conflict" or "already exists" |
| CI-04 | `test_pin_overwrite` | `tp-cli -p --force work /a`, then `tp-cli -p --force work /b` | exit 0; `tp-cli -s work` stderr shows path `/b` |
| CI-05 | `test_pin_invalid_alias_slash` | `tp-cli -p "bad/alias"` | exit 5; stderr contains error |
| CI-06 | `test_pin_stdout_is_empty` | `tp-cli -p work` | stdout is empty (confirmation goes to stderr only) |

---

### 6.2 `tests/integration/test_cli_resolve.py`

| ID | Test name | Invocation | Expected outcome |
|----|-----------|-----------|-----------------|
| CI-07 | `test_resolve_known_alias` | `tp-cli work` (after pinning) | exit 0; stdout = pinned path + `\n`; stderr empty |
| CI-08 | `test_resolve_unknown_alias` | `tp-cli missing` | exit 2; stdout empty; stderr contains "not found" |
| CI-09 | `test_resolve_no_args_prints_home` | `tp-cli` | exit 0; stdout = `str(Path.home())` + `\n` |
| CI-10 | `test_resolve_increments_visit_count` | `tp-cli work` twice, then `tp-cli -s work` | stderr table shows `visit_count = 2` |
| CI-11 | `test_resolve_stdout_single_line` | `tp-cli work` | stdout has exactly one non-empty line, no trailing whitespace |

---

### 6.3 `tests/integration/test_cli_previous.py`

| ID | Test name | Invocation | Expected outcome |
|----|-----------|-----------|-----------------|
| CI-12 | `test_previous_no_history` | `tp-cli -` (no prior jump) | exit 2; stderr contains "no previous path" |
| CI-13 | `test_previous_after_jump` | Pin `work`, `tp-cli work` with CWD=/from, then `tp-cli -` | exit 0; stdout = `/from` (the CWD used during the jump) |
| CI-14 | `test_previous_stdout_single_line` | `tp-cli -` | stdout has exactly one non-empty line |

---

### 6.4 `tests/integration/test_cli_unpin.py`

| ID | Test name | Invocation | Expected outcome |
|----|-----------|-----------|-----------------|
| CI-15 | `test_unpin_existing` | Pin `work`, then `tp-cli -u work` | exit 0; `tp-cli -s work` then returns exit 2 |
| CI-16 | `test_unpin_missing` | `tp-cli -u missing` | exit 2; stderr contains "not found" |
| CI-17 | `test_unpin_stdout_is_empty` | `tp-cli -u work` | stdout is empty |

---

### 6.5 `tests/integration/test_cli_show.py`

| ID | Test name | Invocation | Expected outcome |
|----|-----------|-----------|-----------------|
| CI-18 | `test_show_all_empty` | `tp-cli -s` (no aliases) | exit 0; stderr contains empty-state message; stdout empty |
| CI-19 | `test_show_all_table` | Pin two aliases, `tp-cli -s` | exit 0; stderr contains both alias names; stdout empty |
| CI-20 | `test_show_single` | Pin `work`, `tp-cli -s work` | exit 0; stderr contains path; stdout empty |
| CI-21 | `test_show_single_missing` | `tp-cli -s missing` | exit 2; stderr contains "not found" |
| CI-22 | `test_show_stdout_always_empty` | Any `tp-cli -s …` invocation | stdout is always empty |

---

### 6.6 Exit code contract (`tests/integration/test_cli_exit_codes.py`)

| ID | Test name | Scenario | Expected exit code |
|----|-----------|---------|-------------------|
| CI-23 | `test_exit_0_on_success` | `tp-cli -p work /tmp` | 0 |
| CI-24 | `test_exit_2_alias_not_found` | `tp-cli missing` | 2 |
| CI-25 | `test_exit_3_alias_conflict` | Double-pin same alias | 3 |
| CI-26 | `test_exit_4_storage_error` | Make DB path a directory (unwritable) | 4 |
| CI-27 | `test_exit_5_invalid_path` | *(path with newline; inject via env or file)* | 5 |

---

### 6.7 stdout / stderr contract (`tests/integration/test_cli_output_contract.py`)

| ID | Test name | What it verifies |
|----|-----------|-----------------|
| CI-28 | `test_jump_writes_path_to_stdout_only` | On `tp-cli work`, the path appears only on stdout, not stderr |
| CI-29 | `test_human_output_goes_to_stderr` | Confirmation messages, tables, and errors appear only on stderr |
| CI-30 | `test_stdout_is_machine_parseable` | `tp-cli work` stdout stripped equals an absolute path (starts with `/` or drive letter) |
| CI-31 | `test_stdout_empty_on_non_jump_commands` | `tp-cli -p`, `-u`, `-s` all produce empty stdout |

---

## 7. Shell wrapper tests (`tests/shell/test_bash_wrapper.sh`)

Run on Linux CI only (`ubuntu-latest`). Each test sources the `tp.bash` snippet, overrides `tp-cli` with a stub, and asserts the shell's `$PWD` changed correctly.

| ID | Scenario | Expected shell behaviour |
|----|---------|--------------------------|
| SH-01 | `tp work` with stub printing `/tmp/work` | `$PWD == /tmp/work` after invocation |
| SH-02 | `tp -` with stub printing `/from` | `$PWD == /from` after invocation |
| SH-03 | `tp-cli` exits non-zero | `$PWD` unchanged; function returns non-zero |
| SH-04 | `tp-cli` prints empty stdout | `$PWD` unchanged; function returns 0 |
| SH-05 | Path with spaces | `cd` handles `"/path/with spaces"` without word-splitting |

---

## 8. CI test matrix

```yaml
# Conceptual — actual YAML lives in .github/workflows/ci.yml
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --group dev
      - run: uv run ruff check src tests
      - run: uv run mypy --strict src
      - run: uv run pytest -m unit
      - run: uv run pytest -m integration

  shell-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: bash tests/shell/test_bash_wrapper.sh
```

---

## 9. Test-count summary

| Layer | Count |
|-------|-------|
| `core_lib/common` — db | 15 |
| `core_lib/common` — platform | 8 |
| `core_lib/common` — metadata | 5 |
| `core_lib/common` — exceptions | 3 |
| `core_lib/common` — utils | 6 |
| `core_lib/teleport` — migrations | 6 |
| `core_lib/teleport` — models | 8 |
| `core_lib/teleport` — actions | 15 |
| `core_lib/teleport` — service | 25 |
| `cli_layer` — integration | 31 |
| Shell wrapper | 5 |
| **Total** | **127** |

---

End of test specification.
