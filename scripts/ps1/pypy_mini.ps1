# Tracked copy of ~/bin/pypy_mini.ps1 (install/dev_install copy it to %USERPROFILE%\bin).
# See that file for behaviour: forwards args; `pypy_mini -m pytest ...` runs pytest under PyPy.
$ErrorActionPreference = "Stop"

$project = $env:MINIBASIC_DIR
if (-not $project) {
  $project = [Environment]::GetEnvironmentVariable("MINIBASIC_DIR", "User")
}
if (-not $project -or -not (Test-Path -LiteralPath $project)) {
  Write-Error "MINIBASIC_DIR not set or missing."
  exit 1
}

function Resolve-MiniBasicPypy {
  foreach ($cand in @(
      $env:MINIBASIC_PYPY,
      $env:PYPY,
      (Join-Path $env:USERPROFILE "pypy3.11-v7.3.23-win64\pypy.exe")
    )) {
    if ($cand -and (Test-Path -LiteralPath $cand -PathType Leaf)) {
      return (Resolve-Path -LiteralPath $cand).Path
    }
  }
  foreach ($name in @("pypy", "pypy3", "pypy.exe")) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) { return $cmd.Source }
  }
  Write-Error "PyPy not found. Set MINIBASIC_PYPY to pypy.exe, or install pypy on PATH."
  exit 1
}

$pypy = Resolve-MiniBasicPypy
$orig = Get-Location
$pass = @($args)

$passthroughModule = ($pass.Count -gt 0 -and [string]$pass[0] -eq "-m")

if (-not $passthroughModule) {
  for ($i = 0; $i -lt $pass.Count; $i++) {
    if (-not [string]$pass[$i]) { continue }
    if (-not $pass[$i].ToString().StartsWith("-")) {
      $cand = $pass[$i].ToString()
      $fromUser = Join-Path $orig.Path $cand
      if (Test-Path -LiteralPath $fromUser -PathType Leaf) {
        $pass[$i] = (Resolve-Path -LiteralPath $fromUser).Path
      } else {
        $fromProj = Join-Path $project $cand
        if (Test-Path -LiteralPath $fromProj -PathType Leaf) {
          $pass[$i] = (Resolve-Path -LiteralPath $fromProj).Path
        }
      }
      break
    }
  }
}

$env:PYTHONPATH = "$project;$($env:PYTHONPATH)"

$pipeLines = [System.Collections.Generic.List[string]]::new()
if ($MyInvocation.ExpectingInput) {
  $input | ForEach-Object { [void]$pipeLines.Add([string]$_) }
}

Push-Location $project
try {
  if ($passthroughModule) {
    if ($pipeLines.Count -gt 0) {
      $pipeLines | & $pypy @pass
    } else {
      & $pypy @pass
    }
  } else {
    if ($pipeLines.Count -gt 0) {
      $pipeLines | & $pypy -m mini_basic @pass
    } else {
      & $pypy -m mini_basic @pass
    }
  }
  exit $LASTEXITCODE
} finally {
  Pop-Location
}
