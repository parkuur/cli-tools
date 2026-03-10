# cli-tools (Teleport)

Teleport is a small CLI toolset for pinning and jumping between filesystem paths quickly and efficiently.

This repository bootstraps the project layout used by the teleport implementation.

## Features

- Pin frequently used directories to short aliases.
- Quickly jump to pinned paths.
- Intuitive directory history (jump back to the last path using `-`).
- Easily jump to home directory using `tp`.
- Seamless cross-platform shell integration (Bash, Zsh, Fish, PowerShell, Cmd).
- State persistence utilizing a shared SQLite database (`cli-tools.db`).
- Idempotent and updatable shell snippet installation.
- Built with Python 3.12+, Typer, and Rich.

## Installation

### Prerequisites

The install scripts (`./scripts/install-shell-snippet.sh` and `./scripts/install-shell-snippet.ps1`) expect the `uv` tool to be available on your PATH. The scripts will abort with an explanatory message if `uv` is not found.

Recommended ways to make `uv` available:

- Install with `pipx` (preferred):

```bash
pipx install uv
```

- Or install to your user site-packages and ensure your user `bin` directory is on `PATH`:

```bash
python -m pip install --user uv
export PATH="$HOME/.local/bin:$PATH"
```

If your environment requires the installer to write to a different location (for example in CI or tests), you can set `CLI_TOOLS_DATA_DIR` to point to a writable directory. The install scripts honor this environment variable for data/cache placement.

### 1. Install the Python Package

You can install the package using a modern tool like `uv`, `pipx` or standard `pip`:

```bash
uv tool install .
# or
pip install .
```

This installs the `tp-cli` Python executable which handles the core logic.

### 2. Install Shell Snippets

To actually change directories in your terminal, the Python script is wrapped in a shell function (usually `tp`). You need to install the shell snippet for your specific shell.

Use the provided installation script:

```bash
# Install/update (idempotent):
./scripts/install-shell-snippet.sh bash
./scripts/install-shell-snippet.sh zsh
./scripts/install-shell-snippet.sh fish

# Dry run (no file changes):
./scripts/install-shell-snippet.sh bash --dry-run

# Uninstall from selected shell profile:
./scripts/install-shell-snippet.sh bash --uninstall

# Disable / re-enable tp marker management:
./scripts/install-shell-snippet.sh --no-tp
./scripts/install-shell-snippet.sh --tp

# Optional data directory override:
CLI_TOOLS_DATA_DIR="$HOME/.local/share/cli-tools" ./scripts/install-shell-snippet.sh bash

# Windows (PowerShell) invocation:
./scripts/install-shell-snippet.ps1 --shell powershell
./scripts/install-shell-snippet.ps1 --shell powershell --dry-run
```

Restart your shell or source your configuration file after running the above.

## Usage

Once installed, use the `tp` command in your terminal.

```bash
# Pin the current directory as 'work'
tp --pin work

# Pin a specific directory as 'docs'
tp --pin docs /path/to/docs

# Jump to the 'work' directory
tp work

# Jump to the home directory
tp

# Jump back to the previous directory
tp -

# Show all pinned aliases
tp --show

# Unpin an alias
tp --unpin docs
```

### CLI Reference

The underlying Python script `tp-cli` handles arguments as follows:

- `-p, --pin <alias> [<path>]`: Pin a path to an alias. Uses current directory if `<path>` is omitted. Add `--force` to overwrite existing aliases.
- `-u, --unpin <alias>`: Remove an alias.
- `-s, --show [<alias>]`: Display the path for a specific alias, or print a summary table of all bounded aliases if none is specified.
- `--previous` (or `-` via shell wrapper): Move to the immediately preceding path.

## Development

The project uses `hatchling` as its build backend and is managed by `uv` using PEP 735 dependency groups. It requires Python 3.12+.

Run the tests (unit, integration, and shell wrapper tests) using `pytest`:

```bash
uv sync
uv run pytest
```

Linting and type checking are handled by `ruff` and `mypy` (or `pyright` as noted in CI):

```bash
uv run ruff check .
uv run mypy .
```