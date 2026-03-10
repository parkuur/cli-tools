# Idempotent Shell Snippet Installer — Test Specification

Last updated: 2026-03-10  
Status: **Draft**

This document defines all tests for the idempotent shell snippet installer. Tests follow TDD principles: write tests first (red), implement until green, refactor while keeping tests green.

---

## Test categories

- **MAN** — Manifest helper unit tests (`tests/unit/install/test_manifest.py`)
- **INS** — Installer integration tests (`tests/integration/install/test_installer.py`)
- **IDM** — Idempotency tests (`tests/integration/install/test_idempotency.py`)
- **FLG** — Per-tool flag tests (`tests/integration/install/test_flags.py`)

---

## Unit tests — Manifest helper (MAN-01 to MAN-15)

### MAN-01: `test_create_manifest_with_restrictive_permissions`
- Create a new manifest file via `manifest.create_manifest(path)`
- Assert file exists with mode `0o600` on POSIX
- Assert content is valid empty JSON: `{"installed": {}}`

### MAN-02: `test_read_empty_manifest`
- Given an empty manifest `{"installed": {}}`
- Call `manifest.read_manifest(path)`
- Assert returns `{"installed": {}}` dict

### MAN-03: `test_read_nonexistent_manifest_returns_default`
- Call `manifest.read_manifest(nonexistent_path)`
- Assert returns `{"installed": {}}` default structure

### MAN-04: `test_write_manifest_atomically`
- Write manifest with data
- Assert intermediate temp file not visible after write completes
- Assert final file exists with correct content

### MAN-05: `test_add_marker_to_manifest`
- Start with empty manifest
- Call `manifest.add_marker(marker_id, source, profiles, checksum, enabled)`
- Read back manifest and assert marker exists with all fields

### MAN-06: `test_update_marker_checksum`
- Given manifest with marker `teleport#tp.bash` checksum `abc123`
- Call `manifest.update_marker(marker_id, new_checksum="def456")`
- Assert manifest shows new checksum `def456`

### MAN-07: `test_remove_marker_from_manifest`
- Given manifest with 2 markers
- Call `manifest.remove_marker(marker_id)`
- Assert manifest contains 1 marker, removed marker absent

### MAN-08: `test_get_marker_returns_metadata`
- Given manifest with marker
- Call `manifest.get_marker(marker_id)`
- Assert returns dict with `source`, `profiles`, `checksum`, `enabled`, `installed_at`

### MAN-09: `test_get_nonexistent_marker_returns_none`
- Call `manifest.get_marker("missing#marker")`
- Assert returns `None`

### MAN-10: `test_compute_checksum_sha256`
- Given snippet file content
- Call `manifest.compute_checksum(file_path)`
- Assert returns 64-char hex SHA256

### MAN-11: `test_compute_checksum_identical_for_same_content`
- Compute checksum for file A
- Compute checksum for file B with identical content
- Assert checksums equal

### MAN-12: `test_manifest_handles_multiple_tools`
- Add marker `teleport#tp.bash` and marker `bookmarks#bm.bash`
- Read manifest and assert both present with distinct keys

### MAN-13: `test_enabled_flag_defaults_to_true`
- Add marker without explicit `enabled` parameter
- Assert manifest marker has `enabled: true`

### MAN-14: `test_disabled_marker_preserved_in_manifest`
- Add marker with `enabled=false`
- Read manifest and assert `enabled: false`

### MAN-15: `test_manifest_tolerates_missing_fields`
- Write manifest with marker missing `enabled` field
- Call `manifest.get_marker(marker_id)`
- Assert returns data with `enabled` defaulting to `true`

---

## Integration tests — Installer CLI (INS-01 to INS-25)

These tests run the installer script via subprocess in isolated temp home directories.

### INS-01: `test_install_creates_manifest`
- Run `install-shell-snippet.sh` in temp env
- Assert `$DATA_DIR/install_manifest.json` exists

### INS-02: `test_install_inserts_marker_block`
- Run installer for bash
- Read `~/.bashrc`
- Assert contains marker header `>>> teleport snippet: tp.bash (id: teleport#tp.bash)`
- Assert contains marker footer `<<< teleport snippet: tp.bash`
- Assert snippet content between markers

### INS-03: `test_install_creates_backup_before_edit`
- Create `~/.bashrc` with existing content
- Run installer
- Assert `$DATA_DIR/backups/teleport/bashrc.<timestamp>.bak` exists
- Assert backup contains original content

### INS-04: `test_install_records_marker_in_manifest`
- Run installer
- Read manifest
- Assert `teleport#tp.bash` key exists with correct `source`, `profiles`, `checksum`, `enabled: true`

