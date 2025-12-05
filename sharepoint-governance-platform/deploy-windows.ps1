# ============================================================================
# SharePoint Governance Platform - Windows Deployment Script
# ============================================================================
#
# Author: Jyotirmoy Bhowmik
# Email: jyotirmoy.bhowmik@company.com
# Version: 3.0.0
# Created: 2025
# Last Modified: December 5, 2025
#
# Description:
#   PowerShell deployment script for Windows environments.
#   Automates the complete deployment process including prerequisite checks,
#   environment configuration, Docker container deployment, and verification.
#
#   This script performs:
#   1. Administrator privilege verification
#   2. Prerequisite checks (Docker Desktop, Git, Node.js)
#   3. Repository cloning (if needed)
#   4. Environment variable configuration
#   5. Docker image building
#   6. Service startup and health verification
#   7. Database migration execution
#   8. Deployment verification
#
# Requirements:
#   - Windows 10 version 2004+ or Windows 11
#   - Docker Desktop for Windows installed
#   - WSL 2 enabled (recommended)
#   - PowerShell 5.1+ or PowerShell 7+
#   - 8GB RAM minimum, 16GB recommended
#   - 30GB free disk space
#   - Administrator privileges
#
# Usage:
#   1. Open PowerShell as Administrator
#   2. Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
#   3. .\deploy-windows.ps1
#
# Maintained by: Jyotirmoy Bhowmik
# ============================================================================

