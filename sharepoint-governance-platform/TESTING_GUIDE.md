# SharePoint Governance Platform - Testing Guide

## Overview

This guide provides procedures for testing the SharePoint Governance Platform to ensure all features work correctly before production deployment.

---

## Test Environment Setup

### Prerequisites

```bash
# 1. Clone repository
git clone <repository-url>
cd sharepoint-governance-platform

# 2. Configure test environment
cp .env.example .env.test
# Edit .env.test with test credentials

# 3. Start test environment
docker-compose -f docker-compose.test.yml up -d

# 4. Run database migrations
docker-compose exec backend alembic upgrade head

# 5. Seed test data
docker-compose exec backend python scripts/seed_test_data.py
```

---

## Unit Testing

### Backend Unit Tests

```bash
# Run all unit tests
cd backend
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html tests/

# Run specific test file
pytest tests/test_auth.py -v

# Run specific test
pytest tests/test_auth.py::test_create_access_token -v
```

**Coverage Target**: >80%

**Test Categories**:
- Authentication (JWT, AD/LDAP)
- Services (site discovery, audit sync, access reviews)
- API endpoints (all 42+ endpoints)
- Database models
- Background jobs

### Frontend Unit Tests

```bash
cd frontend
npm test

# With coverage
npm test -- --coverage

# Watch mode
npm test -- --watch
```

---

## Integration Testing

### API Integration Tests

**Test Suite**: `backend/tests/test_api.py`

```bash
# Run API integration tests
pytest tests/test_api.py -v

# Test specific endpoint category
pytest tests/test_api.py::TestSitesAPI -v
```

**Test Scenarios**:
1. **Authentication Flow**
   - Login with valid credentials
   - Login with invalid credentials
   - Token refresh
   - Logout

2. **Site Management**
   - List sites with pagination
   - Get site details
   - Trigger site discovery
   - View access matrix

3. **Access Reviews**
   - List pending reviews
   - Update review decisions
   - Certify review
   - Check overdue reviews

4. **Audit Logs**
   - Query audit logs with filters
   - Export logs to CSV/JSON
   - Generate compliance reports

5. **Storage & Versioning**
   - Get storage summary
   - Get version recommendations
   - Trigger version cleanup

---

## End-to-End Testing

### Manual Test Scripts

#### Test Script 1: Site Owner Workflow

**Objective**: Verify complete site owner experience

**Steps**:
1. ✅ Login as site owner
2. ✅ View "My Sites" dashboard
3. ✅ Click on a site to view details
4. ✅ View access matrix for the site
5. ✅ Navigate to "Access Reviews"
6. ✅ Open a pending review
7. ✅ Review and approve/revoke users
8. ✅ Certify the review
9. ✅ Verify review status updated to "Completed"
10. ✅ Logout

**Expected Result**: All steps complete successfully, review marked as certified

#### Test Script 2: Administrator Workflow

**Objective**: Verify admin operations

**Steps**:
1. ✅ Login as administrator
2. ✅ View admin dashboard with system metrics
3. ✅ Navigate to "Sites" → Trigger site discovery
4. ✅ Wait for discovery to complete (monitor logs)
5. ✅ Verify new/updated sites appear
6. ✅ Navigate to "Storage" → View storage analytics
7. ✅ Select a library → Trigger version cleanup
8. ✅ Navigate to "Recycle Bin" → View bin summary
9. ✅ Restore an item from recycle bin
10. ✅ Navigate to "Users" → Trigger AD sync
11. ✅ Logout

**Expected Result**: All admin operations complete successfully

#### Test Script 3: Compliance Officer Workflow

**Objective**: Verify compliance features

**Steps**:
1. ✅ Login as compliance officer
2. ✅ Navigate to "Audit Logs"
3. ✅ Search logs with filters (date range, user, operation)
4. ✅ Export audit logs to CSV
5. ✅ Navigate to "Anomalies"
6. ✅ View detected anomalies
7. ✅ Mark an anomaly as "Confirmed" or "False Positive"
8. ✅ Navigate to "Compliance Reports"
9. ✅ Generate GDPR compliance report (PDF)
10. ✅ Generate ISO 27001 audit report
11. ✅ Logout

**Expected Result**: Reports generated successfully with correct data

#### Test Script 4: Background Jobs

**Objective**: Verify scheduled background jobs

**Steps**:
1. ✅ Verify site discovery job is scheduled
   ```bash
   docker-compose exec backend python -c "
   from app.tasks.scheduler import scheduler
   jobs = scheduler.get_jobs()
   print([j.name for j in jobs])
   "
   ```
2. ✅ Manually trigger site discovery job
3. ✅ Check logs for successful execution
4. ✅ Verify audit sync job runs
5. ✅ Verify user sync job runs
6. ✅ Check database for new/updated records

**Expected Result**: All 4 background jobs execute successfully

---

## Performance Testing

### Load Testing with Locust

**Install Locust**:
```bash
pip install locust
```

**Create Load Test** (`tests/locustfile.py`):
```python
from locust import HttpUser, task, between

class GovernanceUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login
        response = self.client.post("/api/v1/auth/login", json={
            "username": "test@domain.com",
            "password": "password"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def list_sites(self):
        self.client.get("/api/v1/sites", headers=self.headers)
    
    @task(2)
    def view_dashboard(self):
        self.client.get("/api/v1/dashboard/overview", headers=self.headers)
    
    @task(1)
    def list_reviews(self):
        self.client.get("/api/v1/access-reviews", headers=self.headers)
```

**Run Load Test**:
```bash
locust -f tests/locustfile.py --host=http://localhost:8000

# Open browser to http://localhost:8089
# Configure: 100 users, 10 users/second spawn rate
# Run for 5 minutes
```

