#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$ROOT_DIR/src/cli_layer/shell_snippets/tp.bash"

failures=0

assert_eq() {
  local got="$1"
  local expected="$2"
  local msg="$3"
  if [[ "$got" != "$expected" ]]; then
    echo "FAIL: $msg (got='$got', expected='$expected')" >&2
    failures=$((failures + 1))
  fi
}

assert_status() {
  local got="$1"
  local expected="$2"
  local msg="$3"
  if [[ "$got" -ne "$expected" ]]; then
    echo "FAIL: $msg (got=$got, expected=$expected)" >&2
    failures=$((failures + 1))
  fi
}

orig_pwd="$PWD"

tp-cli() {
  if [[ "${1:-}" == "work" ]]; then
    echo "/tmp"
    return 0
  fi
  if [[ "${1:-}" == "-" ]]; then
    echo "$orig_pwd"
    return 0
  fi
  if [[ "${1:-}" == "error" ]]; then
    return 7
  fi
  if [[ "${1:-}" == "empty" ]]; then
    return 0
  fi
  if [[ "${1:-}" == "space" ]]; then
    echo "/tmp/with space"
    return 0
  fi
  return 0
}

# SH-01
cd "$orig_pwd"
tp work
assert_eq "$PWD" "/tmp" "tp work changes directory"

# SH-02
cd /tmp
tp -
assert_eq "$PWD" "$orig_pwd" "tp - changes to previous path"

# SH-03
cd "$orig_pwd"
set +e
tp error
status=$?
set -e
assert_status "$status" 7 "non-zero from tp-cli is propagated"
assert_eq "$PWD" "$orig_pwd" "PWD unchanged on non-zero tp-cli"

# SH-04
cd "$orig_pwd"
tp empty
assert_status "$?" 0 "empty stdout keeps zero exit"
assert_eq "$PWD" "$orig_pwd" "PWD unchanged on empty stdout"

# SH-05
mkdir -p "/tmp/with space"
cd "$orig_pwd"
tp space
assert_eq "$PWD" "/tmp/with space" "path with spaces handled correctly"

cd "$orig_pwd"

if [[ "$failures" -gt 0 ]]; then
  exit 1
fi

echo "All shell wrapper tests passed"
