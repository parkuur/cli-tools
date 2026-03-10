# Teleport — Implementation Task List

Last updated: 2026-03-10  
Status: **Not started**

Each step follows **red → green → refactor**. Check off tests first, then implementation subtasks, then the step gate. Do not advance to the next step until the gate is cleared.

Reference documents:
- Design: `.copilot/teleport.spec.md`
- Tests: `.copilot/teleport.tests.md`

---

## Step 1 — Bootstrap scaffold

- [ ] Create top-level directory structure (`src/core_lib/`, `src/cli_layer/`, `tests/`, `scripts/`)
- [ ] Create all empty `__init__.py` files for every package directory
- [ ] Write `pyproject.toml` with:
  - [ ] `[project]` metadata (name, version, Python 3.12 requires)
  - [ ] `[project.dependencies]`: `rich`, `typer`, `pydantic`, `portalocker`
  - [ ] `[dependency-groups] dev`: `pytest`, `mypy`, `ruff`, `pytest-cov`
  - [ ] `[build-system]` with `hatchling`
  - [ ] `[tool.pytest.ini_options]` with markers and testpaths
  - [ ] `[tool.mypy]` strict settings
  - [ ] `[tool.ruff]` lint settings
- [ ] Write `README.md` with project overview and quick-start
- [ ] Write `.gitignore`
- [ ] Run `uv sync --group dev` — lockfile created, no errors
- [ ] Run `uv run pytest` — collects 0 tests, exits 0
- [ ] Run `uv run mypy --strict src` — no errors on empty packages
- [ ] Run `uv run ruff check src tests` — no errors

**Gate**: `uv run pytest` exits 0 with 0 tests collected.

---

## Step 2 — `core_lib/common` shared infrastructure

### 2a — Write tests (red)

- [ ] `tests/conftest.py` — fixtures: `tmp_db_path`, `tmp_data_dir`, `teleport_service`, `run_tp`
- [ ] `tests/unit/core/common/test_db.py`
  - [ ] DB-01 `test_open_db_returns_connection`
  - [ ] DB-02 `test_open_db_wal_mode`
  - [ ] DB-03 `test_open_db_foreign_keys`
  - [ ] DB-04 `test_open_db_row_factory`
  - [ ] DB-05 `test_open_db_creates_file`
  - [ ] DB-06 `test_ensure_common_schema_creates_migrations_table`
  - [ ] DB-07 `test_ensure_common_schema_creates_metadata_table`
  - [ ] DB-08 `test_ensure_common_schema_idempotent`
  - [ ] DB-09 `test_run_tool_migrations_applies_pending`
  - [ ] DB-10 `test_run_tool_migrations_records_version_and_name`
  - [ ] DB-11 `test_run_tool_migrations_idempotent`
  - [ ] DB-12 `test_run_tool_migrations_partial_resume`
  - [ ] DB-13 `test_run_tool_migrations_tool_isolation`
  - [ ] DB-14 `test_run_tool_migrations_failure_rolls_back`
  - [ ] DB-15 `test_run_tool_migrations_empty_list`
- [ ] `tests/unit/core/common/test_platform.py`
  - [ ] PL-01 `test_get_data_dir_env_override`
  - [ ] PL-02 `test_get_data_dir_macos_default`
  - [ ] PL-03 `test_get_data_dir_linux_xdg`
  - [ ] PL-04 `test_get_data_dir_linux_fallback`
  - [ ] PL-05 `test_get_data_dir_windows_localappdata`
  - [ ] PL-06 `test_get_db_path_appends_filename`
  - [ ] PL-07 `test_get_data_dir_creates_directory`
  - [ ] PL-08 `test_get_data_dir_posix_permissions`
- [ ] `tests/unit/core/common/test_metadata.py`
  - [ ] MT-01 `test_get_metadata_returns_none_when_absent`
  - [ ] MT-02 `test_set_and_get_metadata_roundtrip`
  - [ ] MT-03 `test_set_metadata_upserts`
  - [ ] MT-04 `test_metadata_namespaced_by_tool`
  - [ ] MT-05 `test_metadata_value_can_be_empty_string`
- [ ] `tests/unit/core/common/test_exceptions.py`
  - [ ] EX-01 `test_all_exceptions_inherit_cli_tools_error`
  - [ ] EX-02 `test_migration_error_inherits_storage_error`
  - [ ] EX-03 `test_catch_base_exception`
