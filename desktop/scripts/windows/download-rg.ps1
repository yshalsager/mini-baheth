Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Set-Location (Resolve-Path "$PSScriptRoot\..\..")

$binDir = "src-tauri\bin"
New-Item -ItemType Directory -Force -Path $binDir | Out-Null

if (Test-Path "$binDir\rg.exe") { exit 0 }

$rgVersion = '15.1.0'

$arch = $env:PROCESSOR_ARCHITECTURE
switch -Regex ($arch) {
  'ARM64' { $targetArch = 'aarch64-pc-windows-msvc' }
  'AMD64' { $targetArch = 'x86_64-pc-windows-msvc' }
  default { Write-Error "unsupported arch: $arch" }
}

$zip = "ripgrep-$rgVersion-$targetArch.zip"
$url = "https://github.com/BurntSushi/ripgrep/releases/download/$rgVersion/$zip"

$tmp = New-Item -ItemType Directory -Path ([System.IO.Path]::GetTempPath()) -Name ("rgdl_" + [System.Guid]::NewGuid().ToString("N"))
try {
  $zipPath = Join-Path $tmp $zip
  curl.exe -L "$url" -o "$zipPath" | Out-Null
  $extractDir = Join-Path $tmp ("ripgrep-" + $rgVersion + "-" + $targetArch)
  Expand-Archive -Path $zipPath -DestinationPath $tmp -Force
  Copy-Item -Path (Join-Path $extractDir 'rg.exe') -Destination (Join-Path $binDir 'rg.exe') -Force
}
finally {
  Remove-Item -Recurse -Force $tmp
}

Write-Output "rg installed to $binDir\rg.exe"
