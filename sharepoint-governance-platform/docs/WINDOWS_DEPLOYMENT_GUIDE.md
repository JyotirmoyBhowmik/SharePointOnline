# SharePoint Governance Platform - Windows Deployment Guide

**Version:** 1.0.0  
**Last Updated:** 2025-12-05  
**Target OS:** Windows 10/11 or Windows Server 2016+

This guide provides step-by-step instructions for deploying the SharePoint Governance Platform on a Windows environment.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Software Installation](#software-installation)
3. [Code Deployment](#code-deployment)
4. [Database Setup](#database-setup)
5. [Configuration](#configuration)
6. [Backend Setup](#backend-setup)
7. [Frontend Setup](#frontend-setup)
8. [Running the Application](#running-the-application)
9. [Verification](#verification)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- Windows 10/11 (64-bit) or Windows Server 2016+
- Administrator access (for installations)
- Internet connection (for downloading dependencies)
- Minimum 8GB RAM
- 20GB free disk space

### Required Credentials
You will need to obtain the following before starting:
- PostgreSQL admin credentials
- Azure AD Tenant ID, Client ID, and Client Secret
- Active Directory service account credentials
- LDAP server address and Base DN

Refer to the [Configuration Guide](CONFIGURATION_GUIDE.md) for details on obtaining these credentials.

---

## Software Installation

### Step 1: Install Python 3.11

1. **Download Python:**
   - Open your web browser
   - Navigate to: https://www.python.org/downloads/
   - Download **Python 3.11.x** (Windows installer, 64-bit)

2. **Run the Installer:**
   ```
   - Double-click the downloaded `python-3.11.x-amd64.exe`
   - ✅ CHECK: "Add Python 3.11 to PATH"
   - ✅ CHECK: "Install launcher for all users"
   - Click "Install Now"
   - Wait for installation to complete
   - Click "Close"
   ```

3. **Verify Installation:**
   - Press `Win + R`
   - Type `cmd` and press Enter
   - In the Command Prompt, type:
     ```cmd
     python --version
     ```
   - Expected output: `Python 3.11.x`
   - Type:
     ```cmd
     pip --version
     ```
   - Expected output: `pip 23.x.x from ...`

### Step 2: Install Node.js 18 LTS

1. **Download Node.js:**
   - Navigate to: https://nodejs.org/
   - Download **Node.js 18.x LTS** (Windows Installer, 64-bit)

2. **Run the Installer:**
   ```
   - Double-click `node-v18.x.x-x64.msi`
   - Click "Next"
   - Accept license agreement → "Next"
   - Keep default installation path: C:\Program Files\nodejs\
   - Accept default components → "Next"
   - ✅ CHECK: "Automatically install necessary tools"
   - Click "Install"
   - Wait for installation
   - Click "Finish"
   ```

3. **Verify Installation:**
   - Open a **NEW** Command Prompt (Win + R → `cmd`)
   - Type:
     ```cmd
     node --version
     ```
   - Expected output: `v18.x.x`
   - Type:
     ```cmd
     npm --version
     ```
   - Expected output: `9.x.x` or `10.x.x`

### Step 3: Install PostgreSQL 15

1. **Download PostgreSQL:**
   - Navigate to: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
   - Download **PostgreSQL 15.x** for Windows x86-64

2. **Run the Installer:**
   ```
   - Double-click `postgresql-15.x-windows-x64.exe`
   - Click "Next"
   - Installation Directory: C:\Program Files\PostgreSQL\15
   - Select components:
     ✅ PostgreSQL Server
     ✅ pgAdmin 4
     ✅ Stack Builder
     ✅ Command Line Tools
   - Data Directory: C:\Program Files\PostgreSQL\15\data
   - Set Superuser Password: <WRITE THIS DOWN SECURELY>
     Example: PostgresAdmin123!
   - Port: 5432 (default)
   - Locale: Default locale
   - Click "Next" → "Next" → "Finish"
   ```

3. **Add PostgreSQL to PATH:**
   - Press `Win + X` → Select "System"
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - Under "System variables", select "Path" → Click "Edit"
   - Click "New" → Add:
     ```
     C:\Program Files\PostgreSQL\15\bin
     ```
   - Click "OK" → "OK" → "OK"
   - Close and reopen any Command Prompt windows

4. **Verify Installation:**
   ```cmd
   psql --version
   ```
   - Expected output: `psql (PostgreSQL) 15.x`

### Step 4: Install Git for Windows

1. **Download Git:**
   - Navigate to: https://git-scm.com/download/win
   - Download the 64-bit Windows installer

2. **Run the Installer:**
   ```
   - Double-click `Git-x.x.x-64-bit.exe`
   - Click "Next"
   - Installation path: C:\Program Files\Git
   - Components: Keep defaults (✅ Git Bash, ✅ Git GUI)
   - Start Menu folder: Git
   - Default editor: Use Notepad++ or VS Code (if installed)
   - PATH environment: "Git from the command line and also from 3rd-party software"
   - HTTPS transport: "Use the OpenSSL library"
   - Line ending conversions: "Checkout Windows-style, commit Unix-style"
   - Terminal emulator: "Use MinTTY"
   - Click "Install"
   - Click "Finish"
   ```

3. **Verify Installation:**
   ```cmd
   git --version
   ```
   - Expected output: `git version 2.x.x`

### Step 5: Install Redis (Optional but Recommended)

Redis doesn't have official Windows support, but we'll use a community port or WSL.

**Option A: Using WSL (Recommended)**

1. **Enable WSL:**
   ```powershell
   # Run PowerShell as Administrator
   wsl --install
   # Restart computer when prompted
   ```

2. **Install Redis in WSL:**
   ```bash
   # After restart, open Ubuntu/WSL terminal
   sudo apt update
   sudo apt install redis-server
   sudo service redis-server start
   ```

**Option B: Using Memurai (Windows Native)**

1. **Download Memurai:**
   - Navigate to: https://www.memurai.com/get-memurai
   - Download Memurai (free version)

2. **Install:**
   ```
   - Run installer
   - Keep default port: 6379
   - Install as Windows Service: ✅
   - Start service: ✅
   ```

---

## Code Deployment

### Step 6: Create Deployment Directory

1. **Open File Explorer**
   - Navigate to `C:\`
   - Create folder: `SharePointGovernance`
   - Full path: `C:\SharePointGovernance`

### Step 7: Copy Application Code

**Option A: Using Git (Recommended)**

1. **Open Command Prompt**
   ```cmd
   cd C:\SharePointGovernance
   git clone <YOUR_REPOSITORY_URL> platform
   cd platform
   ```

**Option B: Manual Copy**

1. **If you have the code on a USB drive or network share:**
   ```
   - Copy the entire `sharepoint-governance-platform` folder
   - Paste to: C:\SharePointGovernance\platform
   ```

2. **Verify Structure:**
   ```
   C:\SharePointGovernance\platform\
   ├── backend\
   ├── frontend\
   ├── docs\
   ├── .env.example
   ├── docker-compose.yml
   └── README.md
   ```

---

## Database Setup

### Step 8: Create PostgreSQL Database

1. **Open Command Prompt**
   ```cmd
   cd C:\SharePointGovernance\platform
   ```

2. **Connect to PostgreSQL:**
   ```cmd
   psql -U postgres -h localhost
   ```
   - Enter password when prompted (the one you set during installation)

3. **Create Database and User:**
   ```sql
   -- Create database
   CREATE DATABASE spg_db;

   -- Create user
   CREATE USER spg_user WITH ENCRYPTED PASSWORD 'YourSecurePassword123!';

   -- Grant privileges
   GRANT ALL PRIVILEGES ON DATABASE spg_db TO spg_user;

   -- Connect to the new database
   \c spg_db

   -- Grant schema privileges
   GRANT ALL ON SCHEMA public TO spg_user;

   -- Exit
   \q
   ```

4. **Test Connection:**
   ```cmd
   psql -U spg_user -h localhost -d spg_db
   ```
   - Enter the password you just created
   - If successful, you'll see: `spg_db=>`
   - Type `\q` to exit

---

## Configuration

### Step 9: Create .env File

1. **Open File Explorer**
   - Navigate to: `C:\SharePointGovernance\platform`
   - Find file: `.env.example`

2. **Copy and Rename:**
   - Right-click `.env.example`
   - Select "Copy"
   - Right-click in the same folder → "Paste"
   - Rename the copy to `.env` (remove `.example`)
   - **Note:** Windows might warn that changing file extension could make it unusable - click "Yes"

3. **Edit .env File:**
   - Right-click `.env` → "Open with" → "Notepad" (or VS Code if installed)

### Step 10: Configure Database Connection

Find and update these lines in `.env`:

```env
# Database
DATABASE_URL=postgresql://spg_user:YourSecurePassword123!@localhost:5432/spg_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

**Replace:**
- `spg_user` → Your PostgreSQL username (from Step 8)
- `YourSecurePassword123!` → Your PostgreSQL password (from Step 8)
- `localhost` → Keep as is (unless database is on another server)
- `5432` → PostgreSQL port (default)
- `spg_db` → Database name (from Step 8)

### Step 11: Configure Redis Connection

```env
# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=300
```

**If using WSL:**
- Use `REDIS_URL=redis://127.0.0.1:6379/0`

**If using Memurai:**
- Use `REDIS_URL=redis://localhost:6379/0`

**If Redis is not available:**
- Use `REDIS_URL=redis://localhost:6379/0` (application will work without Redis, but caching will be disabled)

### Step 12: Configure Microsoft 365 Integration

You need to create an Azure AD App Registration first.

#### 12.1: Create Azure AD App Registration

1. **Open Browser** → Navigate to: https://portal.azure.com
2. **Sign in** with your Microsoft 365 admin account
3. **Navigate to Azure Active Directory:**
   - Click on "Azure Active Directory" in the left menu
   - Or search for "Azure Active Directory" in the top search bar

4. **Create App Registration:**
   ```
   - Click "App registrations" in left menu
   - Click "+ New registration"
   
   Name: SharePoint Governance Platform
   Supported account types: Accounts in this organizational directory only
   Redirect URI: Leave blank for now
   
   - Click "Register"
   ```

5. **Copy Tenant ID and Client ID:**
   - After registration, you'll see the "Overview" page
   - Copy and save these values:
     ```
     Directory (tenant) ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
     Application (client) ID: yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
     ```

6. **Create Client Secret:**
   ```
   - Click "Certificates & secrets" in left menu
   - Click "+ New client secret"
   
   Description: SPG Backend Secret
   Expires: 24 months (recommended)
   
   - Click "Add"
   - ⚠️ IMMEDIATELY copy the "Value" (you cannot see it again!)
   - Save as: zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz
   ```

7. **Configure API Permissions:**
   ```
   - Click "API permissions" in left menu
   - Click "+ Add a permission"
   - Click "Microsoft Graph"
   - Click "Application permissions"
   - Search and add:
     ✅ Sites.Read.All
     ✅ Sites.ReadWrite.All
     ✅ User.Read.All
     ✅ Group.Read.All
     ✅ Files.Read.All
     ✅ AuditLog.Read.All
     ✅ Mail.Send
   - Click "Add permissions"
   - Click "Grant admin consent for [Your Organization]"
   - Click "Yes"
   - Wait for all permissions to show "Granted for [Your Organization]"
   ```

#### 12.2: Update .env File

In your `.env` file, update:

```env
# Microsoft 365 Configuration
TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
CLIENT_ID=yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
CLIENT_SECRET=zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz
SHAREPOINT_SITE_URL=https://yourtenant.sharepoint.com
```

**Replace:**
- `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` → Your Tenant ID (from step 5)
- `yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy` → Your Client ID (from step 5)
- `zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz` → Your Client Secret (from step 6)
- `https://yourtenant.sharepoint.com` → Your SharePoint root site URL

**To find your SharePoint URL:**
1. Open browser → Go to office.com
2. Sign in with your Microsoft 365 account
3. Click on "SharePoint" app
4. Copy the URL from browser (e.g., `https://contoso.sharepoint.com`)

### Step 13: Configure Active Directory / LDAP

#### 13.1: Find Your LDAP Server

**On a domain-joined Windows machine:**

1. **Open Command Prompt**
   ```cmd
   echo %LOGONSERVER%
   ```
   - Output example: `\\DC01`
   - This is your domain controller

2. **Get LDAP Server Address:**
   ```cmd
   nslookup DC01
   ```
   - Note the IP address or use the hostname

3. **Construct LDAP URL:**
   ```
   ldap://dc01.yourdomain.com:389
   or
   ldap://192.168.1.100:389
   ```

#### 13.2: Find Your Base DN

**From Domain Name:**
- If your domain is: `company.com`
- Base DN is: `dc=company,dc=com`

- If your domain is: `subdomain.company.com`
- Base DN is: `dc=subdomain,dc=company,dc=com`

**Using Command:**
```cmd
echo %USERDNSDOMAIN%
```
- Output example: `COMPANY.COM`
- Convert to: `dc=company,dc=com`

#### 13.3: Create Service Account

**In Active Directory Users and Computers (on Domain Controller):**

1. **Open Active Directory Users and Computers**
2. **Create new OU (Optional but recommended):**
   - Right-click on your domain → New → Organizational Unit
   - Name: `ServiceAccounts`

3. **Create User:**
   ```
   - Right-click "ServiceAccounts" → New → User
   
   First name: SPG
   Last name: Service
   User logon name: svc_spg
   
   - Click "Next"
   - Set Password: <SECURE_PASSWORD>
   - ✅ User cannot change password
   - ✅ Password never expires
   - ⬜ Account is disabled
   - Click "Next" → "Finish"
   ```

4. **Set Permissions:**
   - The service account needs READ permissions on:
     - User objects
     - Group objects
   - **This should already be granted by default for domain users**

5. **Note the Bind DN:**
   ```
   cn=svc_spg,ou=ServiceAccounts,dc=company,dc=com
   ```

#### 13.4: Update .env File

```env
# Active Directory / LDAP
LDAP_SERVER=ldap://dc01.company.com:389
LDAP_BASE_DN=dc=company,dc=com
LDAP_BIND_DN=cn=svc_spg,ou=ServiceAccounts,dc=company,dc=com
LDAP_BIND_PASSWORD=<YOUR_SERVICE_ACCOUNT_PASSWORD>
LDAP_USER_SEARCH_BASE=ou=Users,dc=company,dc=com
LDAP_GROUP_SEARCH_BASE=ou=Groups,dc=company,dc=com
```

**Replace:**
- `dc01.company.com` → Your domain controller hostname or IP
- `dc=company,dc=com` → Your domain's Base DN
- `cn=svc_spg,ou=ServiceAccounts,dc=company,dc=com` → Your service account DN
- `<YOUR_SERVICE_ACCOUNT_PASSWORD>` → Service account password
- `ou=Users,dc=company,dc=com` → Where users are stored (verify in AD)
- `ou=Groups,dc=company,dc=com` → Where groups are stored (verify in AD)

### Step 14: Configure JWT Secret

1. **Generate Secure Secret**
   
   **Option A: Using Python**
   ```cmd
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   - Copy the output

   **Option B: Using PowerShell**
   ```powershell
   -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
   ```
   - Copy the output

2. **Update .env:**
   ```env
   # JWT Authentication
   SECRET_KEY=<PASTE_YOUR_GENERATED_SECRET_HERE>
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=7
   ```

### Step 15: Configure CORS and Email

```env
# CORS (Frontend URLs)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
CORS_ALLOW_CREDENTIALS=true

# Email Notifications (via Microsoft Graph)
EMAIL_FROM=noreply@company.com
EMAIL_ENABLED=true
```

**Replace:**
- `noreply@company.com` → An email address in your Microsoft 365 tenant
- In production, update `CORS_ORIGINS` to include your actual domain

### Step 16: Save .env File

- Press `Ctrl + S` to save
- Close Notepad

---

## Backend Setup

### Step 17: Install Python Dependencies

1. **Open Command Prompt**
   ```cmd
   cd C:\SharePointGovernance\platform\backend
   ```

2. **Create Virtual Environment:**
   ```cmd
   python -m venv venv
   ```
   - This creates a `venv` folder

3. **Activate Virtual Environment:**
   ```cmd
   venv\Scripts\activate
   ```
   - Your prompt should now show `(venv)` at the beginning

4. **Upgrade pip:**
   ```cmd
   python -m pip install --upgrade pip
   ```

5. **Install Dependencies:**
   ```cmd
   pip install -r requirements.txt
   ```
   - This will take 5-10 minutes
   - You'll see packages being downloaded and installed

6. **Verify Installation:**
   ```cmd
   pip list
   ```
   - You should see packages like:
     - fastapi
     - uvicorn
     - sqlalchemy
     - psycopg2-binary
     - pyotp
     - qrcode
     - etc.

### Step 18: Run Database Migrations

1. **Still in the backend folder with venv activated:**
   ```cmd
   alembic upgrade head
   ```
   - Expected output:
     ```
     INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
     INFO  [alembic.runtime.migration] Will assume transactional DDL.
     INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial_schema
     INFO  [alembic.runtime.migration] Running upgrade 001_initial_schema -> 002_add_two_factor
     ```

2. **If you see errors:**
   - Check that PostgreSQL is running
   - Verify `DATABASE_URL` in `.env` is correct
   - Verify you can connect with `psql -U spg_user -h localhost -d spg_db`

---

## Frontend Setup

### Step 19: Install Frontend Dependencies

1. **Open a NEW Command Prompt** (keep backend one open)
   ```cmd
   cd C:\SharePointGovernance\platform\frontend
   ```

2. **Install Dependencies:**
   ```cmd
   npm install
   ```
   - This will take 5-10 minutes
   - You'll see a progress bar
   - Ignore any warnings about deprecated packages

3. **Verify Installation:**
   ```cmd
   npm list --depth=0
   ```
   - You should see packages like:
     - react
     - react-router-dom
     - @mui/material
     - redux
     - axios
     - qrcode.react
     - etc.

### Step 20: Configure Frontend Environment

1. **Check if `.env` exists in frontend folder:**
   ```cmd
   dir .env
   ```

2. **If not exists, create it:**
   ```cmd
   echo REACT_APP_API_URL=http://localhost:8000 > .env
   echo REACT_APP_API_PREFIX=/api/v1 >> .env
   ```

3. **Or manually create:**
   - Create file: `C:\SharePointGovernance\platform\frontend\.env`
   - Content:
     ```env
     REACT_APP_API_URL=http://localhost:8000
     REACT_APP_API_PREFIX=/api/v1
     ```

---

## Running the Application

### Step 21: Start Backend Server

1. **In the backend Command Prompt (with venv activated):**
   ```cmd
   cd C:\SharePointGovernance\platform\backend
   venv\Scripts\activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Expected output:**
   ```
   INFO:     Will watch for changes in these directories: ['C:\\SharePointGovernance\\platform\\backend']
   INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
   INFO:     Started reloader process using WatchFiles
   INFO:     Started server process
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   ```

3. **Test Backend:**
   - Open browser
   - Navigate to: http://localhost:8000/docs
   - You should see the Swagger API documentation

### Step 22: Start Frontend Server

1. **In the frontend Command Prompt:**
   ```cmd
   cd C:\SharePointGovernance\platform\frontend
   npm start
   ```

2. **Expected output:**
   ```
   Compiled successfully!

   You can now view frontend in the browser.

     Local:            http://localhost:3000
     On Your Network:  http://192.168.x.x:3000

   Note that the development build is not optimized.
   To create a production build, use npm run build.

   webpack compiled successfully
   ```

3. **Browser should automatically open to:**
   - http://localhost:3000

4. **If browser doesn't open:**
   - Manually open browser
   - Navigate to: http://localhost:3000

---

## Verification

### Step 23: Test Application Access

1. **Frontend should load:**
   - You should see the Login page
   - Title: "SharePoint Governance Platform"

2. **Test Backend API:**
   - Open: http://localhost:8000/health
   - Expected response:
     ```json
     {"status": "healthy", "timestamp": "2025-12-05T..."}
     ```

3. **Check API Docs:**
   - Open: http://localhost:8000/docs
   - You should see sections:
     - Authentication
     - Two-Factor Authentication
     - Setup Wizard
     - Sites
     - Access Reviews
     - Audit & Compliance
     - Dashboard

### Step 24: Create First Admin User

**Option A: Using Setup Wizard (Recommended)**

1. **Create initial admin user via database:**
   ```cmd
   psql -U spg_user -h localhost -d spg_db
   ```

2. **Insert admin user:**
   ```sql
   INSERT INTO users (user_id, email, name, role, is_active)
   VALUES (
     gen_random_uuid(),
     'admin@company.com',
     'System Administrator',
     'admin',
     true
   );
   ```

3. **Exit:**
   ```sql
   \q
   ```

**Option B: Login with AD Account**
- If you've configured LDAP correctly
- Try logging in with your AD username and password
- The system will create your user account automatically

### Step 25: Test Login

1. **Open:** http://localhost:3000/login

2. **Enter credentials:**
   - Username: `admin@company.com` (or your AD username)
   - Password: (your AD password)

3. **Click "Sign In"**

4. **If successful:**
   - You'll be redirected to the Dashboard
   - You should see metrics and charts

---

## Creating Windows Services (Production)

### Step 26: Install NSSM (Non-Sucking Service Manager)

1. **Download NSSM:**
   - Navigate to: https://nssm.cc/download
   - Download the latest version (zip file)

2. **Extract:**
   - Extract to: `C:\nssm`
   - Use the `win64` folder for 64-bit Windows

3. **Add to PATH:**
   - Win + X → System → Advanced system settings
   - Environment Variables → System variables → Path → Edit
   - New → `C:\nssm\win64`
   - OK → OK → OK

### Step 27: Create Backend Service

1. **Open Command Prompt as Administrator**

2. **Navigate to backend:**
   ```cmd
   cd C:\SharePointGovernance\platform\backend
   ```

3. **Create service:**
   ```cmd
   nssm install SPG-Backend
   ```

4. **In NSSM dialog:**
   ```
   Path: C:\SharePointGovernance\platform\backend\venv\Scripts\python.exe
   Startup directory: C:\SharePointGovernance\platform\backend
   Arguments: -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   
   Service name: SPG-Backend
   ```

5. **Details tab:**
   ```
   Display name: SharePoint Governance Platform - Backend
   Description: Backend API server for SharePoint Governance Platform
   Startup type: Automatic
   ```

6. **Environment tab:**
   - Click "Edit"
   - Add the contents of your `.env` file (each line as KEY=VALUE)

7. **Click "Install service"**

8. **Start service:**
   ```cmd
   nssm start SPG-Backend
   ```

### Step 28: Create Frontend Service (Production Build)

1. **Build frontend:**
   ```cmd
   cd C:\SharePointGovernance\platform\frontend
   npm run build
   ```
   - This creates an optimized production build in the `build` folder

2. **Install serve globally:**
   ```cmd
   npm install -g serve
   ```

3. **Create service:**
   ```cmd
   nssm install SPG-Frontend
   ```

4. **In NSSM dialog:**
   ```
   Path: C:\Program Files\nodejs\serve.cmd
   Startup directory: C:\SharePointGovernance\platform\frontend
   Arguments: -s build -l 3000
   
   Service name: SPG-Frontend
   ```

5. **Install and start:**
   ```cmd
   nssm start SPG-Frontend
   ```

### Step 29: Configure Windows Firewall

1. **Open Windows Firewall with Advanced Security**
   - Win + R → `wf.msc` → Enter

2. **Create Inbound Rule for Backend:**
   ```
   - Click "Inbound Rules" → "New Rule"
   - Rule Type: Port
   - Protocol: TCP
   - Specific local ports: 8000
   - Action: Allow the connection
   - Profile: Domain, Private, Public (as needed)
   - Name: SPG Backend API
   - Click "Finish"
   ```

3. **Create Inbound Rule for Frontend:**
   ```
   - Repeat above steps
   - Port: 3000
   - Name: SPG Frontend Web
   ```

---

## Troubleshooting

### Backend Won't Start

**Error: `ModuleNotFoundError: No module named 'fastapi'`**
- Solution: Activate virtual environment
  ```cmd
  cd C:\SharePointGovernance\platform\backend
  venv\Scripts\activate
  pip install -r requirements.txt
  ```

**Error: `psycopg2.OperationalError: could not connect to server`**
- Check PostgreSQL is running:
  ```cmd
  sc query postgresql-x64-15
  ```
- If stopped:
  ```cmd
  sc start postgresql-x64-15
  ```
- Verify `DATABASE_URL` in `.env`

**Error: `alembic.util.exc.CommandError: Can't locate revision`**
- Reset migrations:
  ```cmd
  cd C:\SharePointGovernance\platform\backend
  alembic downgrade base
  alembic upgrade head
  ```

### Frontend Won't Start

**Error: `npm ERR! missing script: start`**
- Check you're in the frontend directory
- Verify `package.json` exists
- Reinstall:
  ```cmd
  del /S /Q node_modules
  npm install
  ```

**Error: `Port 3000 is already in use`**
- Find process using port:
  ```cmd
  netstat -ano | findstr :3000
  ```
- Note the PID (last column)
- Kill process:
  ```cmd
  taskkill /PID <PID> /F
  ```

### Cannot Connect to Backend from Frontend

**Check CORS settings:**
- Ensure `CORS_ORIGINS` in `.env` includes `http://localhost:3000`
- Restart backend server after changing `.env`

**Check backend is running:**
```cmd
curl http://localhost:8000/health
```

### LDAP Connection Fails

**Test LDAP connectivity:**
```cmd
ldp.exe
```
- Connection → Connect
- Server: `dc01.company.com`
- Port: 389
- Click OK

**If fails:**
- Verify domain controller is reachable
- Check domain controller firewall allows port 389
- Verify service account credentials

### Azure AD Authentication Fails

**Verify app permissions:**
- Go to Azure Portal → App registrations
- Click your app → API permissions
- Ensure all permissions show "Granted for <org>"
- If not, click "Grant admin consent"

**Test credentials:**
- Use a tool like Postman to test getting a token
- Endpoint: `https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/token`

---

## Production Deployment Checklist

- [ ] Change all default passwords
- [ ] Use HTTPS (configure SSL certificates)
- [ ] Update `CORS_ORIGINS` to production domains
- [ ] Set `DEBUG=false` in `.env`
- [ ] Configure backup for PostgreSQL database
- [ ] Set up log rotation
- [ ] Configure Windows Firewall rules
- [ ] Install antivirus exceptions for app directories
- [ ] Set up monitoring and alerts
- [ ] Document all credentials securely
- [ ] Create backup of `.env` file (encrypted)
- [ ] Test disaster recovery procedures

---

## Support and Documentation

- **Configuration Guide:** `docs/CONFIGURATION_GUIDE.md`
- **API Documentation:** http://localhost:8000/docs
- **Frontend:** http://localhost:3000

---

## Appendix A: Directory Structure

```
C:\SharePointGovernance\platform\
├── backend\
│   ├── venv\                      # Python virtual environment
│   ├── app\
│   │   ├── api\
│   │   ├── core\
│   │   ├── models\
│   │   └── main.py
│   ├── alembic\
│   ├── requirements.txt
│   └── alembic.ini
├── frontend\
│   ├── node_modules\              # NPM packages (gitignored)
│   ├── public\
│   ├── src\
│   ├── build\                     # Production build (after npm run build)
│   ├── package.json
│   └── .env
├── docs\
├── .env                           # Main configuration file
└── README.md
```

---

## Appendix B: Default Ports

| Service | Port | Purpose |
|---------|------|---------|
| Frontend (Dev) | 3000 | React development server |
| Backend API | 8000 | FastAPI/Uvicorn server |
| PostgreSQL | 5432 | Database server |
| Redis/Memurai | 6379 | Cache server |
| LDAP | 389 | Active Directory (unencrypted) |
| LDAPS | 636 | Active Directory (SSL) |

---

## Appendix C: Common Commands

### Backend Commands
```cmd
# Activate virtual environment
cd C:\SharePointGovernance\platform\backend
venv\Scripts\activate

# Start development server
uvicorn app.main:app --reload --port 8000

# Run migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check logs
type C:\SharePointGovernance\platform\backend\app\logs\app.log
```

### Frontend Commands
```cmd
# Start development server
cd C:\SharePointGovernance\platform\frontend
npm start

# Build for production
npm run build

# Run tests
npm test

# Clear cache and rebuild
del /S /Q node_modules
npm install
```

### Database Commands
```cmd
# Connect to database
psql -U spg_user -h localhost -d spg_db

# Backup database
pg_dump -U spg_user -h localhost spg_db > backup.sql

# Restore database
psql -U spg_user -h localhost -d spg_db < backup.sql

# Check database size
psql -U spg_user -h localhost -d spg_db -c "\l+"
```

### Service Management
```cmd
# View service status
sc query SPG-Backend
sc query SPG-Frontend

# Start service
sc start SPG-Backend

# Stop service
sc stop SPG-Backend

# Restart service
sc stop SPG-Backend && sc start SPG-Backend

# Remove service
nssm remove SPG-Backend confirm
```

---

**End of Deployment Guide**

For additional support, refer to the main documentation or contact your system administrator.
