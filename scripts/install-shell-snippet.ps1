param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

function Command-Exists {
    param([string]$Name)
    try {
        Get-Command $Name -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Ensure-UV {
    if (Command-Exists uv) { return $true }

    Write-Error "'uv' command not found. Please install it and ensure it's on PATH."
    Write-Error "Recommended: pipx install uv or python -m pip install --user uv"
    return $false
}

if (-not (Ensure-UV)) { exit 1 }

# Ensure uv's cache doesn't try to write into a restricted HOME during installs
# Prefer CLI_TOOLS_DATA_DIR if provided by tests or environment
if ($env:CLI_TOOLS_DATA_DIR) {
    $cache = Join-Path $env:CLI_TOOLS_DATA_DIR ".cache"
    $env:XDG_CACHE_HOME = $cache
} else {
    $env:XDG_CACHE_HOME = Join-Path $env:HOME ".cache"
}

# Use 'uv run' so installer works without an active virtualenv
& uv run -- python -m cli_layer.install.cli @Args
exit $LASTEXITCODE
exit $LASTEXITCODE