**Performance Targets**:
- API Response Time: p95 < 500ms, p99 < 2s
- Error Rate: < 1%
- Throughput: > 100 requests/second
- Database Connections: < 80% of max

---

## Security Testing

### Automated Security Scans

**Bandit (Python Security)**:
```bash
cd backend
bandit -r app/ -f json -o security_report.json
```

**Safety (Dependency Vulnerabilities)**:
```bash
cd backend
safety check --json
```

**OWASP ZAP (Web Application Scan)**:
```bash
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:8000/api/v1/docs
```

### Manual Security Tests

#### Test 1: Authentication & Authorization

**Test Cases**:
1. ✅ Attempt login with invalid credentials → Should fail
2. ✅ Attempt to access protected endpoint without token → Should return 401
3. ✅ Attempt to access admin endpoint as site owner → Should return 403
4. ✅ Use expired token → Should return 401
5. ✅ SQL injection in login form → Should be blocked
6. ✅ XSS in input fields → Should be sanitized

#### Test 2: API Security

**Test Cases**:
1. ✅ CORS headers properly set
2. ✅ Rate limiting enforced (if configured)
3. ✅ Sensitive data not exposed in error messages
4. ✅ HTTPS enforced in production
5. ✅ JWT signature validation
6. ✅ Password hashing (bcrypt)

#### Test 3: Data Protection

**Test Cases**:
1. ✅ Passwords never logged
2. ✅ JWT secrets not exposed
3. ✅ Database credentials secured
4. ✅ API keys encrypted at rest
5. ✅ Audit logs capture all sensitive operations

---

## Regression Testing

### Release Checklist

Before each release, run full regression suite:

**Phase 1 Features**:
- [ ] Authentication (login, logout, token refresh)
- [ ] Site discovery and classification
- [ ] Access reviews (create, update, certify)
- [ ] Audit log querying and export
- [ ] Background jobs execution

**Phase 2 Features**:
- [ ] Version management and cleanup
- [ ] Storage analytics and recommendations
- [ ] Recycle bin management
- [ ] Retention policy sync and exclusions
- [ ] PDF/Excel report generation

**Phase 3 Features**:
- [ ] AI anomaly detection
- [ ] Risk score calculation
- [ ] Power BI dataset exports
- [ ] Multi-tenant management
- [ ] Compliance reports (GDPR, ISO 27001, SOX)

**Infrastructure**:
- [ ] Health check endpoint
- [ ] Prometheus metrics
- [ ] Database migrations
- [ ] Docker builds
- [ ] CI/CD pipeline

---

## Test Data Management

### Seeding Test Data

**Create Test Script** (`scripts/seed_test_data.py`):
```python
from app.db.session import SessionLocal
from app.models import User, SharePointSite, AccessReviewCycle
from datetime import datetime, timedelta

db = SessionLocal()

# Create test users
users = [
    User(email="admin@test.com", full_name="Admin User", role="admin"),
    User(email="owner@test.com", full_name="Site Owner", role="site_owner"),
    User(email="auditor@test.com", full_name="Auditor", role="auditor"),
]
db.add_all(users)

# Create test sites
sites = [
    SharePointSite(
        name="Test Site 1",
        site_url="https://contoso.sharepoint.com/sites/test1",
        classification="team_connected",
        storage_used_mb=5000,
        storage_quota_mb=25600
    ),
    SharePointSite(
        name="Test Site 2",
        site_url="https://contoso.sharepoint.com/sites/test2",
        classification="communication",
        storage_used_mb=15000,
        storage_quota_mb=25600
    ),
]
db.add_all(sites)
db.commit()

print("Test data seeded successfully")
```

**Run Seed Script**:
```bash
docker-compose exec backend python scripts/seed_test_data.py
```

### Cleanup Test Data

```bash
docker-compose exec backend python scripts/cleanup_test_data.py
```

---

## Continuous Integration Testing

### GitHub Actions Workflow

Tests run automatically on every pull request:

1. **Linting** (flake8, black, mypy)
2. **Unit Tests** (pytest with coverage)
3. **Security Scan** (bandit, safety)
4. **Docker Build** (verify containers build)
5. **Integration Tests** (API tests)

**View Results**:
- GitHub Actions tab in repository
- Coverage reports in PR comments

---

## Test Reporting

### Generate Test Report

```bash
# Run tests with HTML report
pytest --html=report.html --self-contained-html

# With coverage
pytest --cov=app --cov-report=html --html=report.html
```

**Report Includes**:
- Test execution time
- Pass/fail status
- Code coverage percentage
- Failed test details with stack traces

---

## Troubleshooting Tests

### Common Issues

**Issue**: Tests fail with database connection error  
**Solution**:
```bash
# Ensure database is running
docker-compose exec postgres pg_isready

# Recreate test database
docker-compose exec postgres psql -U admin -c "DROP DATABASE IF EXISTS test_db;"
docker-compose exec postgres psql -U admin -c "CREATE DATABASE test_db;"
```

**Issue**: Flaky tests (intermittent failures)  
**Solution**: Add retries or increase timeouts
```python
@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_api_endpoint():
    # Test code
    pass
```

**Issue**: Tests pass locally but fail in CI  
**Solution**: Check environment differences (Python version, dependencies, timing)

---

## Test Coverage Goals

| Component | Target Coverage |
|-----------|----------------|
| Backend Services | >85% |
| API Endpoints | >90% |
| Database Models | >80% |
| Authentication | >95% |
| Frontend Components | >70% |

**Overall Target**: >80% code coverage

---

**Document Version**: 1.0  
**Last Updated**: December 5, 2025  
**Maintained By**: QA Team
