# PowerShell script to setup WSL2 for AMD GPU + ROCm
# Run this as Administrator in PowerShell

Write-Host "🔧 Setting up WSL2 for AMD GPU support..." -ForegroundColor Green

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator"))
{
    Write-Host "❌ This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Running as Administrator" -ForegroundColor Green

# Check Windows version
$version = [System.Environment]::OSVersion.Version
if ($version.Build -lt 19041) {
    Write-Host "❌ Windows 10 version 2004+ (Build 19041+) or Windows 11 required" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Windows version compatible: $($version.Major).$($version.Minor) Build $($version.Build)" -ForegroundColor Green

# Enable WSL2 if not already enabled
Write-Host "🔧 Checking WSL installation..." -ForegroundColor Cyan

try {
    $wslStatus = wsl --status 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ WSL already installed" -ForegroundColor Green
    }
} catch {
    Write-Host "📦 Installing WSL..." -ForegroundColor Yellow
    wsl --install --no-launch
    Write-Host "⚠️ WSL installed. Please restart your computer and run this script again." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 0
}

# Set WSL2 as default
Write-Host "🔧 Setting WSL2 as default..." -ForegroundColor Cyan
wsl --set-default-version 2

# Check if Ubuntu 22.04 is installed
Write-Host "🔧 Checking Ubuntu installation..." -ForegroundColor Cyan
$distributions = wsl --list --verbose
if ($distributions -notmatch "Ubuntu-22.04") {
    Write-Host "📦 Installing Ubuntu 22.04 LTS..." -ForegroundColor Yellow
    wsl --install -d Ubuntu-22.04
    Write-Host "✅ Ubuntu 22.04 installed" -ForegroundColor Green
    Write-Host "⚠️ Please complete Ubuntu setup (username/password) in the Ubuntu window" -ForegroundColor Yellow
    Write-Host "Then run the setup script inside Ubuntu." -ForegroundColor Yellow
} else {
    Write-Host "✅ Ubuntu 22.04 already installed" -ForegroundColor Green
}

# Copy setup script to WSL2
Write-Host "📁 Copying setup script to WSL2..." -ForegroundColor Cyan
$currentDir = Get-Location
$setupScript = Join-Path $currentDir "setup-wsl2.sh"

if (Test-Path $setupScript) {
    # Copy to WSL2 home directory
    wsl cp /mnt/d/Proyectos/live-video-editor/setup-wsl2.sh ~/setup-wsl2.sh
    wsl chmod +x ~/setup-wsl2.sh
    Write-Host "✅ Setup script copied to WSL2" -ForegroundColor Green
} else {
    Write-Host "❌ setup-wsl2.sh not found in current directory" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 WSL2 setup completed!" -ForegroundColor Green
Write-Host ""
Write-Host "🚪 How to access Ubuntu:" -ForegroundColor Cyan
Write-Host "• Method 1: Press Windows key → type 'Ubuntu' → click 'Ubuntu 22.04 LTS'" -ForegroundColor White
Write-Host "• Method 2: Open Windows Terminal → select Ubuntu tab" -ForegroundColor White
Write-Host "• Method 3: In PowerShell/CMD type: wsl" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Open Ubuntu using any method above" -ForegroundColor White
Write-Host "2. Run: chmod +x ~/setup-wsl2.sh && ~/setup-wsl2.sh" -ForegroundColor White
Write-Host "3. Follow the on-screen instructions" -ForegroundColor White
Write-Host ""
Write-Host "For GUI support:" -ForegroundColor Cyan
Write-Host "• Windows 11 22H2+: Built-in support (WSLg)" -ForegroundColor White
Write-Host "• Windows 10/11: Install VcXsrv or X410" -ForegroundColor White

Read-Host "Press Enter to continue"
