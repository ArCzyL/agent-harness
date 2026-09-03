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

# 2. Check / Install codebase-memory-mcp.exe
$CbmExe = "$InstallDir\codebase-memory-mcp.exe"
$CbmVersion = "v0.10.8"

if (-not (Test-Path $CbmExe)) {
    Write-Host "⬇️  Downloading codebase-memory-mcp engine ($CbmVersion)..." -ForegroundColor Cyan
    $DownloadUrl = "https://github.com/DeusData/codebase-memory-mcp/releases/download/$CbmVersion/$CbmZip"
    $TempZip = "$env:TEMP\$CbmZip"
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $TempZip -UseBasicParsing
    
    $TempExtract = "$env:TEMP\cbm_extract"
    if (Test-Path $TempExtract) { Remove-Item -Recurse -Force $TempExtract }
    Expand-Archive -Path $TempZip -DestinationPath $TempExtract -Force
    
    Copy-Item "$TempExtract\codebase-memory-mcp.exe" $CbmExe -Force
    Remove-Item $TempZip -Force -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force $TempExtract -ErrorAction SilentlyContinue
    Write-Host "✅ Installed codebase-memory-mcp to $CbmExe" -ForegroundColor Green
} else {
    Write-Host "✅ Found existing codebase-memory-mcp at $CbmExe" -ForegroundColor Green
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

# 5. Run setup across installed IDEs
Write-Host "🔧 Configuring installed AI IDEs..." -ForegroundColor Cyan
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

Or in AI chat, simply say: '为当前项目建图并初始化开发规范'
" -ForegroundColor Green