- [ ] `tests/unit/core/common/test_utils.py`
  - [ ] UT-01 `test_validate_path_accepts_normal_path`
  - [ ] UT-02 `test_validate_path_rejects_newline`
  - [ ] UT-03 `test_validate_path_rejects_carriage_return`
  - [ ] UT-04 `test_sanitize_alias_strips_whitespace`
  - [ ] UT-05 `test_sanitize_alias_rejects_empty`
  - [ ] UT-06 `test_sanitize_alias_rejects_slash`
- [ ] Confirm all new tests **fail** (red) before writing any implementation

### 2b — Implement

- [ ] `src/core_lib/common/exceptions.py`
  - [ ] `CliToolsError` base class
  - [ ] `AliasNotFoundError`
  - [ ] `AliasConflictError`
  - [ ] `StorageError`
  - [ ] `MigrationError(StorageError)`
  - [ ] `InvalidPathError`
- [ ] `src/core_lib/common/db.py`
  - [ ] `Migration` frozen dataclass (`version`, `name`, `forward`)
  - [ ] `open_db(db_path: Path) -> sqlite3.Connection`
  - [ ] `_COMMON_DDL` string with `_migrations` and `metadata` DDL
  - [ ] `ensure_common_schema(conn)`
  - [ ] `_max_applied_version(conn, tool) -> int`
  - [ ] `run_tool_migrations(conn, tool, migrations)`
- [ ] `src/core_lib/common/platform.py`
  - [ ] `get_data_dir() -> Path`
  - [ ] `get_db_path() -> Path`
- [ ] `src/core_lib/common/metadata.py`
  - [ ] `get_metadata(conn, tool, key) -> str | None`
  - [ ] `set_metadata(conn, tool, key, value) -> None`
- [ ] `src/core_lib/common/types.py` — `type AliasName = str` and other shared aliases (PEP 695 `type` statement)
- [ ] `src/core_lib/common/utils.py`
  - [ ] `validate_path(path: str) -> None` — raises `InvalidPathError` on newline
  - [ ] `sanitize_alias(alias: str) -> str` — strips whitespace, raises on empty or slash

### 2c — Gate

- [ ] `uv run pytest -m unit tests/unit/core/common/` — all 37 tests green
- [ ] `uv run mypy --strict src/core_lib/common/` — no errors
- [ ] `uv run ruff check src/core_lib/common/` — no errors

---

## Step 3 — `core_lib/teleport/migrations.py`

### 3a — Write tests (red)

- [ ] `tests/unit/core/teleport/test_migrations.py`
  - [ ] MG-01 `test_migrations_list_not_empty`
  - [ ] MG-02 `test_migrations_versions_sequential`
  - [ ] MG-03 `test_v001_creates_tp_aliases`
  - [ ] MG-04 `test_v001_creates_tp_history`
  - [ ] MG-05 `test_v001_creates_index`
  - [ ] MG-06 `test_v001_idempotent`
- [ ] Confirm all new tests **fail** (red)

### 3b — Implement

- [ ] `src/core_lib/teleport/__init__.py`
- [ ] `src/core_lib/teleport/migrations.py`
  - [ ] `_v001_forward(conn)` — creates `tp_aliases`, `tp_history`, `idx_tp_alias_path`
  - [ ] `MIGRATIONS: list[Migration]` — ordered list starting with v001

### 3c — Gate

- [ ] `uv run pytest -m unit tests/unit/core/teleport/test_migrations.py` — all 6 tests green
- [ ] `uv run mypy --strict src/core_lib/teleport/migrations.py` — no errors

---

## Step 4 — `core_lib/teleport/models.py` and `actions.py`

### 4a — Write tests (red)

- [ ] `tests/unit/core/teleport/test_models.py`
  - [ ] AL-01 `test_alias_valid_construction`
  - [ ] AL-02 `test_alias_path_rejects_newline`
  - [ ] AL-03 `test_alias_path_rejects_carriage_return`
  - [ ] AL-04 `test_alias_as_path_returns_path_object`
  - [ ] AL-05 `test_alias_model_validate_from_dict`
  - [ ] AL-06 `test_alias_visit_count_defaults_to_zero`
  - [ ] HE-01 `test_history_entry_valid_construction`
  - [ ] HE-02 `test_history_entry_action_values`
