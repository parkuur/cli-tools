#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Delegate to the Python installer for safe, idempotent install/uninstall
first_arg="${1:-}"
# If the first argument looks like a flag (starts with -), treat as no shell provided
if [[ "$first_arg" == --* || "$first_arg" == -* || -z "$first_arg" ]]; then
	shell_name=""
else
	shell_name="$first_arg"
	shift || true
fi

PYTHON="${ROOT_DIR}/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
	echo "Virtualenv not found at ${ROOT_DIR}/.venv. Run 'uv sync' first."
	exit 1
fi

# Invoke the Python installer directly via the project virtualenv.
"$PYTHON" -m cli_layer.install.cli --shell "${shell_name:-bash}" "$@"

