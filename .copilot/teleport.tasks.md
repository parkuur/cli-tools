# Teleport — Implementation Task List

Last updated: 2026-03-10  
Status: **Completed**

Each step follows **red → green → refactor**. Check off tests first, then implementation subtasks, then the step gate. Do not advance to the next step until the gate is cleared.

Reference documents:
- Design: `.copilot/teleport.spec.md`
- Tests: `.copilot/teleport.tests.md`

---

## Step 1 — Bootstrap scaffold


 - [x] Create top-level directory structure (`src/core_lib/`, `src/cli_layer/`, `tests/`, `scripts/`)
 - [x] Create all empty `__init__.py` files for every package directory
 - [x] Write `pyproject.toml` with:
  - [x] `[project]` metadata (name, version, Python 3.12 requires)
  - [x] `[project.dependencies]`: `rich`, `typer`, `pydantic`, `portalocker`
  - [x] `[dependency-groups] dev`: `pytest`, `mypy`, `ruff`, `pytest-cov`
  - [x] `[build-system]` with `hatchling`
  - [x] `[tool.pytest.ini_options]` with markers and testpaths
  - [x] `[tool.mypy]` strict settings
  - [x] `[tool.ruff]` lint settings
 - [x] Write `README.md` with project overview and quick-start
 - [x] Write `.gitignore`
 - [x] Run `uv sync --group dev` — lockfile created, no errors
 - [x] Run `uv run pytest` — collects 0 tests, exits 0
 - [x] Run `uv run mypy --strict src` — no errors on empty packages
 - [x] Run `uv run ruff check src tests` — no errors

**Gate**: `uv run pytest` exits 0 with 0 tests collected.

---

## Step 2 — `core_lib/common` shared infrastructure

### 2a — Write tests (red)


 - [x] `tests/conftest.py` — fixtures: `tmp_db_path`, `tmp_data_dir`, `teleport_service`, `run_tp`
 - [x] `tests/unit/core/common/test_db.py`
  - [x] DB-01 `test_open_db_returns_connection`
  - [x] DB-02 `test_open_db_wal_mode`
  - [x] DB-03 `test_open_db_foreign_keys`
  - [x] DB-04 `test_open_db_row_factory`
  - [x] DB-05 `test_open_db_creates_file`
  - [x] DB-06 `test_ensure_common_schema_creates_migrations_table`
  - [x] DB-07 `test_ensure_common_schema_creates_metadata_table`
  - [x] DB-08 `test_ensure_common_schema_idempotent`
  - [x] DB-09 `test_run_tool_migrations_applies_pending`
  - [x] DB-10 `test_run_tool_migrations_records_version_and_name`
  - [x] DB-11 `test_run_tool_migrations_idempotent`
  - [x] DB-12 `test_run_tool_migrations_partial_resume`
  - [x] DB-13 `test_run_tool_migrations_tool_isolation`
  - [x] DB-14 `test_run_tool_migrations_failure_rolls_back`
  - [x] DB-15 `test_run_tool_migrations_empty_list`
 - [x] `tests/unit/core/common/test_platform.py`
  - [x] PL-01 `test_get_data_dir_env_override`
  - [x] PL-02 `test_get_data_dir_macos_default`
  - [x] PL-03 `test_get_data_dir_linux_xdg`
  - [x] PL-04 `test_get_data_dir_linux_fallback`
  - [x] PL-05 `test_get_data_dir_windows_localappdata`
  - [x] PL-06 `test_get_db_path_appends_filename`
  - [x] PL-07 `test_get_data_dir_creates_directory`
  - [x] PL-08 `test_get_data_dir_posix_permissions`
 - [x] `tests/unit/core/common/test_metadata.py`
  - [x] MT-01 `test_get_metadata_returns_none_when_absent`
  - [x] MT-02 `test_set_and_get_metadata_roundtrip`
  - [x] MT-03 `test_set_metadata_upserts`
  - [x] MT-04 `test_metadata_namespaced_by_tool`
  - [x] MT-05 `test_metadata_value_can_be_empty_string`
 - [x] `tests/unit/core/common/test_exceptions.py`
  - [x] EX-01 `test_all_exceptions_inherit_cli_tools_error`
  - [x] EX-02 `test_migration_error_inherits_storage_error`
  - [x] EX-03 `test_catch_base_exception`
 - [x] `tests/unit/core/common/test_utils.py`
  - [x] UT-01 `test_validate_path_accepts_normal_path`
  - [x] UT-02 `test_validate_path_rejects_newline`
  - [x] UT-03 `test_validate_path_rejects_carriage_return`
  - [x] UT-04 `test_sanitize_alias_strips_whitespace`
  - [x] UT-05 `test_sanitize_alias_rejects_empty`
  - [x] UT-06 `test_sanitize_alias_rejects_slash`
 - [x] Confirm all new tests **fail** (red) before writing any implementation

