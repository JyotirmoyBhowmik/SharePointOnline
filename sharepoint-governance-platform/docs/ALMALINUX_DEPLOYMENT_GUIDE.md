# SharePoint Governance Platform - AlmaLinux Deployment Guide

**Version:** 1.0.0  
**Last Updated:** 2025-12-05  
**Target OS:** AlmaLinux 8.x / 9.x (also compatible with Rocky Linux, RHEL 8+, CentOS Stream)

This guide provides step-by-step instructions for deploying the SharePoint Governance Platform on AlmaLinux.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [System Preparation](#system-preparation)
3. [Software Installation](#software-installation)
4. [Code Deployment](#code-deployment)
5. [Database Setup](#database-setup)
6. [Configuration](#configuration)
7. [Backend Setup](#backend-setup)
8. [Frontend Setup](#frontend-setup)
9. [Running the Application](#running-the-application)
10. [SystemD Services](#systemd-services)
11. [Firewall Configuration](#firewall-configuration)
12. [SSL/HTTPS Setup](#sslhttps-setup)
13. [Verification](#verification)
14. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- AlmaLinux 8.x or 9.x (64-bit)
- Root or sudo access
- Minimum 4GB RAM (8GB recommended)
- 20GB free disk space
- Internet connection

### Required Credentials
Before starting, gather:
- PostgreSQL admin password (you'll create this)
- Azure AD Tenant ID, Client ID, and Client Secret
- Active Directory service account credentials
- LDAP server address and Base DN

Refer to the [Configuration Guide](CONFIGURATION_GUIDE.md) for credential acquisition details.

---

## System Preparation

### Step 1: Update System

**Log in as root or use sudo for all commands:**

```bash
# Update all packages to latest versions
sudo dnf update -y

# Reboot if kernel was updated (optional but recommended)
sudo reboot
```

After reboot, log back in and continue.

### Step 2: Set Hostname (Optional)

```bash
# Set a meaningful hostname
sudo hostnamectl set-hostname spg-server.yourdomain.com

# Verify
hostnamectl
```

Expected output:
```
Static hostname: spg-server.yourdomain.com
```

### Step 3: Configure SELinux

**Option A: Set to Permissive (easier for development)**

```bash
# Check current status
getenforce

# Set to permissive temporarily
sudo setenforce 0

# Make it permanent
sudo sed -i 's/^SELINUX=enforcing/SELINUX=permissive/' /etc/selinux/config

# Verify
cat /etc/selinux/config | grep SELINUX=
```

Expected: `SELINUX=permissive`

**Option B: Keep Enforcing (production recommended)**

If you keep SELinux enforcing, you'll need to configure contexts later. See [SELinux Configuration](#selinux-configuration) section.

### Step 4: Configure Firewall

```bash
# Check firewall status
sudo firewall-cmd --state

# If not running, start it
sudo systemctl start firewalld
sudo systemctl enable firewalld
```

We'll configure firewall rules later after installing services.

---

## Software Installation

### Step 5: Install Development Tools

```bash
# Install essential build tools
sudo dnf groupinstall "Development Tools" -y

# Install additional utilities
sudo dnf install -y \
    wget \
    curl \
    git \
    vim \
    nano \
    net-tools \
    bind-utils
```

### Step 6: Install Python 3.11

AlmaLinux 8/9 comes with Python 3.6/3.9 by default. We need Python 3.11.

**Install Python 3.11 from EPEL:**

```bash
# Enable EPEL repository
sudo dnf install epel-release -y

# For AlmaLinux 9
sudo dnf install python3.11 python3.11-devel python3.11-pip -y

# For AlmaLinux 8 (if python3.11 not available, use python3.9)
# sudo dnf install python39 python39-devel python39-pip -y
```

**Verify Installation:**

```bash
python3.11 --version
```

Expected output: `Python 3.11.x`

**Create python3 symlink (optional):**

```bash
sudo alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
```

### Step 7: Install Node.js 18 LTS

```bash
# Add NodeSource repository for Node.js 18
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -

# Install Node.js
sudo dnf install nodejs -y

# Verify installation
node --version
npm --version
```

Expected output:
```
v18.x.x
9.x.x or 10.x.x
```

### Step 8: Install PostgreSQL 15

```bash
# Add PostgreSQL repository
sudo dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-$(rpm -E %{rhel})-x86_64/pgdg-redhat-repo-latest.noarch.rpm

# Disable built-in PostgreSQL module (AlmaLinux 8/9)
sudo dnf -qy module disable postgresql

# Install PostgreSQL 15
sudo dnf install -y postgresql15-server postgresql15-contrib

# Initialize database
sudo /usr/pgsql-15/bin/postgresql-15-setup initdb

# Start and enable PostgreSQL
sudo systemctl start postgresql-15
sudo systemctl enable postgresql-15

# Verify status
sudo systemctl status postgresql-15
```

Expected: `active (running)`

### Step 9: Install Redis

```bash
# Install Redis
sudo dnf install redis -y

# Start and enable Redis
sudo systemctl start redis
sudo systemctl enable redis

# Verify status
sudo systemctl status redis
```

Expected: `active (running)`

**Configure Redis to listen on localhost:**

```bash
# Edit Redis config
sudo nano /etc/redis/redis.conf

# Find and verify these lines:
# bind 127.0.0.1 -::1
# protected-mode yes

# Save and exit (Ctrl+X, Y, Enter)

# Restart Redis
sudo systemctl restart redis
```

### Step 10: Install LDAP Client Libraries

```bash
# Install LDAP development libraries
sudo dnf install -y openldap-devel openldap-clients

# Verify
ldapsearch -V
```

---

## Code Deployment

### Step 11: Create Application User

**Don't run the application as root!**

```bash
# Create system user for the application
sudo useradd -r -m -d /opt/spg -s /bin/bash spgadmin

# Set password (optional, for SSH access)
sudo passwd spgadmin

# Verify user created
id spgadmin
```

### Step 12: Create Directory Structure

```bash
# Create application directory
sudo mkdir -p /opt/spg/platform

# Set ownership
sudo chown -R spgadmin:spgadmin /opt/spg

# Create log directory
sudo mkdir -p /var/log/spg
sudo chown -R spgadmin:spgadmin /var/log/spg
```

### Step 13: Deploy Application Code

**Option A: Using Git (Recommended)**

```bash
# Switch to spgadmin user
sudo su - spgadmin

# Clone repository
cd /opt/spg
git clone <YOUR_REPOSITORY_URL> platform

# Or if you have the code locally, copy it
# From your local machine:
# scp -r sharepoint-governance-platform spgadmin@server-ip:/opt/spg/platform
```

**Option B: Manual Copy with scp**

```bash
# From your development machine (where code exists):
cd /path/to/your/code
scp -r sharepoint-governance-platform/* spgadmin@server-ip:/opt/spg/platform/

# On the server, verify
sudo su - spgadmin
ls -la /opt/spg/platform
```

**Verify Directory Structure:**

```bash
cd /opt/spg/platform
ls -la
```

Expected output:
```
drwxr-xr-x  backend
drwxr-xr-x  frontend
drwxr-xr-x  docs
-rw-r--r--  .env.example
-rw-r--r--  docker-compose.yml
-rw-r--r--  README.md
```

---

## Database Setup

### Step 14: Configure PostgreSQL Authentication

```bash
# Switch to postgres user
sudo su - postgres

# Edit pg_hba.conf to allow password authentication
# Find the file location first
psql -c "SHOW hba_file;"
```

Output example: `/var/lib/pgsql/15/data/pg_hba.conf`

```bash
# Exit postgres user
exit

# Edit the file as root
sudo nano /var/lib/pgsql/15/data/pg_hba.conf
```

**Find these lines (near the bottom):**

```
# IPv4 local connections:
host    all             all             127.0.0.1/32            ident
# IPv6 local connections:
host    all             all             ::1/128                 ident
```

**Change to:**

```
# IPv4 local connections:
host    all             all             127.0.0.1/32            md5
# IPv6 local connections:
host    all             all             ::1/128                 md5
```

**Save and exit** (Ctrl+X, Y, Enter)

**Restart PostgreSQL:**

```bash
sudo systemctl restart postgresql-15
```

### Step 15: Create Database and User

```bash
# Switch to postgres user
sudo su - postgres

# Connect to PostgreSQL
psql
```

**In the PostgreSQL prompt:**

```sql
-- Create database
CREATE DATABASE spg_db;

-- Create user with password
CREATE USER spg_user WITH ENCRYPTED PASSWORD 'YourSecurePassword123!';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE spg_db TO spg_user;

-- Connect to new database
\c spg_db

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO spg_user;

-- Verify database created
\l

-- Exit
\q
```

**Exit postgres user:**

```bash
exit
```

**Test connection as spg_user:**

```bash
psql -U spg_user -h localhost -d spg_db
```

Enter password when prompted. If successful, you'll see `spg_db=>` prompt.

Type `\q` to exit.

---

## Configuration

### Step 16: Create .env File

```bash
# Switch to spgadmin user
sudo su - spgadmin

# Navigate to platform directory
cd /opt/spg/platform

# Copy example .env file
cp .env.example .env

# Edit the file
nano .env
```

### Step 17: Configure Database Connection

**In the .env file, find and update:**

```env
# Database
DATABASE_URL=postgresql://spg_user:YourSecurePassword123!@localhost:5432/spg_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

**Replace:**
- `spg_user` → PostgreSQL username (from Step 15)
- `YourSecurePassword123!` → PostgreSQL password (from Step 15)
- `localhost` → Database server (usually localhost)
- `5432` → PostgreSQL port
- `spg_db` → Database name (from Step 15)

### Step 18: Configure Redis Connection

```env
# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=300
```

Keep as-is unless Redis is on a different server.

### Step 19: Configure Microsoft 365 Integration

**You need Azure AD credentials.** See the [Configuration Guide](CONFIGURATION_GUIDE.md) or Windows guide Step 12 for detailed instructions on creating Azure AD App Registration.

**Update these values:**

```env
# Microsoft 365 Configuration
TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
CLIENT_ID=yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
CLIENT_SECRET=zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz
SHAREPOINT_SITE_URL=https://yourtenant.sharepoint.com
```

**To find these values:**

1. **Tenant ID** → Azure Portal → Azure AD → Overview → Directory (tenant) ID
2. **Client ID** → Azure Portal → App Registrations → Your App → Application (client) ID
3. **Client Secret** → Azure Portal → Your App → Certificates & secrets → New client secret → Copy Value
4. **SharePoint URL** → Your SharePoint root site (e.g., `https://contoso.sharepoint.com`)

### Step 20: Configure Active Directory / LDAP

**Finding LDAP server from Linux:**

```bash
# If domain is example.com, find domain controllers
nslookup -type=SRV _ldap._tcp.dc._msdcs.example.com

# Or test LDAP connection
ldapsearch -x -H ldap://dc01.example.com -b "dc=example,dc=com" -s base
```

**Update .env:**

```env
# Active Directory / LDAP
LDAP_SERVER=ldap://dc01.yourdomain.com:389
LDAP_BASE_DN=dc=yourdomain,dc=com
LDAP_BIND_DN=cn=svc_spg,ou=ServiceAccounts,dc=yourdomain,dc=com
LDAP_BIND_PASSWORD=<SERVICE_ACCOUNT_PASSWORD>
LDAP_USER_SEARCH_BASE=ou=Users,dc=yourdomain,dc=com
LDAP_GROUP_SEARCH_BASE=ou=Groups,dc=yourdomain,dc=com
```

**Replace:**
- `dc01.yourdomain.com` → Your AD domain controller hostname or IP
- `dc=yourdomain,dc=com` → Your domain's Base DN
- `cn=svc_spg,ou=ServiceAccounts,dc=yourdomain,dc=com` → Service account DN
- `<SERVICE_ACCOUNT_PASSWORD>` → Service account password
- Adjust OU paths based on your AD structure

### Step 21: Generate JWT Secret

```bash
# Generate secure random string
python3.11 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output (64-character string).

**Update .env:**

```env
# JWT Authentication
SECRET_KEY=<PASTE_YOUR_GENERATED_SECRET_HERE>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Step 22: Configure CORS and Networking

```env
# CORS (Frontend URLs)
CORS_ORIGINS=http://localhost:3000,http://<SERVER_IP>:3000
CORS_ALLOW_CREDENTIALS=true

# Email Notifications
EMAIL_FROM=noreply@yourdomain.com
EMAIL_ENABLED=true
```

**Replace:**
- `<SERVER_IP>` → Your server's IP address or hostname
- `noreply@yourdomain.com` → Valid email in your Microsoft 365 tenant

### Step 23: Save .env File

Press `Ctrl+X`, then `Y`, then `Enter` to save and exit nano.

**Secure the .env file:**

```bash
# Make .env readable only by owner
chmod 600 /opt/spg/platform/.env

# Verify
ls -la .env
```

Expected: `-rw------- 1 spgadmin spgadmin`

---

## Backend Setup

### Step 24: Create Python Virtual Environment

```bash
# Ensure you're spgadmin user
whoami  # Should show: spgadmin

# Navigate to backend directory
cd /opt/spg/platform/backend

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Your prompt should now show: (venv)
```

### Step 25: Upgrade pip

```bash
# Upgrade pip to latest
pip install --upgrade pip

# Verify
pip --version
```

### Step 26: Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

This takes 5-10 minutes. You'll see packages being downloaded and installed.

**Verify installation:**

```bash
pip list | grep -E "fastapi|uvicorn|sqlalchemy|psycopg2|pyotp"
```

You should see all these packages listed.

### Step 27: Run Database Migrations

```bash
# Still in backend directory with venv activated
cd /opt/spg/platform/backend
source venv/bin/activate

# Run migrations
alembic upgrade head
```

**Expected output:**

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial_schema
INFO  [alembic.runtime.migration] Running upgrade 001_initial_schema -> 002_add_two_factor
```

**If you see errors:**
- Verify PostgreSQL is running: `sudo systemctl status postgresql-15`
- Check DATABASE_URL in .env is correct
- Test manual connection: `psql -U spg_user -h localhost -d spg_db`

---

## Frontend Setup

### Step 28: Install Frontend Dependencies

```bash
# Stay as spgadmin user
# Navigate to frontend directory
cd /opt/spg/platform/frontend

# Install dependencies
npm install
```

This takes 5-10 minutes.

**Verify installation:**

```bash
npm list --depth=0 | grep -E "react|redux|mui"
```

### Step 29: Configure Frontend Environment

```bash
# Create frontend .env file
cd /opt/spg/platform/frontend
nano .env
```

**Add these lines:**

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_API_PREFIX=/api/v1
```

**For production (accessible from network):**

```env
REACT_APP_API_URL=http://<SERVER_IP>:8000
REACT_APP_API_PREFIX=/api/v1
```

Replace `<SERVER_IP>` with your server's IP address.

Save and exit (Ctrl+X, Y, Enter).

### Step 30: Build Frontend for Production

```bash
# Create optimized production build
cd /opt/spg/platform/frontend
npm run build
```

This creates a `build` directory with optimized static files.

**Verify build:**

```bash
ls -la build/
```

You should see `index.html`, `static/` directory, etc.

---

## Running the Application

### Step 31: Test Backend Server

```bash
# Navigate to backend
cd /opt/spg/platform/backend
source venv/bin/activate

# Start backend (test run)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Expected output:**

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Open another terminal and test:**

```bash
curl http://localhost:8000/health
```

Expected response: `{"status":"healthy","timestamp":"..."}`

**Stop the server:** Press `Ctrl+C`

### Step 32: Test Frontend Server

**Install serve (global static file server):**

```bash
sudo npm install -g serve
```

**Serve the built frontend:**

```bash
cd /opt/spg/platform/frontend
serve -s build -l 3000
```

**Test from another terminal:**

```bash
curl http://localhost:3000
```

You should see HTML output.

**Stop the server:** Press `Ctrl+C`

---

## SystemD Services

### Step 33: Create Backend SystemD Service

```bash
# Exit spgadmin user
exit

# Create service file as root
sudo nano /etc/systemd/system/spg-backend.service
```

**Paste this content:**

```ini
[Unit]
Description=SharePoint Governance Platform Backend API
After=network.target postgresql-15.service redis.service
Requires=postgresql-15.service redis.service

[Service]
Type=simple
User=spgadmin
Group=spgadmin
WorkingDirectory=/opt/spg/platform/backend
Environment="PATH=/opt/spg/platform/backend/venv/bin"
EnvironmentFile=/opt/spg/platform/.env
ExecStart=/opt/spg/platform/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Restart policy
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/var/log/spg/backend.log
StandardError=append:/var/log/spg/backend-error.log

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Save and exit (Ctrl+X, Y, Enter).

**Reload systemd and start service:**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Start backend service
sudo systemctl start spg-backend

# Enable auto-start on boot
sudo systemctl enable spg-backend

# Check status
sudo systemctl status spg-backend
```

Expected: `active (running)`

**View logs:**

```bash
sudo tail -f /var/log/spg/backend.log
```

Press `Ctrl+C` to exit.

### Step 34: Create Frontend SystemD Service

```bash
sudo nano /etc/systemd/system/spg-frontend.service
```

**Paste this content:**

```ini
[Unit]
Description=SharePoint Governance Platform Frontend Web Server
After=network.target spg-backend.service
Requires=spg-backend.service

[Service]
Type=simple
User=spgadmin
Group=spgadmin
WorkingDirectory=/opt/spg/platform/frontend
Environment="PATH=/usr/bin"
ExecStart=/usr/bin/serve -s build -l 3000

# Restart policy
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/var/log/spg/frontend.log
StandardError=append:/var/log/spg/frontend-error.log

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Save and exit.

**Start frontend service:**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Start frontend service
sudo systemctl start spg-frontend

# Enable auto-start on boot
sudo systemctl enable spg-frontend

# Check status
sudo systemctl status spg-frontend
```

**Verify both services are running:**

```bash
sudo systemctl status spg-backend spg-frontend
```

---

## Firewall Configuration

### Step 35: Open Required Ports

```bash
# Allow backend API port (8000)
sudo firewall-cmd --permanent --add-port=8000/tcp

# Allow frontend web port (3000)
sudo firewall-cmd --permanent --add-port=3000/tcp

# Allow HTTP (80) if using reverse proxy later
sudo firewall-cmd --permanent --add-service=http

# Allow HTTPS (443) if using SSL later
sudo firewall-cmd --permanent --add-service=https

# Reload firewall
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --list-all
```

Expected output should include:
```
ports: 8000/tcp 3000/tcp
services: http https
```

### Step 36: Test External Access

**From another machine on the network:**

```bash
# Test backend API
curl http://<SERVER_IP>:8000/health

# Test frontend (in browser)
# Open: http://<SERVER_IP>:3000
```

Replace `<SERVER_IP>` with your server's IP address.

---

## SSL/HTTPS Setup

### Step 37: Install Nginx (Optional but Recommended)

```bash
# Install Nginx
sudo dnf install nginx -y

# Start and enable
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Step 38: Configure Nginx Reverse Proxy

```bash
# Create Nginx config for SPG
sudo nano /etc/nginx/conf.d/spg.conf
```

**Paste this content:**

```nginx
# Backend API
upstream backend {
    server 127.0.0.1:8000;
}

# Frontend
upstream frontend {
    server 127.0.0.1:3000;
}

# Redirect HTTP to HTTPS (enable after SSL setup)
# server {
#     listen 80;
#     server_name spg.yourdomain.com;
#     return 301 https://$host$request_uri;
# }

# Main server block
server {
    listen 80;
    server_name spg.yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://backend/health;
        proxy_http_version 1.1;
    }
}
```

**Replace `spg.yourdomain.com` with your actual domain.**

Save and exit.

**Test and restart Nginx:**

```bash
# Test configuration
sudo nginx -t

# If OK, restart
sudo systemctl restart nginx
```

### Step 39: Install SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo dnf install certbot python3-certbot-nginx -y

# Obtain certificate (interactive)
sudo certbot --nginx -d spg.yourdomain.com

# Follow prompts:
# - Enter email address
# - Agree to terms
# - Choose whether to redirect HTTP to HTTPS (recommended: Yes)
```

Certbot will automatically update your Nginx config for HTTPS.

**Test auto-renewal:**

```bash
sudo certbot renew --dry-run
```

---

## SELinux Configuration

### Step 40: Configure SELinux Contexts (If Enforcing)

If you kept SELinux in enforcing mode:

```bash
# Allow Nginx to connect to network
sudo setsebool -P httpd_can_network_connect 1

# Set contexts for application directories
sudo semanage fcontext -a -t httpd_sys_content_t "/opt/spg/platform(/.*)?"
sudo restorecon -Rv /opt/spg/platform

# Allow custom ports
sudo semanage port -a -t http_port_t -p tcp 8000
sudo semanage port -a -t http_port_t -p tcp 3000
```

---

## Verification

### Step 41: Verify Services

```bash
# Check all services are running
sudo systemctl status postgresql-15
sudo systemctl status redis
sudo systemctl status spg-backend
sudo systemctl status spg-frontend
sudo systemctl status nginx
```

All should show `active (running)`.

### Step 42: Test Application

**Access the application:**

```bash
# Using server IP
http://<SERVER_IP>

# Or using domain (if configured)
http://spg.yourdomain.com
https://spg.yourdomain.com  # If SSL configured
```

**You should see the login page.**

### Step 43: Create First Admin User

```bash
# Connect to database
sudo su - postgres
psql -d spg_db
```

```sql
-- Insert admin user
INSERT INTO users (user_id, email, name, role, is_active)
VALUES (
    gen_random_uuid(),
    'admin@yourdomain.com',
    'System Administrator',
    'admin',
    true
);

-- Verify
SELECT email, name, role FROM users;

-- Exit
\q
exit
```

### Step 44: Test Login

1. Open application in browser
2. Try logging in with AD credentials
3. If successful, you'll see the dashboard

---

## Troubleshooting

### Backend Won't Start

**Check logs:**

```bash
sudo journalctl -u spg-backend -n 50  # Last 50 lines
sudo tail -f /var/log/spg/backend.log
sudo tail -f /var/log/spg/backend-error.log
```

**Common issues:**

**PostgreSQL connection failed:**

```bash
# Verify PostgreSQL is running
sudo systemctl status postgresql-15

# Test connection manually
psql -U spg_user -h localhost -d spg_db

# Check pg_hba.conf allows md5 authentication
sudo cat /var/lib/pgsql/15/data/pg_hba.conf | grep md5
```

**Permission denied errors:**

```bash
# Verify ownership
ls -la /opt/spg/platform

# Fix ownership if needed
sudo chown -R spgadmin:spgadmin /opt/spg/platform
```

**Module not found:**

```bash
# Reinstall dependencies
sudo su - spgadmin
cd /opt/spg/platform/backend
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Won't Start

**Check logs:**

```bash
sudo journalctl -u spg-frontend -n 50
sudo tail -f /var/log/spg/frontend.log
```

**Rebuild if needed:**

```bash
sudo su - spgadmin
cd /opt/spg/platform/frontend
npm run build
```

### Cannot Access from Network

**Check firewall:**

```bash
sudo firewall-cmd --list-all
```

Ensure ports 80, 443, 3000, 8000 are open.

**Check SELinux:**

```bash
# If enforcing, check denials
sudo ausearch -m avc -ts recent
```

**Test connectivity:**

```bash
# From another machine
telnet <SERVER_IP> 8000
telnet <SERVER_IP> 3000
```

### LDAP Connection Fails

**Test LDAP from server:**

```bash
# Test connection
ldapsearch -x -H ldap://dc01.yourdomain.com -b "dc=yourdomain,dc=com" -D "cn=svc_spg,ou=ServiceAccounts,dc=yourdomain,dc=com" -W

# Enter bind password when prompted
```

If fails:
- Verify LDAP server is reachable: `ping dc01.yourdomain.com`
- Check firewall allows port 389
- Verify bind DN and password are correct

---

## Maintenance Commands

### View Service Status

```bash
# All SPG services
sudo systemctl status spg-backend spg-frontend

# With logs
sudo journalctl -u spg-backend -f
sudo journalctl -u spg-frontend -f
```

### Restart Services

```bash
# Restart backend
sudo systemctl restart spg-backend

# Restart frontend
sudo systemctl restart spg-frontend

# Restart all
sudo systemctl restart spg-backend spg-frontend nginx
```

### Update Application

```bash
# Switch to spgadmin
sudo su - spgadmin

# Pull latest code
cd /opt/spg/platform
git pull

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# Update frontend
cd ../frontend
npm install
npm run build

# Exit spgadmin
exit

# Restart services
sudo systemctl restart spg-backend spg-frontend
```

### Backup Database

```bash
# Create backup
sudo su - postgres
pg_dump -U spg_user spg_db > /tmp/spg_backup_$(date +%Y%m%d).sql
exit

# Move to safe location
sudo mv /tmp/spg_backup_* /opt/backups/
```

### Restore Database

```bash
sudo su - postgres
psql -U spg_user -d spg_db < /opt/backups/spg_backup_20251205.sql
exit
```

### View Logs

```bash
# Backend logs
sudo tail -f /var/log/spg/backend.log

# Frontend logs
sudo tail -f /var/log/spg/frontend.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# PostgreSQL logs
sudo tail -f /var/lib/pgsql/15/data/log/postgresql-*.log
```

---

## Security Hardening

### Firewall Rules (Stricter)

```bash
# Remove direct backend/frontend ports if using Nginx
sudo firewall-cmd --permanent --remove-port=8000/tcp
sudo firewall-cmd --permanent --remove-port=3000/tcp

# Keep only HTTP/HTTPS
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https

# Reload
sudo firewall-cmd --reload
```

### Configure fail2ban

```bash
# Install fail2ban
sudo dnf install fail2ban -y

# Create jail for Nginx
sudo nano /etc/fail2ban/jail.d/nginx.conf
```

```ini
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
```

```bash
sudo systemctl start fail2ban
sudo systemctl enable fail2ban
```

### Automatic Security Updates

```bash
# Install dnf-automatic
sudo dnf install dnf-automatic -y

# Configure
sudo nano /etc/dnf/automatic.conf
```

Set:
```ini
apply_updates = yes
```

```bash
sudo systemctl start dnf-automatic.timer
sudo systemctl enable dnf-automatic.timer
```

---

## Appendix

### A. Directory Structure

```
/opt/spg/platform/
├── backend/
│   ├── venv/
│   ├── app/
│   ├── alembic/
│   └── requirements.txt
├── frontend/
│   ├── build/
│   ├── node_modules/
│   ├── src/
│   └── package.json
├── docs/
└── .env

/var/log/spg/
├── backend.log
├── backend-error.log
├── frontend.log
└── frontend-error.log
```

### B. Service Management

```bash
# Start
sudo systemctl start spg-backend
sudo systemctl start spg-frontend

# Stop
sudo systemctl stop spg-backend
sudo systemctl stop spg-frontend

# Restart
sudo systemctl restart spg-backend
sudo systemctl restart spg-frontend

# Status
sudo systemctl status spg-backend
sudo systemctl status spg-frontend

# Enable (auto-start on boot)
sudo systemctl enable spg-backend
sudo systemctl enable spg-frontend

# Disable
sudo systemctl disable spg-backend
sudo systemctl disable spg-frontend

# View logs
sudo journalctl -u spg-backend -f
sudo journalctl -u spg-frontend -f
```

### C. Default Ports

| Service | Port | Access |
|---------|------|--------|
| Frontend | 3000 | Internal (proxied by Nginx) |
| Backend API | 8000 | Internal (proxied by Nginx) |
| Nginx HTTP | 80 | External |
| Nginx HTTPS | 443 | External |
| PostgreSQL | 5432 | localhost only |
| Redis | 6379 | localhost only |
| LDAP | 389 | Outbound to AD server |

### D. Useful Commands

```bash
# Check port usage
sudo ss -tulpn | grep -E "3000|8000|80|443"

# Check disk space
df -h

# Check memory usage
free -h

# Check CPU usage
top

# Check system logs
sudo journalctl -xe

# Check active connections
sudo netstat -an | grep ESTABLISHED

# Test database connection
psql -U spg_user -h localhost -d spg_db -c "SELECT version();"

# Test Redis connection
redis-cli ping
```

---

## Production Deployment Checklist

- [ ] Change all default passwords
- [ ] Configure SSL/TLS with valid certificates
- [ ] Update CORS_ORIGINS to production domain
- [ ] Set DEBUG=false in .env
- [ ] Configure automated database backups
- [ ] Set up log rotation
- [ ] Configure SELinux in enforcing mode
- [ ] Enable firewall with minimal ports
- [ ] Install and configure fail2ban
- [ ] Set up monitoring (email alerts)
- [ ] Document all credentials securely
- [ ] Create encrypted backup of .env file
- [ ] Test disaster recovery procedures
- [ ] Configure automatic security updates

---

**End of AlmaLinux Deployment Guide**

For additional support, refer to the main documentation or contact your system administrator.
