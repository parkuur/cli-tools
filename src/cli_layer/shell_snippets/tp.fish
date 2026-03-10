function tp
    set -l _out (tp-cli $argv)
    set -l _status $status
    if test $_status -ne 0
        return $_status
    end
    if test -n "$_out"
        cd -- "$_out"
    end
end
