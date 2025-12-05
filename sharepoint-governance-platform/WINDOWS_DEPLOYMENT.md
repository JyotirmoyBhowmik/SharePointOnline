# SharePoint Governance Platform - Windows Deployment Guide

## 🪟 Prerequisites for Windows

### 1. Docker Desktop for Windows
**Required**: Yes  
**Download**: https://www.docker.com/products/docker-desktop

**Installation Steps**:
1. Download Docker Desktop installer
2. Run `Docker Desktop Installer.exe`
3. Follow the installation wizard
4. **IMPORTANT**: Enable WSL 2 during installation (recommended)
5. Restart your computer
6. Launch Docker Desktop from Start Menu
7. Wait for Docker to start (whale icon in system tray)

**Verify Installation**:
```powershell
# Open PowerShell
docker --version
docker-compose --version
```

**Expected Output**:
```
Docker version 24.0.x
Docker Compose version v2.23.x
```

---

### 2. Windows Subsystem for Linux (WSL 2) - Recommended
**Required**: Recommended for Docker Desktop  
**Download**: Built into Windows 10/11

**Installation Steps**:
```powershell
# Open PowerShell as Administrator
wsl --install

# Restart computer
```

**Verify**:
```powershell
wsl --list --verbose
```

---

### 3. Git for Windows
**Required**: Yes  
**Download**: https://git-scm.com/download/win

**Installation Steps**:
1. Download Git installer
2. Run installer with default settings
3. Choose "Use Git from Git Bash only" or "Git from the command line"

**Verify**:
```powershell
git --version
```

---

### 4. Node.js (Optional - for frontend development)
**Required**: No (only for UI development)  
**Download**: https://nodejs.org/

**Installation Steps**:
1. Download LTS version (18.x or higher)
2. Run `.msi` installer
3. Accept defaults

**Verify**:
```powershell
node --version
npm --version
```

---

### 5. PowerShell 7+ (Recommended)
**Required**: No (Windows has PowerShell built-in)  
**Download**: https://github.com/PowerShell/PowerShell/releases

**Installation Steps**:
1. Download `.msi` installer
2. Run installer
3. Launch "PowerShell 7" from Start Menu

---

## 🚀 Quick Deployment (Windows)

### Method 1: Automated PowerShell Script (EASIEST)

1. **Open PowerShell as Administrator**:
   - Press `Win + X`
   - Select "Windows PowerShell (Admin)" or "Terminal (Admin)"

2. **Navigate to project**:
   ```powershell
   cd C:\Users\YourUsername\Documents\SharePointOnline\sharepoint-governance-platform
   ```

3. **Allow script execution** (one-time):
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

4. **Run deployment script**:
   ```powershell
   .\deploy-windows.ps1
   ```

The script will:
- ✅ Check prerequisites
- ✅ Clone repository (if needed)
- ✅ Configure environment
- ✅ Build Docker images
- ✅ Start all services
- ✅ Run database migrations
- ✅ Verify deployment

---

### Method 2: Manual Deployment (Step-by-Step)

#### Step 1: Clone Repository

```powershell
# Open PowerShell
cd C:\Users\$env:USERNAME\Documents

# Clone repository
git clone https://github.com/JyotirmoyBhowmik/SharePointOnline.git

# Navigate to project
cd SharePointOnline\sharepoint-governance-platform
```

#### Step 2: Configure Environment

```powershell
# Copy environment template
Copy-Item .env.example .env

# Edit with Notepad
notepad .env
```

**Required Configuration** (in `.env`):
```bash
# Microsoft Graph API (from Azure AD)
GRAPH_CLIENT_ID=your-azure-app-client-id
GRAPH_CLIENT_SECRET=your-azure-app-secret
GRAPH_TENANT_ID=your-tenant-id

# Database
POSTGRES_SERVER=postgres
POSTGRES_DB=sharepoint_gov
POSTGRES_USER=admin
POSTGRES_PASSWORD=ChangeMe123!StrongPassword

# Redis
REDIS_URL=redis://redis:6379/0

# JWT Secrets (generate random strings)
SECRET_KEY=generate-a-random-64-character-string-here
JWT_SECRET_KEY=another-random-64-character-string-here

# AD/LDAP
LDAP_SERVER=ldap://your-ad-server.company.com
LDAP_BASE_DN=dc=company,dc=com
LDAP_BIND_DN=cn=service,dc=company,dc=com
LDAP_BIND_PASSWORD=service-account-password
```

**Generate JWT Secrets** (PowerShell):
```powershell
# Generate random secret
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object {[char]$_})
```

#### Step 3: Build Docker Images

```powershell
# Ensure Docker Desktop is running (check system tray)
docker-compose build
```

**Expected**: "Successfully built" messages for backend and frontend

#### Step 4: Start Services

```powershell
docker-compose up -d
```

**Verify Services Are Running**:
```powershell
docker-compose ps
```

You should see:
- `backend` - Up, port 8000
- `frontend` - Up, port 3000
- `postgres` - Up, port 5432
- `redis` - Up, port 6379