- [ ] `tests/unit/core/teleport/test_actions.py`
  - [ ] AC-01 `test_insert_and_get_alias`
  - [ ] AC-02 `test_get_alias_returns_none_when_absent`
  - [ ] AC-03 `test_insert_alias_case_insensitive_unique`
  - [ ] AC-04 `test_update_alias_path`
  - [ ] AC-05 `test_update_alias_updates_updated_at`
  - [ ] AC-06 `test_delete_alias_removes_row`
  - [ ] AC-07 `test_delete_alias_sets_history_alias_id_null`
  - [ ] AC-08 `test_list_aliases_empty`
  - [ ] AC-09 `test_list_aliases_ordered_by_name`
  - [ ] AC-10 `test_list_aliases_returns_all`
  - [ ] AC-11 `test_increment_visit_count`
  - [ ] AC-12 `test_insert_history_row`
  - [ ] AC-13 `test_prune_history_keeps_1000_rows`
  - [ ] AC-14 `test_prune_history_keeps_newest`
  - [ ] AC-15 `test_prune_history_noop_below_limit`
- [ ] Confirm all new tests **fail** (red)

### 4b — Implement

- [ ] `src/core_lib/teleport/models.py`
  - [ ] `Alias(BaseModel)` with `id`, `alias`, `path`, `created_at`, `updated_at`, `visit_count`
  - [ ] `@field_validator("path")` rejecting newlines
  - [ ] `as_path() -> Path` method
  - [ ] `HistoryEntry(BaseModel)` with `id`, `alias_id`, `path`, `action`, `occurred_at`
- [ ] `src/core_lib/teleport/actions.py`
  - [ ] `get_alias(conn, alias) -> Alias | None`
  - [ ] `insert_alias(conn, alias, path) -> Alias`
  - [ ] `update_alias(conn, alias, path) -> Alias`
  - [ ] `delete_alias(conn, alias) -> None`
  - [ ] `list_aliases(conn) -> list[Alias]`
  - [ ] `increment_visit_count(conn, alias_id) -> None`
  - [ ] `insert_history(conn, alias_id, path, action) -> None`
  - [ ] `prune_history(conn, limit=1000) -> None`

### 4c — Gate

- [ ] `uv run pytest -m unit tests/unit/core/teleport/test_models.py tests/unit/core/teleport/test_actions.py` — all 23 tests green
- [ ] `uv run mypy --strict src/core_lib/teleport/models.py src/core_lib/teleport/actions.py` — no errors

---

## Step 5 — `core_lib/teleport/service.py`

### 5a — Write tests (red)

- [ ] `tests/unit/core/teleport/test_service.py`
  - [ ] SV-01 `test_pin_stores_alias`
  - [ ] SV-02 `test_pin_resolves_path`
  - [ ] SV-03 `test_pin_raises_conflict_on_duplicate`
  - [ ] SV-04 `test_pin_overwrite_replaces_path`
  - [ ] SV-05 `test_pin_warns_nonexistent_path`
  - [ ] SV-06 `test_pin_raises_invalid_path_on_newline`
  - [ ] SV-07 `test_pin_returns_alias_model`
  - [ ] SV-08 `test_unpin_removes_alias`
  - [ ] SV-09 `test_unpin_raises_not_found`
  - [ ] SV-10 `test_resolve_returns_path`
  - [ ] SV-11 `test_resolve_returns_none_for_unknown`
  - [ ] SV-12 `test_resolve_increments_visit_count`
  - [ ] SV-13 `test_resolve_records_jump_history`
  - [ ] SV-14 `test_resolve_stores_previous_path`
  - [ ] SV-15 `test_resolve_previous_path_updates_on_each_jump`
  - [ ] SV-16 `test_previous_returns_none_initially`
  - [ ] SV-17 `test_previous_returns_last_cwd`
  - [ ] SV-18 `test_list_aliases_empty`
  - [ ] SV-19 `test_list_aliases_sorted`
  - [ ] SV-20 `test_show_single_alias`
  - [ ] SV-21 `test_show_all_aliases`
  - [ ] SV-22 `test_show_raises_not_found`
  - [ ] SV-23 `test_show_does_not_record_history`
  - [ ] SV-24 `test_service_init_creates_schema`
  - [ ] SV-25 `test_service_init_idempotent`
- [ ] Confirm all new tests **fail** (red)

### 5b — Implement

- [ ] `src/core_lib/teleport/service.py`
  - [ ] `TeleportService.__init__(self, db_path: Path)` — calls `run_tool_migrations`
  - [ ] `pin(alias, path, *, overwrite=False) -> Alias`
    - [ ] Path validation via `validate_path`
    - [ ] `Path.resolve()` canonicalisation
    - [ ] Existence warning via `logging`
    - [ ] Conflict check with `overwrite` support
  - [ ] `unpin(alias) -> None` — raises `AliasNotFoundError`
  - [ ] `resolve(alias, cwd: Path) -> Path | None`
    - [ ] Increment `visit_count`
    - [ ] Insert `tp_history` row (`action='jump'`)
    - [ ] Update `metadata(tool='teleport', key='previous_path')` with `cwd`
    - [ ] Prune history to 1 000 rows
  - [ ] `list_aliases() -> list[Alias]`
  - [ ] `previous() -> Path | None`
  - [ ] `show(alias: str | None = None) -> list[Alias]`
