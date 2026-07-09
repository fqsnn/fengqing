$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$target = Join-Path $root "open_ai.bat"
$icon = Join-Path $env:SystemRoot "System32\SHELL32.dll"
$items = @(
  @{ Path = Join-Path ([Environment]::GetFolderPath("Desktop")) "Fengqing AI.lnk" },
  @{ Path = Join-Path ([Environment]::GetFolderPath("StartMenu")) "Programs\Fengqing AI.lnk" }
)
$shell = New-Object -ComObject WScript.Shell
foreach ($item in $items) {
  $shortcut = $shell.CreateShortcut($item.Path)
  $shortcut.TargetPath = $target
  $shortcut.WorkingDirectory = $root
  $shortcut.WindowStyle = 7
  $shortcut.IconLocation = "$icon,13"
  $shortcut.Description = "Open Fengqing native local AI"
  $shortcut.Save()
}
Write-Host "Installed shortcuts for Fengqing AI."