### 2b — Implement


 - [x] `src/core_lib/common/exceptions.py`
  - [x] `CliToolsError` base class
  - [x] `AliasNotFoundError`
  - [x] `AliasConflictError`
  - [x] `StorageError`
  - [x] `MigrationError(StorageError)`
  - [x] `InvalidPathError`
 - [x] `src/core_lib/common/db.py`
  - [x] `Migration` frozen dataclass (`version`, `name`, `forward`)
  - [x] `open_db(db_path: Path) -> sqlite3.Connection`
  - [x] `_COMMON_DDL` string with `_migrations` and `metadata` DDL
  - [x] `ensure_common_schema(conn)`
  - [x] `_max_applied_version(conn, tool) -> int`
  - [x] `run_tool_migrations(conn, tool, migrations)`
 - [x] `src/core_lib/common/platform.py`
  - [x] `get_data_dir() -> Path`
  - [x] `get_db_path() -> Path`
 - [x] `src/core_lib/common/metadata.py`
  - [x] `get_metadata(conn, tool, key) -> str | None`
  - [x] `set_metadata(conn, tool, key, value) -> None`
 - [x] `src/core_lib/common/types.py` — `type AliasName = str` and other shared aliases (PEP 695 `type` statement)
 - [x] `src/core_lib/common/utils.py`
  - [x] `validate_path(path: str) -> None` — raises `InvalidPathError` on newline
  - [x] `sanitize_alias(alias: str) -> str` — strips whitespace, raises on empty or slash

### 2c — Gate


 - [x] `uv run pytest -m unit tests/unit/core/common/` — all 37 tests green
 - [x] `uv run mypy --strict src/core_lib/common/` — no errors
 - [x] `uv run ruff check src/core_lib/common/` — no errors

---

## Step 3 — `core_lib/teleport/migrations.py`

### 3a — Write tests (red)


 - [x] `tests/unit/core/teleport/test_migrations.py`
  - [x] MG-01 `test_migrations_list_not_empty`
  - [x] MG-02 `test_migrations_versions_sequential`
  - [x] MG-03 `test_v001_creates_tp_aliases`
  - [x] MG-04 `test_v001_creates_tp_history`
  - [x] MG-05 `test_v001_creates_index`
  - [x] MG-06 `test_v001_idempotent`
 - [x] Confirm all new tests **fail** (red)

### 3b — Implement


 - [x] `src/core_lib/teleport/__init__.py`
 - [x] `src/core_lib/teleport/migrations.py`
  - [x] `_v001_forward(conn)` — creates `tp_aliases`, `tp_history`, `idx_tp_alias_path`
  - [x] `MIGRATIONS: list[Migration]` — ordered list starting with v001

### 3c — Gate


 - [x] `uv run pytest -m unit tests/unit/core/teleport/test_migrations.py` — all 6 tests green
 - [x] `uv run mypy --strict src/core_lib/teleport/migrations.py` — no errors

---

## Step 4 — `core_lib/teleport/models.py` and `actions.py`

### 4a — Write tests (red)


 - [x] `tests/unit/core/teleport/test_models.py`
  - [x] AL-01 `test_alias_valid_construction`
  - [x] AL-02 `test_alias_path_rejects_newline`
  - [x] AL-03 `test_alias_path_rejects_carriage_return`
  - [x] AL-04 `test_alias_as_path_returns_path_object`
  - [x] AL-05 `test_alias_model_validate_from_dict`
  - [x] AL-06 `test_alias_visit_count_defaults_to_zero`
  - [x] HE-01 `test_history_entry_valid_construction`
  - [x] HE-02 `test_history_entry_action_values`
 - [x] `tests/unit/core/teleport/test_actions.py`
  - [x] AC-01 `test_insert_and_get_alias`
  - [x] AC-02 `test_get_alias_returns_none_when_absent`
  - [x] AC-03 `test_insert_alias_case_insensitive_unique`
  - [x] AC-04 `test_update_alias_path`
  - [x] AC-05 `test_update_alias_updates_updated_at`
  - [x] AC-06 `test_delete_alias_removes_row`
  - [x] AC-07 `test_delete_alias_sets_history_alias_id_null`
  - [x] AC-08 `test_list_aliases_empty`
  - [x] AC-09 `test_list_aliases_ordered_by_name`
  - [x] AC-10 `test_list_aliases_returns_all`
  - [x] AC-11 `test_increment_visit_count`
  - [x] AC-12 `test_insert_history_row`
  - [x] AC-13 `test_prune_history_keeps_1000_rows`
  - [x] AC-14 `test_prune_history_keeps_newest`
  - [x] AC-15 `test_prune_history_noop_below_limit`
 - [x] Confirm all new tests **fail** (red)

