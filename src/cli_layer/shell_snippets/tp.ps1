function tp {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    $out = & tp-cli @Args
    if ($LASTEXITCODE -ne 0) { return $LASTEXITCODE }
    if (-not [string]::IsNullOrWhiteSpace($out)) {
        Set-Location -LiteralPath $out
    }
}
