# Idempotent Shell Snippet Installer — Implementation Steps

Last updated: 2026-03-10  
Status: **Draft**

This document defines TDD implementation steps for the idempotent shell snippet installer. Each step follows red-green-refactor: write tests first, implement minimal code to pass, refactor while keeping tests green.

---

Idempotent Shell Snippet Installer — Implementation Checklist

Last updated: 2026-03-10
Status: **Draft**

This file converts the step-by-step TDD plan into a compact checklist you can work through. Each major Step (1–15) includes four actionable checkboxes: write tests, implement, verify, refactor. Check items as you complete them.

---

## Step 1 — Manifest helper foundation
- [ ] 1.1 Write tests: `MAN-01`..`MAN-04` (create/read/write manifest, atomic write, permissions)
- [ ] 1.2 Implement: `src/cli_layer/install/manifest.py` with `create_manifest`, `read_manifest`, `write_manifest` (atomic temp+rename)
- [ ] 1.3 Verify: run matching unit tests
- [ ] 1.4 Refactor: extract constants, add docstrings, handle Windows permission fallback

## Step 2 — Marker CRUD operations
- [ ] 2.1 Write tests: `MAN-05`..`MAN-09`, `MAN-13`..`MAN-14` (add/update/remove/get marker, enabled flag)
- [ ] 2.2 Implement: `add_marker`, `update_marker`, `remove_marker`, `get_marker` in `manifest.py`
- [ ] 2.3 Verify: run unit tests for marker CRUD
- [ ] 2.4 Refactor: add `with_manifest_lock`, consolidate read-modify-write, add TypedDict

## Step 3 — Checksum computation
- [ ] 3.1 Write tests: `MAN-10`, `MAN-11` (SHA256 checksum correctness)
- [ ] 3.2 Implement: `compute_checksum(file_path: Path) -> str` in `manifest.py`
- [ ] 3.3 Verify: run checksum unit tests
- [ ] 3.4 Refactor: ensure UTF-8 handling and robust missing-file errors

## Step 4 — Marker block detection and insertion
- [ ] 4.1 Write tests: `INS-02`, `INS-15`, `INS-16`, `INS-21`, `INS-22`
- [ ] 4.2 Implement: `src/cli_layer/install/profile.py` with `detect_marker`, `insert_marker`, `replace_marker`, `remove_marker`
- [ ] 4.3 Verify: run integration tests for marker handling
- [ ] 4.4 Refactor: extract regex constants, support comment syntaxes, add atomic file edit wrapper

## Step 5 — Backup creation
- [ ] 5.1 Write tests: `INS-03`, `INS-18` (backup created and directory structure)
- [ ] 5.2 Implement: `create_backup(profile_path, backup_dir, tool_name)` and ensure backup dir mode `0o700`
- [ ] 5.3 Verify: run backup-related tests
- [ ] 5.4 Refactor: use `shutil.copy2`, add backup rotation, record backups in manifest

## Step 6 — Installer CLI skeleton
- [ ] 6.1 Write tests: `INS-01`, `INS-05`, `INS-06`, `INS-07`, `INS-09`
- [ ] 6.2 Implement: `scripts/install-shell-snippet.sh` CLI parsing and shell→profile mapping (bash, zsh, fish, PowerShell, cmd via AutoRun registry)
- [ ] 6.3 Verify: run relevant integration tests
- [ ] 6.4 Refactor: extract shell detection, add help, use `CLI_TOOLS_DATA_DIR` env var

## Step 7 — Install flow
- [ ] 7.1 Write tests: `INS-04`, `INS-17`, `INS-19`, `INS-20`, `IDM-01`, `IDM-02`
- [ ] 7.2 Implement: full install/update/noop flow (compute checksum, backup, insert/replace marker, update manifest)
- [ ] 7.3 Verify: run install-related integration/idempotency tests
- [ ] 7.4 Refactor: separate install/update logic, add summary reporting, lock manifest

## Step 8 — Uninstall flow
- [ ] 8.1 Write tests: `INS-11`..`INS-14`, `IDM-09`
- [ ] 8.2 Implement: uninstall logic, optional `--restore-backup` flag, remove manifest entries
- [ ] 8.3 Verify: run uninstall tests
- [ ] 8.4 Refactor: preserve backups, handle missing profiles gracefully

## Step 9 — Per-tool disable flags
- [ ] 9.1 Write tests: `FLG-01`..`FLG-03`, `FLG-10`
- [ ] 9.2 Implement: parse `--no-<tool>` flags; record `enabled: false` in manifest; support `--<tool>` to re-enable
- [ ] 9.3 Verify: run flag tests
- [ ] 9.4 Refactor: add tool name mapping, validation, update help text

## Step 10 — Dry-run mode
- [ ] 10.1 Write tests: `INS-08`, `FLG-07`
- [ ] 10.2 Implement: `--dry-run` executes detection and prints planned actions without modifying files
- [ ] 10.3 Verify: run dry-run tests
- [ ] 10.4 Refactor: extract action reporting, add optional color-coded output

## Step 11 — Idempotency and update detection
- [ ] 11.1 Write tests: `IDM-03`, `IDM-04`, `IDM-05`, `IDM-10`
- [ ] 11.2 Implement: checksum comparison and update flow; always replace marker content with canonical snippet
- [ ] 11.3 Verify: run idempotency tests
- [ ] 11.4 Refactor: add verbose logging for checksum changes

## Step 12 — Concurrency safety
- [ ] 12.1 Write tests: `INS-25`, `MAN-15`
- [ ] 12.2 Implement: `with_manifest_lock(manifest_path)` using `fcntl.flock` on POSIX; use atomic rename semantics on Windows
- [ ] 12.3 Verify: run concurrency test(s)
- [ ] 12.4 Refactor: add lock timeouts and graceful failure handling

## Step 13 — Edge cases and robustness
- [ ] 13.1 Write tests: `IDM-06`..`IDM-08`, `INS-23`, `INS-24`
- [ ] 13.2 Implement: corrupted-manifest recovery, missing snippet error path (exit 4), UTF-8 safe edits, path quoting
- [ ] 13.3 Verify: run edge-case tests
- [ ] 13.4 Refactor: centralize error messages and recovery hints

## Step 14 — Integration tests for remaining flags
- [ ] 14.1 Write tests: `FLG-04`..`FLG-09`
- [ ] 14.2 Implement: `--tp` to re-enable, support multiple `--no-*` flags, validate tool names
- [ ] 14.3 Verify: run flag integration tests
- [ ] 14.4 Refactor: document flag examples in help text

## Step 15 — Final integration and cleanup
- [ ] 15.1 Run full test suite:
  ```sh
  uv run pytest -m unit tests/unit/install/
  uv run pytest -m integration tests/integration/install/
  ```
- [ ] 15.2 Refactor: consolidate duplicate code, add type hints, run `ruff` and `mypy`
- [ ] 15.3 Update documentation: README, usage examples (`--no-tp`, `--dry-run`, `--tp`), document `CLI_TOOLS_DATA_DIR`

---

End of checklist.
Run: `uv run pytest tests/integration/install/test_installer.py -k "INS-02 or INS-15 or INS-16 or INS-21 or INS-22"`
