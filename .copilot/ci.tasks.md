# Continuous Integration — Implementation Tasks

Last updated: 2026-03-10
Status: **Completed**

Reference documents:
- Spec: [ci.spec.md](ci.spec.md)
- Existing workflow: [.github/workflows/ci.yml](../.github/workflows/ci.yml)

---

## Phase 1 — Core workflow (replace existing ci.yml)

- [x] **1.1** Rewrite `.github/workflows/ci.yml` with the new structure
  - [x] Trigger on `push` to `main` and `pull_request` to `main`
  - [x] Remove the `|| true` install hack
  - [x] Remove the fake uv shim step
  - [x] Remove manual `pip install` of individual packages

- [x] **1.2** Add shared setup pattern to all jobs
  - [x] `actions/checkout@v4`
  - [x] `astral-sh/setup-uv@v4`
  - [x] `actions/setup-python@v5` with `python-version: "3.12"`
  - [x] `uv sync --group dev`

- [x] **1.3** Add `lint` job
  - [x] Runs on `ubuntu-latest`
  - [x] Runs `uv run ruff check src tests`
  - [x] Fails on any violation

- [x] **1.4** Add `type-check` job
  - [x] Runs on `ubuntu-latest`
  - [x] Runs `uv run mypy --strict src`
  - [x] Fails on any diagnostic

- [x] **1.5** Add `unit-tests` job
  - [x] Runs on `ubuntu-latest`
  - [x] Runs `uv run pytest -m unit tests/unit/ -q`
  - [x] Fails on any test failure

- [x] **1.6** Add `integration` job (Linux only for Phase 1)
  - [x] Runs on `ubuntu-latest`
  - [x] Runs `uv run pytest -m integration tests/integration/ -q`

- [x] **1.7** Add `shell-tests` job
  - [x] Runs on `ubuntu-latest`
  - [x] Runs `bash tests/shell/test_bash_wrapper.sh`

- [x] **1.8** Validate Phase 1
  - [x] Push to a branch and open a PR
  - [x] Confirm all five jobs (lint, type-check, unit-tests, integration, shell-tests) pass green

---

## Phase 2 — Cross-platform matrix

- [x] **2.1** Expand `integration` job to OS matrix
  - [x] Add `strategy.matrix.os: [ubuntu-latest, macos-latest, windows-latest]`
  - [x] Set `runs-on: ${{ matrix.os }}`

- [x] **2.2** Triage platform-specific failures
  - [x] Fix path separator issues on Windows tests
  - [x] Use cross-platform reports directory creation in workflow (replace Unix-only `mkdir -p`)
  - [x] Ensure `pytest -m integration` runs and passes on Windows

- [x] **2.3** Validate Phase 2
  - [x] All three OS runners pass green
  - [x] Verified in GitHub Actions run `22920089341`

---

## Phase 3 — Artifacts and caching

- [x] **3.1** Add JUnit XML output to test jobs
  - [x] Unit tests: `--junitxml=reports/unit.xml`
  - [x] Integration tests: `--junitxml=reports/integration.xml`

- [x] **3.2** Add coverage to unit tests job
  - [x] `--cov=src --cov-report=xml:reports/coverage.xml`
  - [x] Confirm `pytest-cov` is in dev dependencies (already present)

- [x] **3.3** Upload artifacts
  - [x] Use `actions/upload-artifact@v4` to upload `reports/` directory
  - [x] Upload from unit-tests and all integration matrix jobs

- [x] **3.4** Add uv caching
  - [x] Cache `.venv` keyed by `runner.os`, `python-version`, and hash of `uv.lock`
  - [x] Alternatively rely on `astral-sh/setup-uv`'s built-in cache support

- [x] **3.5** Validate Phase 3
  - [x] Artifacts appear in the GitHub Actions run summary
  - [x] Cached runs complete faster than uncached

---

## Phase 4 — Branch protection

- [x] **4.1** Configure branch protection rules on `main`
  - [x] Require all CI jobs to pass before merge
  - [x] Require up-to-date branches before merging
  - [x] Applied via GitHub API on 2026-03-10 for all CI checks

---

## Progress summary

| Phase | Status | Notes |
|-------|--------|-------|
| 1 — Core workflow | ✅ Completed | Workflow added and validated locally |
| 2 — Cross-platform | ✅ Completed | Matrix stabilized on Linux/macOS/Windows; run `22920089341` green |
| 3 — Artifacts + cache | ✅ Completed | Reports and caching steps added; local run verified |
| 4 — Branch protection | ✅ Completed | Required checks + strict up-to-date enabled on `main` |