### INS-05: `test_install_supports_zsh`
- Run installer with `--shell zsh`
- Assert `~/.zshrc` modified with marker block

### INS-06: `test_install_supports_fish`
- Run installer with `--shell fish`
- Assert `~/.config/fish/config.fish` modified

### INS-07: `test_install_fails_with_exit_2_for_unsupported_shell`
- Run installer with `--shell unsupported`
- Assert exit code 2

### INS-08: `test_dry_run_reports_without_modifying`
- Run installer with `--dry-run`
- Assert stderr contains planned actions
- Assert `~/.bashrc` not modified
- Assert manifest not created

### INS-09: `test_install_exit_0_on_success`
- Run installer
- Assert exit code 0

### INS-10: `test_install_exit_3_on_permission_failure`
- Make `$DATA_DIR` read-only
- Run installer
- Assert exit code 3 (permission failure writing manifest)

### INS-11: `test_uninstall_removes_marker_block`
- Run installer (install)
- Run installer with `--uninstall`
- Read `~/.bashrc`
- Assert marker block removed
- Assert file otherwise unchanged

### INS-12: `test_uninstall_removes_manifest_entry`
- Run installer (install)
- Run installer with `--uninstall`
- Read manifest
- Assert `teleport#tp.bash` removed from `installed` map

### INS-13: `test_uninstall_restores_backup_if_present`
- Create `~/.bashrc` with original content
- Run installer
- Run installer with `--uninstall`
- Read `~/.bashrc`
- Assert content matches original backup

### INS-14: `test_uninstall_exit_0_on_success`
- Run installer (install)
- Run installer with `--uninstall`
- Assert exit code 0

### INS-15: `test_install_handles_nonexistent_profile_safely`
- Remove `~/.bashrc` if exists
- Run installer
- Assert `~/.bashrc` created with marker block only

### INS-16: `test_install_preserves_existing_profile_content`
- Create `~/.bashrc` with custom content
- Run installer
- Read `~/.bashrc`
- Assert custom content preserved
- Assert marker block appended

### INS-17: `test_install_outputs_summary_to_stderr`
- Run installer
- Assert stderr contains summary (installed, noop, updated counts)

### INS-18: `test_install_creates_backup_directory_structure`
- Run installer
- Assert `$DATA_DIR/backups/teleport/` directory exists

### INS-19: `test_multiple_profiles_supported`
- Run installer with `--profiles ~/.bashrc,~/.bash_profile`
- Assert both files modified with marker blocks
- Assert manifest records both profiles

### INS-20: `test_installer_respects_cli_tools_data_dir_env`
- Set `CLI_TOOLS_DATA_DIR=/custom/path`
- Run installer
- Assert manifest at `/custom/path/install_manifest.json`

### INS-21: `test_marker_block_uses_correct_comment_syntax_bash`
- Run installer for bash
- Read `~/.bashrc`
- Assert marker uses `#` comment syntax

### INS-22: `test_marker_block_uses_correct_comment_syntax_fish`
- Run installer for fish
- Read config
- Assert marker uses `#` comment syntax

### INS-23: `test_installer_preserves_file_encoding`
- Create `~/.bashrc` with UTF-8 content including unicode
- Run installer
- Read `~/.bashrc`
- Assert encoding preserved, no corruption

### INS-24: `test_installer_handles_paths_with_spaces`
- Set profile path with spaces in name
- Run installer with `--profiles "~/.my profile.sh"`
- Assert file created and modified correctly

### INS-25: `test_installer_locks_manifest_during_write`
- Spawn two installer processes concurrently
- Assert both complete without manifest corruption
- Assert manifest contains valid JSON

---

## Idempotency tests (IDM-01 to IDM-10)

### IDM-01: `test_second_install_is_noop`
- Run installer (first time)
- Run installer (second time)
- Assert stderr indicates noop (no changes)
- Assert exit code 0
- Assert `~/.bashrc` unchanged from first install

### IDM-02: `test_multiple_installs_do_not_duplicate_markers`
- Run installer 5 times
- Read `~/.bashrc`
- Assert exactly 1 marker block present
- Assert no duplicate marker headers

### IDM-03: `test_install_overwrites_manually_edited_marker_block`
- Run installer
- Manually add comment inside marker block
- Run installer again
- Assert marker block replaced with canonical snippet content (manual edit discarded)
- Assert checksum in manifest matches current snippet source

### IDM-04: `test_install_after_snippet_update_replaces_block`
- Run installer
- Record manifest checksum
- Modify snippet source file (add comment)
- Run installer again
- Assert marker block content updated
- Assert new checksum in manifest differs
- Assert backup created for second install