#### Step 5: Database Migration

```powershell
# Wait for PostgreSQL to be ready (wait 15 seconds)
Start-Sleep -Seconds 15

# Run migrations
docker-compose exec backend alembic upgrade head
```

**Verify Migration**:
```powershell
docker-compose exec backend alembic current
```

#### Step 6: Verify Deployment

```powershell
# Test health endpoint
Invoke-RestMethod -Uri http://localhost:8000/health

# Expected output:
# status: healthy
# components: database, cache, scheduler all healthy
```

**Open in Browser**:
```powershell
# Open API documentation
Start-Process http://localhost:8000/api/v1/docs

# Open frontend
Start-Process http://localhost:3000
```

---

## 🧪 Testing on Windows

### Test Backend API

```powershell
# Test login endpoint
$body = @{
    username = "admin@company.com"
    password = "your-password"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/api/v1/auth/login `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

### View Logs

```powershell
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Restart Services

```powershell
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

---

## 📊 Monitoring (Windows)

### Start Monitoring Stack

```powershell
cd monitoring
docker-compose -f docker-compose-monitoring.yml up -d
```

**Access**:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin / admin_change_me)
- Alertmanager: http://localhost:9093

---

## 🔧 Troubleshooting (Windows)

### Docker Desktop Not Starting

**Solution 1**: Enable Virtualization in BIOS
- Restart computer
- Enter BIOS (usually F2, F10, or Del during boot)
- Enable Intel VT-x or AMD-V
- Save and exit

**Solution 2**: Enable Hyper-V
```powershell
# Run as Administrator
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
```

### Port Already in Use

```powershell
# Check what's using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Services Won't Start

```powershell
# Check Docker Desktop is running
Get-Process "*docker*"

# Restart Docker Desktop
Restart-Service docker

# Or restart from system tray
```

### Permission Denied Errors

```powershell
# Run PowerShell as Administrator
# Right-click PowerShell → "Run as Administrator"
```

### Database Connection Fails

```powershell
# Check PostgreSQL is running
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

---

## 📱 Frontend Development (Windows)

### Install Dependencies

```powershell
cd frontend

# Install Node packages
npm install

# Run development server
npm run dev
```

**Access**: http://localhost:5173 (Vite dev server)

### Build for Production

```powershell
npm run build

# Preview build
npm run preview
```

---

## 🛑 Stopping the Platform

```powershell
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Stop but keep data
docker-compose stop
```

---

## 🔄 Updating the Platform

```powershell
# Pull latest code
git pull origin main

# Rebuild images
docker-compose build

# Restart services
docker-compose down
docker-compose up -d

# Run new migrations
docker-compose exec backend alembic upgrade head
```

---

## 💾 Backup (Windows)

### Backup Database

```powershell
# Backup to file
docker-compose exec -T postgres pg_dump -U admin sharepoint_gov > backup_$(Get-Date -Format "yyyyMMdd_HHmmss").sql

# Compressed backup
docker-compose exec -T postgres pg_dump -U admin sharepoint_gov | gzip > backup.sql.gz
```

### Restore Database

```powershell
# Restore from backup
Get-Content backup.sql | docker-compose exec -T postgres psql -U admin sharepoint_gov
```

---

## 🌐 Network Configuration (Windows Firewall)

### Allow Docker Ports

```powershell
# Run as Administrator
# Allow port 8000 (Backend)
New-NetFirewallRule -DisplayName "SharePoint Gov Backend" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow

# Allow port 3000 (Frontend)
New-NetFirewallRule -DisplayName "SharePoint Gov Frontend" -Direction Inbound -LocalPort 3000 -Protocol TCP -Action Allow
```

---

## 📚 Additional Resources for Windows Users

- **Docker Desktop Documentation**: https://docs.docker.com/desktop/windows/
- **WSL 2 Setup**: https://docs.microsoft.com/en-us/windows/wsl/install
- **PowerShell 7**: https://docs.microsoft.com/en-us/powershell/
- **Git for Windows**: https://gitforwindows.org/

---

## ✅ Post-Deployment Checklist

- [ ] Docker Desktop installed and running
- [ ] Repository cloned
- [ ] `.env` file configured with credentials
- [ ] Services started with `docker-compose up -d`
- [ ] Database migrated with `alembic upgrade head`
- [ ] Health check passes at http://localhost:8000/health
- [ ] Frontend accessible at http://localhost:3000
- [ ] API docs accessible at http://localhost:8000/api/v1/docs
- [ ] Successfully logged in with AD credentials

---

## 🆘 Getting Help

- **User Manual**: See `USER_MANUAL.md`
- **Runbook**: See `RUNBOOK.md`
- **Testing**: See `TESTING_GUIDE.md`
- **Support**: sharepoint-gov-support@company.com

---

**Platform Version**: 3.0.0  
**Last Updated**: December 5, 2025  
**Maintained By**: Platform Engineering Team
