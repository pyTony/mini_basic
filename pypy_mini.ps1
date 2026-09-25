# Deprecated stub: use %USERPROFILE%\bin\pypy_mini.ps1 (forwards args; -m pytest works).
& (Join-Path $env:USERPROFILE "bin\pypy_mini.ps1") @args
exit $LASTEXITCODE