### IDM-05: `test_install_after_snippet_update_creates_new_backup`
- Run installer
- Note backup count
- Modify snippet source
- Run installer again
- Assert backup count increased by 1

### IDM-06: `test_idempotent_across_shell_changes`
- Run installer with `--shell bash`
- Run installer with `--shell bash` again
- Assert noop
- Run installer with `--shell zsh`
- Assert zsh profile modified, bash unchanged

### IDM-07: `test_reinstall_after_uninstall`
- Run installer (install)
- Run installer with `--uninstall`
- Run installer (install again)
- Assert marker block present in profile
- Assert manifest contains marker

### IDM-08: `test_manifest_corruption_recovery`
- Run installer
- Corrupt manifest JSON (invalid syntax)
- Run installer again
- Assert installer creates new manifest
- Assert stderr warns about corruption

### IDM-09: `test_missing_backup_handled_gracefully`
- Run installer
- Delete backup file manually
- Run installer with `--uninstall`
- Assert marker removed but no backup restore attempted
- Assert exit code 0

### IDM-10: `test_checksum_mismatch_triggers_update`
- Run installer
- Manually edit manifest to change checksum to invalid value
- Run installer again
- Assert marker block replaced
- Assert manifest checksum corrected

---

## Per-tool flag tests (FLG-01 to FLG-10)

### FLG-01: `test_no_tp_flag_skips_teleport_install`
- Run installer with `--no-tp`
- Assert `~/.bashrc` not modified
- Assert manifest created but empty or teleport markers have `enabled: false`

### FLG-02: `test_no_tp_flag_records_disabled_state`
- Run installer with `--no-tp`
- Read manifest
- Assert `teleport#tp.bash` present with `enabled: false`

### FLG-03: `test_install_after_no_tp_flag_respects_previous_choice`
- Run installer with `--no-tp`
- Run installer without flags (default enable all)
- Assert teleport still disabled (respects manifest state)

### FLG-04: `test_explicit_enable_overrides_disabled_state`
- Run installer with `--no-tp` (records `enabled: false`)
- Run installer with `--tp` flag to explicitly re-enable
- Assert manifest shows `enabled: true`
- Assert marker block installed in profile

### FLG-05: `test_multiple_tool_flags_supported`
- Run installer with `--no-tp --no-bm` (assuming future bookmarks tool)
- Assert both tools disabled in manifest

### FLG-06: `test_uninstall_with_no_tp_flag_noops_for_disabled_tool`
- Run installer with `--no-tp`
- Run installer with `--uninstall --no-tp`
- Assert exit code 0 (noop, nothing to uninstall)

### FLG-07: `test_dry_run_with_no_tp_flag`
- Run installer with `--dry-run --no-tp`
- Assert stderr indicates teleport would be skipped

### FLG-08: `test_flag_pattern_consistent_across_tools`
- For each tool `<tool>`, verify `--no-<tool>` flag exists and works
- Assert pattern is `--no-tp`, `--no-bm`, etc. (lowercase, hyphen-prefixed)

### FLG-09: `test_invalid_tool_flag_fails_with_exit_1`
- Run installer with `--no-invalid-tool`
- Assert exit code 1 (usage error)

### FLG-10: `test_enabled_flag_default_true_for_new_installs`
- Run installer without any `--no-*` flags
- Read manifest
- Assert all installed markers have `enabled: true`

---

## Fixtures (`tests/conftest.py` additions)

### `isolated_home` fixture
- Create temp directory
- Set `HOME` to temp dir
- Set `CLI_TOOLS_DATA_DIR` to `<temp>/data`
- Yield temp path
- Cleanup after test

### `installer_runner` fixture
- Returns callable `run_installer(*args)` that:
  - Runs `scripts/install-shell-snippet.sh` with args
  - Uses `isolated_home` fixture
  - Returns `subprocess.CompletedProcess` with stdout/stderr/returncode

### `sample_snippet` fixture
- Creates a temp snippet file with known content
- Returns path and SHA256 checksum
- Used for testing snippet updates

---

## Test execution markers

- `@pytest.mark.unit` — all MAN-* tests
- `@pytest.mark.integration` — all INS-*, IDM-*, FLG-* tests
- `@pytest.mark.slow` — IDM-* tests (run multiple installs)

---

## CI test sequence

```sh
uv run pytest -m unit tests/unit/install/
uv run pytest -m integration tests/integration/install/
```

Expected counts:
- MAN: 15 tests
- INS: 25 tests
- IDM: 10 tests
- FLG: 10 tests
- **Total: 60 tests**

---

End of test specification.
