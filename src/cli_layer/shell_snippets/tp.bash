tp() {
  local _out
  _out="$(tp-cli "$@")"
  local _status=$?
  if [ $_status -ne 0 ]; then
    return $_status
  fi
  if [ -n "$_out" ]; then
    cd -- "$_out" || return $?
  fi
}