### 4b — Implement


 - [x] `src/core_lib/teleport/models.py`
  - [x] `Alias(BaseModel)` with `id`, `alias`, `path`, `created_at`, `updated_at`, `visit_count`
  - [x] `@field_validator("path")` rejecting newlines
  - [x] `as_path() -> Path` method
  - [x] `HistoryEntry(BaseModel)` with `id`, `alias_id`, `path`, `action`, `occurred_at`
 - [x] `src/core_lib/teleport/actions.py`
  - [x] `get_alias(conn, alias) -> Alias | None`
  - [x] `insert_alias(conn, alias, path) -> Alias`
  - [x] `update_alias(conn, alias, path) -> Alias`
  - [x] `delete_alias(conn, alias) -> None`
  - [x] `list_aliases(conn) -> list[Alias]`
  - [x] `increment_visit_count(conn, alias_id) -> None`
  - [x] `insert_history(conn, alias_id, path, action) -> None`
  - [x] `prune_history(conn, limit=1000) -> None`

### 4c — Gate


 - [x] `uv run pytest -m unit tests/unit/core/teleport/test_models.py tests/unit/core/teleport/test_actions.py` — all 23 tests green
 - [x] `uv run mypy --strict src/core_lib/teleport/models.py src/core_lib/teleport/actions.py` — no errors

---

## Step 5 — `core_lib/teleport/service.py`

### 5a — Write tests (red)


 - [x] `tests/unit/core/teleport/test_service.py`
  - [x] SV-01 `test_pin_stores_alias`
  - [x] SV-02 `test_pin_resolves_path`
  - [x] SV-03 `test_pin_raises_conflict_on_duplicate`
  - [x] SV-04 `test_pin_overwrite_replaces_path`
  - [x] SV-05 `test_pin_warns_nonexistent_path`
  - [x] SV-06 `test_pin_raises_invalid_path_on_newline`
  - [x] SV-07 `test_pin_returns_alias_model`
  - [x] SV-08 `test_unpin_removes_alias`
  - [x] SV-09 `test_unpin_raises_not_found`
  - [x] SV-10 `test_resolve_returns_path`
  - [x] SV-11 `test_resolve_returns_none_for_unknown`
  - [x] SV-12 `test_resolve_increments_visit_count`
  - [x] SV-13 `test_resolve_records_jump_history`
  - [x] SV-14 `test_resolve_stores_previous_path`
  - [x] SV-15 `test_resolve_previous_path_updates_on_each_jump`
  - [x] SV-16 `test_previous_returns_none_initially`
  - [x] SV-17 `test_previous_returns_last_cwd`
  - [x] SV-18 `test_list_aliases_empty`
  - [x] SV-19 `test_list_aliases_sorted`
  - [x] SV-20 `test_show_single_alias`
  - [x] SV-21 `test_show_all_aliases`
  - [x] SV-22 `test_show_raises_not_found`
  - [x] SV-23 `test_show_does_not_record_history`
  - [x] SV-24 `test_service_init_creates_schema`
  - [x] SV-25 `test_service_init_idempotent`
 - [x] Confirm all new tests **fail** (red)

### 5b — Implement


 - [x] `src/core_lib/teleport/service.py`
  - [x] `TeleportService.__init__(self, db_path: Path)` — calls `run_tool_migrations`
  - [x] `pin(alias, path, *, overwrite=False) -> Alias`
    - [x] Path validation via `validate_path`
    - [x] `Path.resolve()` canonicalisation
    - [x] Existence warning via `logging`
    - [x] Conflict check with `overwrite` support
  - [x] `unpin(alias) -> None` — raises `AliasNotFoundError`
  - [x] `resolve(alias, cwd: Path) -> Path | None`
    - [x] Increment `visit_count`
    - [x] Insert `tp_history` row (`action='jump'`)
    - [x] Update `metadata(tool='teleport', key='previous_path')` with `cwd`
    - [x] Prune history to 1 000 rows
  - [x] `list_aliases() -> list[Alias]`
  - [x] `previous() -> Path | None`
  - [x] `show(alias: str | None = None) -> list[Alias]`
 - [x] `src/core_lib/teleport/__init__.py` — export `TeleportService`, `Alias`, `HistoryEntry`
 - [x] `src/core_lib/logging.py` — `configure_logging(level: str) -> None`