- [ ] `src/core_lib/teleport/__init__.py` — export `TeleportService`, `Alias`, `HistoryEntry`
- [ ] `src/core_lib/logging.py` — `configure_logging(level: str) -> None`

### 5c — Gate

- [ ] `uv run pytest -m unit` — all 91 unit tests (Steps 2–5) green
- [ ] `uv run mypy --strict src/core_lib/` — no errors
- [ ] `uv run ruff check src/core_lib/` — no errors

---

## Step 6 — `cli_layer/teleport_cli.py`

### 6a — Write tests (red)

- [ ] `tests/integration/test_cli_pin.py`
  - [ ] CI-01 `test_pin_current_dir`
  - [ ] CI-02 `test_pin_explicit_path`
  - [ ] CI-03 `test_pin_conflict`
  - [ ] CI-04 `test_pin_overwrite`
  - [ ] CI-05 `test_pin_invalid_alias_slash`
  - [ ] CI-06 `test_pin_stdout_is_empty`
- [ ] `tests/integration/test_cli_resolve.py`
  - [ ] CI-07 `test_resolve_known_alias`
  - [ ] CI-08 `test_resolve_unknown_alias`
  - [ ] CI-09 `test_resolve_no_args_prints_home`
  - [ ] CI-10 `test_resolve_increments_visit_count`
  - [ ] CI-11 `test_resolve_stdout_single_line`
- [ ] `tests/integration/test_cli_previous.py`
  - [ ] CI-12 `test_previous_no_history`
  - [ ] CI-13 `test_previous_after_jump`
  - [ ] CI-14 `test_previous_stdout_single_line`
- [ ] `tests/integration/test_cli_unpin.py`
  - [ ] CI-15 `test_unpin_existing`
  - [ ] CI-16 `test_unpin_missing`
  - [ ] CI-17 `test_unpin_stdout_is_empty`
- [ ] `tests/integration/test_cli_show.py`
  - [ ] CI-18 `test_show_all_empty`
  - [ ] CI-19 `test_show_all_table`
  - [ ] CI-20 `test_show_single`
  - [ ] CI-21 `test_show_single_missing`
  - [ ] CI-22 `test_show_stdout_always_empty`
- [ ] `tests/integration/test_cli_exit_codes.py`
  - [ ] CI-23 `test_exit_0_on_success`
  - [ ] CI-24 `test_exit_2_alias_not_found`
  - [ ] CI-25 `test_exit_3_alias_conflict`
  - [ ] CI-26 `test_exit_4_storage_error`
  - [ ] CI-27 `test_exit_5_invalid_path`
- [ ] `tests/integration/test_cli_output_contract.py`
  - [ ] CI-28 `test_jump_writes_path_to_stdout_only`
  - [ ] CI-29 `test_human_output_goes_to_stderr`
  - [ ] CI-30 `test_stdout_is_machine_parseable`
  - [ ] CI-31 `test_stdout_empty_on_non_jump_commands`
- [ ] Confirm all new tests **fail** (red)

### 6b — Implement

- [ ] `src/cli_layer/__init__.py`
- [ ] `src/cli_layer/teleport_cli.py` (single module — no sub-package required)
  - [ ] `main()` entrypoint registered as `tp-cli` console script
  - [ ] Pre-process `sys.argv` to convert lone `-` to `--previous` sentinel
  - [ ] Initialise `TeleportService` with `get_db_path()`
  - [ ] Call `configure_logging()` at startup (default `WARNING`, `--verbose` for `DEBUG`)
  - [ ] Top-level `CliToolsError` catch → map to exit codes (spec §7 table)
  - [ ] `tp-cli -p <alias>` — pins `Path.cwd()`; `tp-cli -p <alias> <path>` — pins given path; confirmation to stderr; stdout empty
  - [ ] `tp-cli -u <alias>` — confirmation to stderr; stdout empty; exit 2 on not found
  - [ ] `tp-cli <alias>` — prints path to stdout; `tp-cli` (no args) — prints `Path.home()` to stdout; passes `os.getcwd()` as `cwd` to `service.resolve()`
  - [ ] `tp-cli --previous` (sentinel for `-`) — prints path to stdout; exit 2 with stderr message when no previous path exists
  - [ ] `tp-cli -s` — rich table to stderr; `tp-cli -s <alias>` — path to stderr; stdout empty; exit 2 on alias not found
