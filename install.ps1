# ==============================================================================
# agent-harness Windows PowerShell Installer
# Universal AI Agent Anti-Drift Framework & Codebase Memory
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host "
   ___                    __     __ __                                 
  / _ | ___ ____ ___  __ / /_   / // /___ _ ____ ___  ___  ___ ___    
 / __ |/ _ `/ -_) _ \/ // / -_) / _  // _ `// __// _ \/ -_)(_-<(_-<   
/_/ |_|\_, /\__/_//_/\_,_/\__/ /_//_/ \_,_//_/  /_//_/\__//___/___/   
      /___/                                                            
       Universal Anti-Drift & Codebase Memory Harness for AI Agents
" -ForegroundColor Cyan

$InstallDir = "$HOME\.local\bin"
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

# 1. Detect Architecture
$Arch = $env:PROCESSOR_ARCHITECTURE
$CbmZip = "codebase-memory-mcp-windows-amd64.zip"
if ($Arch -eq "ARM64") {
    $CbmZip = "codebase-memory-mcp-windows-arm64.zip"
}

Write-Host "🔍 Detected Windows Architecture: $Arch" -ForegroundColor Yellow

# 2. Install / upgrade codebase-memory-mcp.exe to the latest official release
$CbmExe = "$InstallDir\codebase-memory-mcp.exe"
$CbmUpgraded = $null
$LatestTag = $null
try {
    $LatestTag = (Invoke-RestMethod -Uri "https://api.github.com/repos/DeusData/codebase-memory-mcp/releases/latest" -UseBasicParsing).tag_name
} catch { }
$InstalledTag = $null
if (Test-Path $CbmExe) {
    try {
        $VersionLine = (& $CbmExe --version | Select-Object -First 1)
        if ($VersionLine -match '(\d+\.\d+\.\d+)') { $InstalledTag = "v$($Matches[1])" }
    } catch { }
}

if (-not $LatestTag -and -not (Test-Path $CbmExe)) {
    throw "Could not resolve the latest codebase-memory-mcp release. Check your network and retry."
}

if ($LatestTag -and $LatestTag -ne $InstalledTag) {
    Write-Host "⬇️  Downloading codebase-memory-mcp engine ($LatestTag)..." -ForegroundColor Cyan
    $DownloadUrl = "https://github.com/DeusData/codebase-memory-mcp/releases/download/$LatestTag/$CbmZip"
    $TempZip = "$env:TEMP\$CbmZip"
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $TempZip -UseBasicParsing
    
    $TempExtract = "$env:TEMP\cbm_extract"
    if (Test-Path $TempExtract) { Remove-Item -Recurse -Force $TempExtract }
    Expand-Archive -Path $TempZip -DestinationPath $TempExtract -Force

    if (Test-Path $CbmExe) {
        # A new engine refuses to start while any older engine process is alive
        try { & $CbmExe daemon stop | Out-Null } catch { }
        Get-Process -Name "codebase-memory-mcp" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        $CbmUpgraded = "$InstalledTag -> $LatestTag"
    }
    Copy-Item "$TempExtract\codebase-memory-mcp.exe" $CbmExe -Force
    Remove-Item $TempZip -Force -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force $TempExtract -ErrorAction SilentlyContinue
    Write-Host "✅ Installed codebase-memory-mcp $LatestTag to $CbmExe" -ForegroundColor Green
} elseif ($LatestTag) {
    Write-Host "✅ codebase-memory-mcp $InstalledTag is already the latest release" -ForegroundColor Green
} else {
    Write-Host "⚠️  Could not check for engine updates; keeping installed $InstalledTag" -ForegroundColor Yellow
}

# 3. Download / Install agent-harness CLI
Write-Host "📦 Installing agent-harness CLI..." -ForegroundColor Cyan
$CliPy = "$InstallDir\agent-harness"
$CliCmd = "$InstallDir\agent-harness.cmd"
$CbmInitCmd = "$InstallDir\cbm-init.cmd"

$RawCliUrl = "https://raw.githubusercontent.com/ArCzyL/agent-harness/main/bin/agent-harness"
Invoke-WebRequest -Uri $RawCliUrl -OutFile $CliPy -UseBasicParsing

$CmdContent = "@echo off`r`npython `"%~dp0agent-harness`" %*`r`n"
Set-Content -Path $CliCmd -Value $CmdContent -Encoding ASCII

$InitCmdContent = "@echo off`r`npython `"%~dp0agent-harness`" init %*`r`n"
Set-Content -Path $CbmInitCmd -Value $InitCmdContent -Encoding ASCII

# 3.1 Install templates
$ShareDir = "$HOME\.local\share\agent-harness\templates"
if (-not (Test-Path $ShareDir)) {
    New-Item -ItemType Directory -Path $ShareDir -Force | Out-Null
}
$RawTmplUrl = "https://raw.githubusercontent.com/ArCzyL/agent-harness/main/templates/karpathy_rules.md"
Invoke-WebRequest -Uri $RawTmplUrl -OutFile "$ShareDir\karpathy_rules.md" -UseBasicParsing -ErrorAction SilentlyContinue

# 4. Add ~/.local/bin to User PATH
$UserPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
if ($UserPath -notlike "*$InstallDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$InstallDir", [EnvironmentVariableTarget]::User)
    $env:Path = "$env:Path;$InstallDir"
    Write-Host "✅ Added $InstallDir to User PATH environment variable." -ForegroundColor Green
}

# 5. Run setup across all supported IDEs
Write-Host "🔧 Configuring all supported AI IDEs..." -ForegroundColor Cyan
& python $CliPy setup

# 6. Start daemon
Write-Host "⚡ Starting codebase memory background daemon..." -ForegroundColor Cyan
Start-Process -FilePath $CbmExe -ArgumentList "daemon","start" -WindowStyle Hidden -ErrorAction SilentlyContinue

Write-Host "
==================================================================
🎉 agent-harness successfully installed on Windows!
==================================================================
How to use:
  1. cd C:\path\to\your\project
  2. agent-harness init .
  3. Open project in TRAE, Cursor, Claude Code, or Antigravity!
  4. Before delivery: agent-harness check   (agent-harness sync if stack facts drifted)

Or in AI chat, simply say: '为当前项目建图并初始化开发规范'
" -ForegroundColor Green

if ($CbmUpgraded) {
    Write-Host "⚠️  Engine upgraded ($CbmUpgraded). Restart codebase-memory-mcp in each open AI tool
   (Cursor: Settings → MCP → toggle it off/on; or restart the app) so the new engine takes over." -ForegroundColor Yellow
}