### 5c — Gate


 - [x] `uv run pytest -m unit` — all 91 unit tests (Steps 2–5) green
 - [x] `uv run mypy --strict src/core_lib/` — no errors
 - [x] `uv run ruff check src/core_lib/` — no errors

---

## Step 6 — `cli_layer/teleport_cli.py`

### 6a — Write tests (red)


 - [x] `tests/integration/test_cli_pin.py`
  - [x] CI-01 `test_pin_current_dir`
  - [x] CI-02 `test_pin_explicit_path`
  - [x] CI-03 `test_pin_conflict`
  - [x] CI-04 `test_pin_overwrite`
  - [x] CI-05 `test_pin_invalid_alias_slash`
  - [x] CI-06 `test_pin_stdout_is_empty`
 - [x] `tests/integration/test_cli_resolve.py`
  - [x] CI-07 `test_resolve_known_alias`
  - [x] CI-08 `test_resolve_unknown_alias`
  - [x] CI-09 `test_resolve_no_args_prints_home`
  - [x] CI-10 `test_resolve_increments_visit_count`
  - [x] CI-11 `test_resolve_stdout_single_line`
 - [x] `tests/integration/test_cli_previous.py`
  - [x] CI-12 `test_previous_no_history`
  - [x] CI-13 `test_previous_after_jump`
  - [x] CI-14 `test_previous_stdout_single_line`
 - [x] `tests/integration/test_cli_unpin.py`
  - [x] CI-15 `test_unpin_existing`
  - [x] CI-16 `test_unpin_missing`
  - [x] CI-17 `test_unpin_stdout_is_empty`
 - [x] `tests/integration/test_cli_show.py`
  - [x] CI-18 `test_show_all_empty`
  - [x] CI-19 `test_show_all_table`
  - [x] CI-20 `test_show_single`
  - [x] CI-21 `test_show_single_missing`
  - [x] CI-22 `test_show_stdout_always_empty`
 - [x] `tests/integration/test_cli_exit_codes.py`
  - [x] CI-23 `test_exit_0_on_success`
  - [x] CI-24 `test_exit_2_alias_not_found`
  - [x] CI-25 `test_exit_3_alias_conflict`
  - [x] CI-26 `test_exit_4_storage_error`
  - [x] CI-27 `test_exit_5_invalid_path`
 - [x] `tests/integration/test_cli_output_contract.py`
  - [x] CI-28 `test_jump_writes_path_to_stdout_only`
  - [x] CI-29 `test_human_output_goes_to_stderr`
  - [x] CI-30 `test_stdout_is_machine_parseable`
  - [x] CI-31 `test_stdout_empty_on_non_jump_commands`
 - [x] Confirm all new tests **fail** (red)

### 6b — Implement


 - [x] `src/cli_layer/__init__.py`
 - [x] `src/cli_layer/teleport_cli.py` (single module — no sub-package required)
  - [x] `main()` entrypoint registered as `tp-cli` console script
  - [x] Pre-process `sys.argv` to convert lone `-` to `--previous` sentinel
  - [x] Initialise `TeleportService` with `get_db_path()`
  - [x] Call `configure_logging()` at startup (default `WARNING`, `--verbose` for `DEBUG`)
  - [x] Top-level `CliToolsError` catch → map to exit codes (spec §7 table)
  - [x] `tp-cli -p <alias>` — pins `Path.cwd()`; `tp-cli -p <alias> <path>` — pins given path; confirmation to stderr; stdout empty
  - [x] `tp-cli -u <alias>` — confirmation to stderr; stdout empty; exit 2 on not found
  - [x] `tp-cli <alias>` — prints path to stdout; `tp-cli` (no args) — prints `Path.home()` to stdout; passes `os.getcwd()` as `cwd` to `service.resolve()`
  - [x] `tp-cli --previous` (sentinel for `-`) — prints path to stdout; exit 2 with stderr message when no previous path exists
  - [x] `tp-cli -s` — rich table to stderr; `tp-cli -s <alias>` — path to stderr; stdout empty; exit 2 on alias not found
 - [x] Add `[project.scripts]` entry to `pyproject.toml`: `tp-cli = "cli_layer.teleport_cli:main"`
 - [x] Run `uv sync` to register the entry point