- [ ] Add `[project.scripts]` entry to `pyproject.toml`: `tp-cli = "cli_layer.teleport_cli:main"`
- [ ] Run `uv sync` to register the entry point

### 6c — Gate

- [ ] `uv run pytest -m integration` — all 31 integration tests green
- [ ] `uv run pytest -m unit` — all 91 unit tests still green
- [ ] `uv run mypy --strict src/` — no errors
- [ ] `uv run ruff check src/ tests/` — no errors

---

## Step 7 — Shell snippets

### 7a — Write tests (red)

- [ ] `tests/shell/test_bash_wrapper.sh`
  - [ ] SH-01 `tp work` with stub → `$PWD` changes to target
  - [ ] SH-02 `tp -` with stub → `$PWD` changes to previous
  - [ ] SH-03 `tp-cli` exits non-zero → `$PWD` unchanged
  - [ ] SH-04 `tp-cli` prints empty stdout → `$PWD` unchanged, exit 0
  - [ ] SH-05 path with spaces → `cd` handles correctly
- [ ] Confirm all shell tests **fail** (red)

### 7b — Implement

- [ ] `src/cli_layer/shell_snippets/tp.bash`
  - [ ] Works for both bash and zsh
  - [ ] Reads stdout of `tp-cli`, runs `cd -- "${_out}"`
  - [ ] Propagates non-zero exit codes
- [ ] `src/cli_layer/shell_snippets/tp.fish`
  - [ ] `function tp` definition for fish
  - [ ] Handles empty stdout (no-op `cd`)
- [ ] `src/cli_layer/shell_snippets/tp.ps1`
  - [ ] Uses `Set-Location -LiteralPath` to handle spaces
- [ ] `src/cli_layer/shell_snippets/tp.bat`
  - [ ] Reads output of `tp-cli` via `for /f`
- [ ] `scripts/install-shell-snippet.sh`
  - [ ] Detects shell (`$SHELL`, `$0`), prints appropriate snippet to stdout

### 7c — Gate

- [ ] `bash tests/shell/test_bash_wrapper.sh` — all 5 tests pass
- [ ] Manual spot-check of fish, ps1, and bat snippets

---

## Step 8 — CI

- [ ] Create `.github/workflows/ci.yml`
  - [ ] Matrix: `ubuntu-latest`, `macos-latest`, `windows-latest`
  - [ ] Steps per job:
    - [ ] `actions/checkout@v4`
    - [ ] `astral-sh/setup-uv@v4`
    - [ ] `uv sync --group dev`
    - [ ] `uv run ruff check src tests`
    - [ ] `uv run mypy --strict src`
    - [ ] `uv run pytest -m unit`
    - [ ] `uv run pytest -m integration`
  - [ ] Separate `shell-tests` job on `ubuntu-latest` only running `bash tests/shell/test_bash_wrapper.sh`
- [ ] Verify CI passes on all three platforms (push a branch)

**Gate**: all CI jobs green on `ubuntu-latest`, `macos-latest`, `windows-latest`.

---

## Step 9 — Packaging

- [ ] Confirm `[project.scripts]` entry `tp-cli = "cli_layer.teleport_cli:main"` is correct in `pyproject.toml`
- [ ] `uv build` — wheel and sdist produced in `dist/` without errors
- [ ] Install wheel into a clean isolated environment and verify `tp-cli --help` works
- [ ] `uv run pytest` — all tests (unit + integration) still green after build
- [ ] Tag `v0.1.0` and confirm CI passes on the tag

**Gate**: wheel installs cleanly, `tp-cli --help` works, all tests green.

---

## Progress summary

| Step | Status | Tests green |
|------|--------|-------------|
| 1 — Bootstrap scaffold | ⬜ Not started | — |
| 2 — `core_lib/common` | ⬜ Not started | 0 / 37 |
| 3 — `teleport/migrations` | ⬜ Not started | 0 / 6 |
| 4 — `teleport/models` + `actions` | ⬜ Not started | 0 / 23 |
| 5 — `teleport/service` | ⬜ Not started | 0 / 25 |
| 6 — `cli_layer` | ⬜ Not started | 0 / 31 |
| 7 — Shell snippets | ⬜ Not started | 0 / 5 |
| 8 — CI | ⬜ Not started | — |
| 9 — Packaging | ⬜ Not started | — |
| **Total** | | **0 / 127** |

Status key: ⬜ Not started · 🔄 In progress · ✅ Complete
