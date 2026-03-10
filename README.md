# cli-tools (Teleport)

Teleport is a small CLI toolset for pinning and jumping between filesystem paths quickly and efficiently.

This repository bootstraps the project layout used by the teleport implementation.

## Features

- Pin frequently used directories to short aliases.
- Quickly jump to pinned paths.
- Intuitive directory history (jump back to the last path using `-`).
- Built with Python 3.12+, Typer, and Rich.

## Installation

### 1. Install the Python Package

You can install the package directly or use a tool like `pipx` or `pip`:

```bash
pip install .
```

This installs the `tp-cli` Python executable which handles the core logic.

### 2. Install Shell Snippets

To actually change directories in your terminal, the Python script is wrapped in a shell function (usually `tp`). You need to install the shell snippet for your specific shell.

Use the provided installation script:

```bash
# For bash or zsh:
./scripts/install-shell-snippet.sh bash >> ~/.bashrc
# Or for zsh:
./scripts/install-shell-snippet.sh zsh >> ~/.zshrc

# For fish:
./scripts/install-shell-snippet.sh fish >> ~/.config/fish/config.fish
```

Restart your shell or `source` your configuration file after running the above.

## Usage

Once installed, use the `tp` command in your terminal.

```bash
# Pin the current directory as 'work'
tp --pin work

# Pin a specific directory as 'docs'
tp --pin docs /path/to/docs

# Jump to the 'work' directory
tp work

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

The project uses `hatchling` as its build backend and requires Python 3.12+.

Run the tests (unit, integration, and shell wrapper tests) using `pytest`:

```bash
pip install -e ".[dev]"
pytest
```

Linting and type checking are handled by `ruff` and `mypy`:

```bash
ruff check .
mypy .
```