$ErrorActionPreference = "Stop"  # Stop execution on any error

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "SharePoint Governance Platform Deployment" -ForegroundColor Cyan
Write-Host "Windows Edition" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if command exists
function Test-CommandExists {
    param($Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

# Function to print status messages
function Write-Status {
    param(
        [string]$Message,
        [string]$Status = "Info"
    )
    switch ($Status) {
        "Success" { Write-Host "[OK] $Message" -ForegroundColor Green }
        "Error" { Write-Host "[ERROR] $Message" -ForegroundColor Red }
        "Warning" { Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
        "Info" { Write-Host "[INFO] $Message" -ForegroundColor Cyan }
    }
}

# Step 1: Check Prerequisites
Write-Host "Step 1: Checking prerequisites..." -ForegroundColor Yellow
Write-Host "--------------------------------" -ForegroundColor Yellow

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Status "This script requires Administrator privileges" "Warning"
    Write-Status "Please run PowerShell as Administrator and try again" "Error"
    exit 1
}

# Check Docker Desktop
if (Test-CommandExists docker) {
    $dockerVersion = docker --version
    Write-Status "Docker installed: $dockerVersion" "Success"
} else {
    Write-Status "Docker Desktop not installed" "Error"
    Write-Host ""
    Write-Host "Please install Docker Desktop for Windows:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor White
    Write-Host "2. Run the installer" -ForegroundColor White
    Write-Host "3. Restart your computer" -ForegroundColor White
    Write-Host "4. Run this script again" -ForegroundColor White
    Write-Host ""
    $response = Read-Host "Would you like to open the download page? (Y/N)"
    if ($response -eq "Y" -or $response -eq "y") {
        Start-Process "https://www.docker.com/products/docker-desktop"
    }
    exit 1
}

# Check Docker Compose
if (Test-CommandExists docker-compose) {
    Write-Status "Docker Compose installed" "Success"
} else {
    Write-Status "Docker Compose not found (included with Docker Desktop)" "Warning"
}

# Check Git
if (Test-CommandExists git) {
    $gitVersion = git --version
    Write-Status "Git installed: $gitVersion" "Success"
} else {
    Write-Status "Git not installed" "Warning"
    Write-Host "Install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
}

# Check Node.js (optional)
if (Test-CommandExists node) {
    $nodeVersion = node --version
    Write-Status "Node.js installed: $nodeVersion" "Success"
} else {
    Write-Status "Node.js not installed (optional for frontend development)" "Warning"
}

Write-Host ""
Write-Host "Step 2: Navigate to project directory" -ForegroundColor Yellow
Write-Host "--------------------------------------" -ForegroundColor Yellow

# Set project path
$projectPath = "C:\Users\$env:USERNAME\Documents\SharePointOnline\sharepoint-governance-platform"

# Check if project exists
if (-not (Test-Path $projectPath)) {
    Write-Status "Project directory not found at: $projectPath" "Error"
    Write-Host ""
    
    # Ask if user wants to clone
    $response = Read-Host "Would you like to clone the repository? (Y/N)"
    if ($response -eq "Y" -or $response -eq "y") {
        $repoUrl = Read-Host "Enter repository URL (or press Enter for default)"
        if ([string]::IsNullOrWhiteSpace($repoUrl)) {
            $repoUrl = "https://github.com/JyotirmoyBhowmik/SharePointOnline.git"
        }
        
        $parentPath = Split-Path $projectPath -Parent
        New-Item -ItemType Directory -Force -Path $parentPath | Out-Null
        Set-Location $parentPath
        
        Write-Status "Cloning repository..." "Info"
        git clone $repoUrl
        Set-Location $projectPath
    } else {
        Write-Status "Please clone the repository and run this script again" "Error"
        exit 1
    }
} else {
    Set-Location $projectPath
    Write-Status "Project directory: $projectPath" "Success"
}

Write-Host ""
Write-Host "Step 3: Configure environment variables" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    Write-Status "Creating .env from .env.example..." "Info"
    Copy-Item ".env.example" ".env"
    
    Write-Host ""
    Write-Status "IMPORTANT: Edit .env file with your credentials:" "Warning"
    Write-Host "   - Microsoft Graph API credentials" -ForegroundColor White
    Write-Host "   - PostgreSQL password" -ForegroundColor White
    Write-Host "   - JWT secrets" -ForegroundColor White
    Write-Host "   - AD/LDAP settings" -ForegroundColor White
    Write-Host ""
    
    $response = Read-Host "Press ENTER to open .env in Notepad, or type 'skip' to edit later"
    if ($response -ne "skip") {
        notepad .env
        $response = Read-Host "Have you saved your changes? Press ENTER to continue"
    }
} else {
    Write-Status ".env file already exists" "Success"
}

Write-Host ""
Write-Host "Step 4: Build Docker images" -ForegroundColor Yellow
Write-Host "----------------------------" -ForegroundColor Yellow
docker-compose build

Write-Host ""
Write-Host "Step 5: Start services" -ForegroundColor Yellow
Write-Host "----------------------" -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "Step 6: Wait for services to be ready" -ForegroundColor Yellow
Write-Host "--------------------------------------" -ForegroundColor Yellow

Write-Status "Waiting for PostgreSQL..." "Info"
Start-Sleep -Seconds 10

$maxAttempts = 30
$attempt = 0
$postgresReady = $false

while (-not $postgresReady -and $attempt -lt $maxAttempts) {
    $attempt++
    try {
        docker-compose exec -T postgres pg_isready -U admin 2>$null
        if ($LASTEXITCODE -eq 0) {
            $postgresReady = $true
            Write-Status "PostgreSQL is ready" "Success"
        } else {
            Write-Host "." -NoNewline
            Start-Sleep -Seconds 2
        }
    } catch {
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 2
    }
}
Write-Host ""

if (-not $postgresReady) {
    Write-Status "PostgreSQL failed to start within timeout" "Error"
    Write-Host "Check logs: docker-compose logs postgres" -ForegroundColor Yellow
    exit 1
}

Write-Status "Waiting for Redis..." "Info"
Start-Sleep -Seconds 3

try {
    docker-compose exec -T redis redis-cli ping 2>$null | Out-Null
    Write-Status "Redis is ready" "Success"
} catch {
    Write-Status "Redis not responding (non-critical)" "Warning"
}

Write-Host ""
Write-Host "Step 7: Run database migrations" -ForegroundColor Yellow
Write-Host "--------------------------------" -ForegroundColor Yellow
docker-compose exec backend alembic upgrade head

if ($LASTEXITCODE -eq 0) {
    Write-Status "Database migrations complete" "Success"
} else {
    Write-Status "Database migration failed" "Error"
    Write-Host "Check logs: docker-compose logs backend" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Step 8: Verify deployment" -ForegroundColor Yellow
Write-Host "-------------------------" -ForegroundColor Yellow

Write-Status "Checking service health..." "Info"
docker-compose ps

Write-Host ""
Write-Status "Testing backend health endpoint..." "Info"
Start-Sleep -Seconds 3

try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -ErrorAction Stop
    if ($healthResponse.status -eq "healthy") {
        Write-Status "Backend is healthy" "Success"
    } else {
        Write-Status "Backend health check returned: $($healthResponse.status)" "Warning"
    }
} catch {
    Write-Status "Backend health check failed (may still be starting)" "Warning"
    Write-Host "Wait 30 seconds and try: http://localhost:8000/health" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access the platform:" -ForegroundColor Cyan
Write-Host "  • Frontend:    http://localhost:3000" -ForegroundColor White
Write-Host "  • Backend:     http://localhost:8000" -ForegroundColor White
Write-Host "  • API Docs:    http://localhost:8000/api/v1/docs" -ForegroundColor White
Write-Host "  • Health:      http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Open http://localhost:3000 in your browser" -ForegroundColor White
Write-Host "  2. Login with your AD credentials" -ForegroundColor White
Write-Host "  3. Trigger site discovery via API" -ForegroundColor White
Write-Host "  4. View documentation in QUICKSTART.md" -ForegroundColor White
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  • View logs:   docker-compose logs -f" -ForegroundColor White
Write-Host "  • Stop:        docker-compose down" -ForegroundColor White
Write-Host "  • Restart:     docker-compose restart" -ForegroundColor White
Write-Host ""

# Ask if user wants to open browser
$response = Read-Host "Would you like to open the platform in your browser? (Y/N)"
if ($response -eq "Y" -or $response -eq "y") {
    Start-Process "http://localhost:8000/api/v1/docs"
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:3000"
}

Write-Host ""
Write-Host "Deployment script completed successfully!" -ForegroundColor Green
