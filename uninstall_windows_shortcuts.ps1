$ErrorActionPreference = "Stop"
$items = @(
  Join-Path ([Environment]::GetFolderPath("Desktop")) "fqsnn.lnk",
  Join-Path ([Environment]::GetFolderPath("StartMenu")) "Programs\fqsnn.lnk",
  Join-Path ([Environment]::GetFolderPath("Desktop")) "Fengqing AI.lnk",
  Join-Path ([Environment]::GetFolderPath("StartMenu")) "Programs\Fengqing AI.lnk"
)
foreach ($item in $items) {
  if (Test-Path $item) {
    Remove-Item -LiteralPath $item
  }
}
Write-Host "Removed shortcuts for fqsnn."
