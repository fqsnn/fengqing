param(
  [string]$Message = "Update clean release"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Invoke-Checked {
  param([string]$Tool, [string[]]$ToolArgs)
  & $Tool @ToolArgs
  if ($LASTEXITCODE -ne 0) {
    throw "$Tool failed with exit code $LASTEXITCODE"
  }
}

function Find-Python {
  $candidates = @(
    (Join-Path $Root ".venv\Scripts\python.exe"),
    (Join-Path $Root "backend\.venv\Scripts\python.exe")
  )
  foreach ($candidate in $candidates) {
    if (Test-Path -LiteralPath $candidate) {
      return $candidate
    }
  }
  return "python"
}

function Test-Code {
  $python = Find-Python
  Push-Location (Join-Path $Root "backend")
  try {
    Invoke-Checked -Tool $python -ToolArgs @("tools\quality_gate.py")
    $compile = @'
from pathlib import Path
import py_compile
files = list(Path("app").rglob("*.pyw"))
files += list(Path("tools").rglob("*.py"))
files += list(Path("../desktop").rglob("*.pyw"))
for path in files:
    py_compile.compile(str(path), doraise=True)
print("compiled", len(files))
'@
    $compile | & $python -
    if ($LASTEXITCODE -ne 0) {
      throw "python compile check failed"
    }
  } finally {
    Pop-Location
  }
}

function New-PublishTree {
  $publishIndex = Join-Path $Root ".git\index.publish"
  if (Test-Path -LiteralPath $publishIndex) {
    Remove-Item -LiteralPath $publishIndex -Force
  }
  $env:GIT_INDEX_FILE = $publishIndex
  try {
    $paths = @(
      ".gitignore", "README.md", "LICENSE",
      "fqsnn.bat", "publish_to_github.bat", "publish_to_github.ps1",
      "install_windows_shortcuts.bat", "install_windows_shortcuts.ps1",
      "uninstall_windows_shortcuts.ps1", "backend/.env.example",
      "backend/requirements.txt", "backend/start.bat", "backend/config.yaml",
      "backend/app", "backend/tools", "backend/context", "desktop"
    )
    Invoke-Checked -Tool "git" -ToolArgs (@("add", "--") + $paths)
    return (& git write-tree).Trim()
  } finally {
    Remove-Item Env:GIT_INDEX_FILE -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $publishIndex) {
      Remove-Item -LiteralPath $publishIndex -Force
    }
  }
}

function Assert-CleanBranch {
  $privateName = [string]([char]0x8BB8) + [string]([char]0x53EF) + [string]([char]0x5FC3)
  $filePattern = "workspace|(^|/)\.env$|venv|event_logs|\.exe$|\.dll$|\.pak$|\.bin$|\.dat$|resources/|locales/|LICENSE1|__pycache__|\.pyc$|front" + "end|index\.html|app\.js|styles\.css"
  $badFiles = & git ls-tree -r --name-only publish-clean | Select-String -Pattern $filePattern
  if ($badFiles) {
    throw "blocked publish files: $($badFiles -join '; ')"
  }

  $patterns = @(
    "s" + "k-proj",
    "s" + "k-[A-Za-z0-9]",
    "OPENAI_API_KEY=.*[A-Za-z0-9_-]{20,}",
    "codex" + "\\\\Workspace",
    $privateName,
    "open" + "_browser",
    "start" + "_desktop",
    "ms" + "edge",
    "frontend" + "/index",
    "File" + "Response",
    "Static" + "Files"
  )
  $matches = & git grep -n -I -E ($patterns -join "|") publish-clean -- .
  if ($LASTEXITCODE -eq 0) {
    throw "blocked publish content: $($matches -join '; ')"
  }
  if ($LASTEXITCODE -gt 1) {
    throw "content scan failed"
  }
}

Test-Code
Invoke-Checked -Tool "git" -ToolArgs @("fetch", "origin", "main")
$tree = New-PublishTree
$parent = (& git rev-parse --verify origin/main).Trim()
$oldTree = (& git rev-parse "$parent^{tree}").Trim()
if ($tree -eq $oldTree) {
  Write-Output "No publishable changes."
  exit 0
}

$commit = (& git commit-tree $tree -p $parent -m $Message).Trim()
Invoke-Checked -Tool "git" -ToolArgs @("branch", "-f", "publish-clean", $commit)
Assert-CleanBranch
Invoke-Checked -Tool "git" -ToolArgs @("push", "origin", "publish-clean:main")
Write-Output "Published $commit"
