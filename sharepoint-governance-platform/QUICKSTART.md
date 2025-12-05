# SharePoint Governance Platform - Quick Start

## 🚀 Getting Started in 5 Minutes

### Prerequisites
- Docker & Docker Compose
- Microsoft 365 tenant with admin access
- Azure AD application registration

### Step 1: Configuration (2 minutes)

```bash
# Clone the repository
cd sharepoint-governance-platform

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Required Variables**:
```bash
# Microsoft Graph API
GRAPH_CLIENT_ID=your-client-id
GRAPH_CLIENT_SECRET=your-secret
GRAPH_TENANT_ID=your-tenant-id

# Database
POSTGRES_SERVER=postgres
POSTGRES_DB=sharepoint_gov
POSTGRES_USER=admin
POSTGRES_PASSWORD=change-me-in-production

# Redis
REDIS_URL=redis://redis:6379/0

# JWT Secrets (generate random strings)
SECRET_KEY=generate-random-64-char-string
JWT_SECRET_KEY=generate-another-random-string

# AD/LDAP
LDAP_SERVER=ldap://your-ad-server
LDAP_BASE_DN=dc=company,dc=com
```

### Step 2: Start Services (1 minute)

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps
```

### Step 3: Initialize Database (1 minute)

```bash
# Run database migrations
docker-compose exec backend alembic upgrade head

# Verify
docker-compose exec backend alembic current
```

### Step 4: Access the Platform (1 minute)

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/v1/docs
- **Metrics**: http://localhost:9090 (Prometheus)

### Step 5: First Login

1. Navigate to http://localhost:3000
2. Login with your AD credentials
3. System will:
   - Authenticate via AD/LDAP
   - Assign role based on group membership
   - Issue JWT token
   - Redirect to dashboard

---

## 📊 Key Features

### For Site Owners
- View owned sites and health scores
- Complete quarterly access reviews
- See pending actions and certifications

### For Administrators
- Monitor all SharePoint sites
- Trigger site discovery
- Review anomaly detections
- Generate compliance reports

### For Executives
- View governance dashboards
- Access Power BI reports
- Review compliance metrics
- Export executive summaries

---

## 🔧 Common Operations

### Trigger Site Discovery
```bash
curl -X POST http://localhost:8000/api/v1/sites/discover \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Export Audit Logs
```bash
curl "http://localhost:8000/api/v1/audit/logs/export?format=csv" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  > audit_logs.csv
```

### Generate Compliance Report
```bash
curl "http://localhost:8000/api/v1/audit/compliance-report?report_type=gdpr" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📖 API Quick Reference

### Authentication
```bash
# Login
POST /api/v1/auth/login
Body: {"username": "user@domain.com", "password": "***"}

# Refresh Token
POST /api/v1/auth/refresh
Body: {"refresh_token": "***"}
```

### Sites
```bash
# List Sites
GET /api/v1/sites?skip=0&limit=10

# Site Health
GET /api/v1/sites/{site_id}/health

# Access Matrix
GET /api/v1/sites/{site_id}/access
```

### Access Reviews
```bash
# List Reviews
GET /api/v1/access-reviews?status=pending

# Update Decision
PUT /api/v1/access-reviews/{cycle_id}/items/{item_id}
Body: {"access_status": "approved", "reviewer_comments": "OK"}

# Certify Review
POST /api/v1/access-reviews/{cycle_id}/certify
```

### Analytics (Phase 3)
```bash
# Anomalies
GET /api/v3/analytics/anomalies?days=30

# Risk Score
GET /api/v3/analytics/sites/{site_id}/risk-score

# Power BI Dataset
GET /api/v3/powerbi/datasets/sites
```

---

## 🔍 Troubleshooting

### Backend Won't Start
```bash
# Check logs
docker-compose logs backend

# Common issues:
# 1. Database not ready - wait 30 seconds
# 2. Missing environment variables - check .env
# 3. Port conflict - change ports in docker-compose.yml
```

### Frontend Can't Connect
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check frontend logs
docker-compose logs frontend

# Rebuild if needed
docker-compose up --build frontend
```

### Authentication Failing
```bash
# Test AD/LDAP connection
docker-compose exec backend python -c "
from app.core.auth import authenticate_with_ad
result = authenticate_with_ad('user@domain.com', 'password')
print(result)
"

# Check logs
docker-compose logs backend | grep -i "auth"
```

---

## 📚 Next Steps

1. **Configure Background Jobs**  
   Jobs run automatically. Check schedule in `backend/app/tasks/scheduler.py`

2. **Set Up Monitoring**  
   Access Prometheus at http://localhost:9090  
   Configure Grafana dashboards (optional)

3. **Create Users**  
   Users are auto-created on first login from AD  
   Or run: `docker-compose exec backend python scripts/seed_users.py`

4. **Power BI Setup**  
   Import datasets from `/api/v3/powerbi/datasets/*`  
   Use provided connection string for Direct Query

5. **Review Documentation**  
   - Full docs: `FINAL_STATUS.md`
   - Architecture: `brain/architecture_review.md`
   - Walkthrough: `brain/walkthrough.md`

---

## 🆘 Support

### Documentation
- **README**: Quick start and overview
- **FINAL_STATUS**: Complete project documentation
- **API Docs**: http://localhost:8000/api/v1/docs

### Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Health Checks
```bash
# Backend
curl http://localhost:8000/health

# Database
docker-compose exec postgres pg_isready

# Redis
docker-compose exec redis redis-cli ping
```

---

## 📦 Production Deployment

For production deployment:
1. Use `docker-compose.prod.yml`
2. Enable HTTPS (reverse proxy/load balancer)
3. Set strong secrets in `.env`
4. Configure backup automation
5. Set up monitoring alerts
6. Review security checklist in `FINAL_STATUS.md`

---

**Platform Version**: 3.0.0  
**Last Updated**: December 5, 2025  
**Status**: Production Ready ✅
