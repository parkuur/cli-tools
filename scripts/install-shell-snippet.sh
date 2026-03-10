#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SNIPPETS_DIR="$ROOT_DIR/src/cli_layer/shell_snippets"

shell_name="${1:-}"
if [[ -z "$shell_name" ]]; then
  shell_name="${SHELL##*/}"
fi

case "$shell_name" in
  bash|zsh)
    cat "$SNIPPETS_DIR/tp.bash"
    ;;
  fish)
    cat "$SNIPPETS_DIR/tp.fish"
    ;;
  powershell|pwsh|ps1)
    cat "$SNIPPETS_DIR/tp.ps1"
    ;;
  cmd|bat)
    cat "$SNIPPETS_DIR/tp.bat"
    ;;
  *)
    echo "Unsupported shell: $shell_name" >&2
    exit 2
    ;;
esac
