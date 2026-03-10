function tp {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    $out = & "{{TP_CLI}}" @Args
    $rc = $LASTEXITCODE
    if ($rc -ne 0) { return $rc }
    if (-not [string]::IsNullOrWhiteSpace($out)) {
        Set-Location -LiteralPath $out
    }
}