### 6c — Gate


 - [x] `uv run pytest -m integration` — all 31 integration tests green
 - [x] `uv run pytest -m unit` — all 91 unit tests still green
 - [x] `uv run mypy --strict src/` — no errors
 - [x] `uv run ruff check src/ tests/` — no errors

---

## Step 7 — Shell snippets

### 7a — Write tests (red)


 - [x] `tests/shell/test_bash_wrapper.sh`
  - [x] SH-01 `tp work` with stub → `$PWD` changes to target
  - [x] SH-02 `tp -` with stub → `$PWD` changes to previous
  - [x] SH-03 `tp-cli` exits non-zero → `$PWD` unchanged
  - [x] SH-04 `tp-cli` prints empty stdout → `$PWD` unchanged, exit 0
  - [x] SH-05 path with spaces → `cd` handles correctly
 - [x] Confirm all shell tests **fail** (red)

### 7b — Implement


 - [x] `src/cli_layer/shell_snippets/tp.bash`
  - [x] Works for both bash and zsh
  - [x] Reads stdout of `tp-cli`, runs `cd -- "${_out}"`
  - [x] Propagates non-zero exit codes
 - [x] `src/cli_layer/shell_snippets/tp.fish`
  - [x] `function tp` definition for fish
  - [x] Handles empty stdout (no-op `cd`)
 - [x] `src/cli_layer/shell_snippets/tp.ps1`
  - [x] Uses `Set-Location -LiteralPath` to handle spaces
 - [x] `src/cli_layer/shell_snippets/tp.bat`
  - [x] Reads output of `tp-cli` via `for /f`
 - [x] `scripts/install-shell-snippet.sh`
  - [x] Detects shell (`$SHELL`, `$0`), prints appropriate snippet to stdout

### 7c — Gate


 - [x] `bash tests/shell/test_bash_wrapper.sh` — all 5 tests pass
 - [x] Manual spot-check of fish, ps1, and bat snippets

---

## Step 8 — CI

- [x] Create `.github/workflows/ci.yml`
  - [x] Matrix: `ubuntu-latest`, `macos-latest`, `windows-latest`
  - [x] Steps per job:
    - [x] `actions/checkout@v4`
    - [x] `astral-sh/setup-uv@v4`
    - [x] `uv sync --group dev`
    - [x] `uv run ruff check src tests`
    - [x] `uv run mypy --strict src`
    - [x] `uv run pytest -m unit`
    - [x] `uv run pytest -m integration`
  - [x] Separate `shell-tests` job on `ubuntu-latest` only running `bash tests/shell/test_bash_wrapper.sh`
- [x] Verify CI passes on all three platforms (push a branch)

**Gate**: all CI jobs green on `ubuntu-latest`, `macos-latest`, `windows-latest`. ✅

---

## Step 9 — Packaging

- [x] Confirm `[project.scripts]` entry `tp-cli = "cli_layer.teleport_cli:main"` is correct in `pyproject.toml`
- [x] `uv build` — wheel and sdist produced in `dist/` without errors
- [x] Install wheel into a clean isolated environment and verify `tp-cli --help` works
- [x] `uv run pytest` — all tests (unit + integration) still green after build
- [x] Tag `v0.1.0` and confirm CI passes on the tag

**Gate**: wheel installs cleanly, `tp-cli --help` works, all tests green. ✅

---

## Progress summary

| Step | Status | Tests green |
|------|--------|-------------|
| 1 — Bootstrap scaffold | ✅ Complete | — |
| 2 — `core_lib/common` | ✅ Complete | 37 / 37 |
| 3 — `teleport/migrations` | ✅ Complete | 6 / 6 |
| 4 — `teleport/models` + `actions` | ✅ Complete | 23 / 23 |
| 5 — `teleport/service` | ✅ Complete | 25 / 25 |
| 6 — `cli_layer` | ✅ Complete | 31 / 31 |
| 7 — Shell snippets | ✅ Complete | 5 / 5 |
| 8 — CI | ✅ Complete | — |
| 9 — Packaging | ✅ Complete | — |
| **Total** | | **127 / 127** |

Status key: ⬜ Not started · 🔄 In progress · ✅ Complete
