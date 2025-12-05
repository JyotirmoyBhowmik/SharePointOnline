# SharePoint Governance Platform - Deployment Checklist

## Prerequisites to Install

### 1. Docker & Docker Compose
**Required for**: Running all services (Backend, Database, Redis, Frontend)

**Check if installed**:
```bash
docker --version
docker-compose --version
```

**Install on Ubuntu/Debian**:
```bash
# Update package index
sudo apt-get update

# Install dependencies
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker's GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to docker group (to run without sudo)
sudo usermod -aG docker $USER

# Log out and log back in for group to take effect
```

**Install on Windows**:
- Download Docker Desktop from https://www.docker.com/products/docker-desktop
- Install and restart

**Install on macOS**:
- Download Docker Desktop from https://www.docker.com/products/docker-desktop
- Install and start

**Verify**:
```bash
docker run hello-world
docker-compose --version
```

---

### 2. Git
**Required for**: Cloning repository, version control

**Check if installed**:
```bash
git --version
```

**Install**:
```bash
# Ubuntu/Debian
sudo apt-get install -y git

# macOS (with Homebrew)
brew install git

# Windows
# Download from https://git-scm.com/download/win
```

---

### 3. Node.js & npm (Optional)
**Required for**: Frontend development only (if building UI)

**Check if installed**:
```bash
node --version
npm --version
```

**Install**:
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# macOS (with Homebrew)
brew install node

# Windows
# Download from https://nodejs.org/
```

**Verify**:
```bash
node --version  # Should be v18.x or higher
npm --version   # Should be v9.x or higher
```

---

### 4. Python 3.11+ (Optional)
**Required for**: Running tests locally, development outside Docker

**Check if installed**:
```bash
python3 --version
```

**Install**:
```bash
# Ubuntu/Debian
sudo apt-get install -y python3.11 python3-pip python3.11-venv

# macOS (with Homebrew)
brew install python@3.11

# Windows
# Download from https://www.python.org/downloads/
```

---

## Quick Deployment (Using Automated Script)

### Option 1: Automated Deployment

```bash
cd /home/genai/Documents/SharePointOnline/sharepoint-governance-platform

# Run deployment script
./deploy.sh
```

The script will:
- ✅ Check and install prerequisites
- ✅ Configure environment
- ✅ Build Docker images
- ✅ Start all services
- ✅ Run database migrations
- ✅ Verify deployment

---

## Manual Deployment Steps

### Step 1: Clone Repository (if not already done)
```bash
cd /home/genai/Documents/SharePointOnline
git clone https://github.com/JyotirmoyBhowmik/SharePointOnline.git
cd SharePointOnline/sharepoint-governance-platform
```

### Step 2: Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit with your credentials
nano .env
```

**Required Credentials**:
```bash
# Microsoft Graph API (from Azure AD App Registration)
GRAPH_CLIENT_ID=your-client-id
GRAPH_CLIENT_SECRET=your-secret
GRAPH_TENANT_ID=your-tenant-id

# Database
POSTGRES_SERVER=postgres
POSTGRES_DB=sharepoint_gov
POSTGRES_USER=admin
POSTGRES_PASSWORD=YourStrongPassword123!

# Redis
REDIS_URL=redis://redis:6379/0

# JWT Secrets (generate random strings)
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# AD/LDAP
LDAP_SERVER=ldap://your-ad-server.company.com
LDAP_BASE_DN=dc=company,dc=com
LDAP_BIND_DN=cn=service,dc=company,dc=com
LDAP_BIND_PASSWORD=service-password
```

### Step 3: Build Docker Images
```bash
docker-compose build
```

This will build:
- Backend API (FastAPI)
- Frontend (React)
- PostgreSQL database
- Redis cache

**Expected output**: "Successfully tagged sharepoint-governance-platform_backend:latest"

### Step 4: Start Services
```bash
docker-compose up -d
```

**Verify all services are running**:
```bash
docker-compose ps
```

You should see:
- `backend` - running on port 8000
- `frontend` - running on port 3000
- `postgres` - running on port 5432
- `redis` - running on port 6379

### Step 5: Database Migration
```bash
# Wait for PostgreSQL to be ready
docker-compose exec postgres pg_isready

# Run migrations
docker-compose exec backend alembic upgrade head
```

**Verify migration**:
```bash
docker-compose exec backend alembic current
```

### Step 6: Verify Deployment
```bash
# Test backend health
curl http://localhost:8000/health

# Expected output:
# {
#   "status": "healthy",
#   "timestamp": "2025-12-05T...",
#   "components": {
#     "database": {"status": "healthy"},
#     "cache": {"status": "healthy"},
#     "scheduler": {"status": "healthy"}
#   }
# }

# Access API documentation
xdg-open http://localhost:8000/api/v1/docs  # Linux
# or open http://localhost:8000/api/v1/docs in browser
```

---

## Testing the Deployment

### 1. Test Authentication
```bash
# Test login endpoint
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@company.com",
    "password": "your-password"
  }'

# Expected: JWT token in response
```

### 2. Test Site Discovery
```bash
# Get token from login response
TOKEN="your-jwt-token"

# Trigger site discovery
curl -X POST http://localhost:8000/api/v1/sites/discover \
  -H "Authorization: Bearer $TOKEN"

# Check logs
docker-compose logs -f backend
```

### 3. View Sites
```bash
curl http://localhost:8000/api/v1/sites \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Frontend Access
Open browser to http://localhost:3000
- Login with AD credentials
- View dashboard
- Navigate through features

---

## Monitoring Deployment

### Start Monitoring Stack (Optional)
```bash
cd monitoring
docker-compose -f docker-compose-monitoring.yml up -d
```

**Access**:
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin_change_me)
- **Alertmanager**: http://localhost:9093

---

## Troubleshooting

### Services Won't Start
```bash
# Check logs
docker-compose logs backend
docker-compose logs postgres

# Common issues:
# 1. Port already in use
sudo lsof -i :8000  # Check what's using port 8000
sudo lsof -i :5432  # Check PostgreSQL port

# 2. Insufficient memory
docker system prune -a  # Clean up Docker
```

### Database Connection Errors
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Wait for ready
docker-compose exec postgres pg_isready

# Check credentials in .env
cat .env | grep POSTGRES
```

### Frontend Build Fails
```bash
cd frontend

# Install dependencies
npm install

# Build manually
npm run build

# Or run in development
npm run dev
```

---

## Next Steps After Deployment

1. **Run E2E Tests** (See TESTING_GUIDE.md):
   ```bash
   cd backend
   pytest tests/test_api.py -v
   ```

2. **Configure Background Jobs**:
   - Jobs start automatically
   - Check scheduler: `docker-compose logs backend | grep scheduler`

3. **Set Up Monitoring**:
   - Import Grafana dashboards
   - Configure alert notifications

4. **Security Hardening**:
   - Change default passwords
   - Enable HTTPS (use reverse proxy)
   - Configure firewall rules

5. **Production Deployment**:
   - Use `docker-compose.prod.yml`
   - Set up load balancer
   - Configure backup automation

---

## Uninstalling / Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove images
docker rmi sharepoint-governance-platform_backend
docker rmi sharepoint-governance-platform_frontend
```

---

## Getting Help

- **User Manual**: USER_MANUAL.md
- **Runbook**: RUNBOOK.md
- **Testing Guide**: TESTING_GUIDE.md
- **API Docs**: http://localhost:8000/api/v1/docs

**Support**: sharepoint-gov-support@company.com
