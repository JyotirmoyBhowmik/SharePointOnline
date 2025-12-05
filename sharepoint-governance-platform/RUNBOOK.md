# SharePoint Governance Platform - Operations Runbook

## Table of Contents
1. [Common Operations](#common-operations)
2. [Troubleshooting](#troubleshooting)
3. [Backup & Recovery](#backup--recovery)
4. [Incident Response](#incident-response)
5. [Monitoring & Alerts](#monitoring--alerts)

---

## Common Operations

### Starting the Platform

```bash
# Development
docker-compose up -d

# Production
docker stack deploy -c docker-compose.prod.yml sharepoint-gov

# Check status
docker-compose ps  # or docker service ls for swarm
```

### Stopping the Platform

```bash
# Development
docker-compose down

# Production (graceful)
docker stack rm sharepoint-gov

# Emergency stop
docker stop $(docker ps -q)
```

### Database Migrations

```bash
# Check current version
docker-compose exec backend alembic current

# Upgrade to latest
docker-compose exec backend alembic upgrade head

# Downgrade one version
docker-compose exec backend alembic downgrade -1

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"
```

### Manual Background Jobs

```bash
# Trigger site discovery
curl -X POST http://localhost:8000/api/v1/sites/discover \
  -H "Authorization: Bearer $TOKEN"

# Sync retention policies
curl -X POST http://localhost:8000/api/v2/retention/sync \
  -H "Authorization: Bearer $TOKEN"

# Check job status
docker-compose exec backend python -c "
from app.tasks.scheduler import scheduler
print(scheduler.get_jobs())
"
```

### Accessing Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend

# Search logs
docker-compose logs backend | grep ERROR

# Export logs
docker-compose logs --no-color backend > backend.log
```

---

## Troubleshooting

### Backend Won't Start

**Symptoms**: Backend container exits immediately

**Diagnosis**:
```bash
# Check logs
docker-compose logs backend

# Common issues:
# 1. Database not ready
# 2. Missing environment variables
# 3. Port already in use
```

**Resolution**:
```bash
# 1. Wait for database
docker-compose up -d postgres
sleep 30
docker-compose up -d backend

# 2. Verify .env file
cat .env | grep -E "(POSTGRES|REDIS|SECRET)"

# 3. Change port
# Edit docker-compose.yml, change "8000:8000" to "8001:8000"
```

### Database Connection Errors

**Symptoms**: "could not connect to server", "connection refused"

**Diagnosis**:
```bash
# Test database
docker-compose exec postgres pg_isready

# Check connectivity
docker-compose exec backend python -c "
from app.db.session import SessionLocal
db = SessionLocal()
print('Connected:', db.execute('SELECT 1').scalar() == 1)
"
```

**Resolution**:
```bash
# Restart database
docker-compose restart postgres

# Check credentials in .env
docker-compose exec postgres psql -U admin -d sharepoint_gov -c "SELECT version();"

# Recreate database (WARNING: data loss)
docker-compose down -v
docker-compose up -d postgres
docker-compose exec backend alembic upgrade head
```

### Authentication Failures

**Symptoms**: "Authentication failed", "Invalid credentials"

**Diagnosis**:
```bash
# Test AD/LDAP connection
docker-compose exec backend python -c "
from app.core.auth import authenticate_with_ad
result = authenticate_with_ad('user@domain.com', 'password')
print('Result:', result)
"

# Check logs
docker-compose logs backend | grep -i "auth"
```

**Resolution**:
```bash
# Verify LDAP settings in .env
echo $LDAP_SERVER
echo $LDAP_BASE_DN

# Test LDAP connectivity
docker-compose exec backend ldapsearch -x -H $LDAP_SERVER -b $LDAP_BASE_DN

# Regenerate JWT secret
# Update JWT_SECRET_KEY in .env
docker-compose restart backend
```

### High CPU/Memory Usage

**Symptoms**: Slow responses, container restarts

**Diagnosis**:
```bash
# Check resource usage
docker stats

# Top processes
docker-compose exec backend top

# Memory hogs
docker-compose exec backend ps aux --sort=-%mem | head
```

**Resolution**:
```bash
# Increase limits in docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

# Restart with new limits
docker-compose up -d

# Scale horizontally (swarm only)
docker service scale sharepoint-gov_backend=3
```

### Background Jobs Not Running

**Symptoms**: No site discovery, audit sync failing

**Diagnosis**:
```bash
# Check scheduler
docker-compose exec backend python -c "
from app.tasks.scheduler import scheduler
print('Running:', scheduler.running)
print('Jobs:', scheduler.get_jobs())
"

# Check logs
docker-compose logs backend | grep -i "scheduler"
```

**Resolution**:
```bash
# Restart backend (scheduler starts on boot)
docker-compose restart backend

# Manual execution
docker-compose exec backend python -c "
from app.services.site_discovery_service import SiteDiscoveryService
from app.db.session import SessionLocal
db = SessionLocal()
service = SiteDiscoveryService(db)
result = service.discover_sites()
print(result)
"
```

---

## Backup & Recovery

### Database Backup

```bash
# Full backup
docker-compose exec postgres pg_dump -U admin sharepoint_gov > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
docker-compose exec postgres pg_dump -U admin sharepoint_gov | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Schema only
docker-compose exec postgres pg_dump -U admin --schema-only sharepoint_gov > schema_backup.sql

# Automated daily backup (add to crontab)
0 2 * * * cd /path/to/project && docker-compose exec -T postgres pg_dump -U admin sharepoint_gov | gzip > /backups/sharepoint_gov_$(date +\%Y\%m\%d).sql.gz
```

### Database Restore

```bash
# Restore from backup
docker-compose exec -T postgres psql -U admin sharepoint_gov < backup.sql

# Restore from compressed
gunzip -c backup.sql.gz | docker-compose exec -T postgres psql -U admin sharepoint_gov

# Point-in-time recovery (requires WAL archiving)
# See PostgreSQL documentation
```

### Redis Backup

```bash
# Trigger save
docker-compose exec redis redis-cli SAVE

# Copy RDB file
docker cp $(docker-compose ps -q redis):/data/dump.rdb redis_backup_$(date +%Y%m%d).rdb

# Restore
docker cp redis_backup.rdb $(docker-compose ps -q redis):/data/dump.rdb
docker-compose restart redis
```

### Configuration Backup

```bash
# Backup .env and configs
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
  .env \
  monitoring/ \
  docker-compose*.yml

# Restore
tar -xzf config_backup.tar.gz
```

---

## Incident Response

### P1: Critical - Platform Down

**Response Time**: Immediate (15 minutes)

**Actions**:
1. Check service status: `docker-compose ps`
2. Review logs: `docker-compose logs --tail=500`
3. Restart services: `docker-compose restart`
4. If database issue: Restore from latest backup
5. Notify stakeholders
6. Create incident ticket

### P2: High - Performance Degradation

**Response Time**: 1 hour

**Actions**:
1. Check metrics: Navigate to Grafana dashboards
2. Identify bottleneck: Database, API, or cache
3. Scale resources or clear cache
4. Monitor for improvement
5. Schedule root cause analysis

### P3: Medium - Feature Not Working

**Response Time**: 4 hours

**Actions**:
1. Verify configuration
2. Check logs for errors
3. Test manually
4. Apply fix and deploy
5. Monitor metrics

### P4: Low - Enhancement Request

**Response Time**: Next sprint

**Actions**:
1. Document request
2. Prioritize in backlog
3. Schedule for development

---

## Monitoring & Alerts

### Access Metrics

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001
- **Application Metrics**: http://localhost:8000/metrics

### Key Metrics to Watch

| Metric | Threshold | Action |
|--------|-----------|--------|
| API Response Time (p95) | > 2s | Investigate slow queries |
| Error Rate | > 5% | Check logs, restart if needed |
| Database Connections | > 80% | Increase max connections |
| Redis Memory | > 90% | Clear cache or increase memory |
| Disk Space | < 15% | Clean up old logs/backups |
| Overdue Reviews | > 10 | Send reminder emails |

### Alert Channels

Configure in `monitoring/prometheus/alertmanager.yml`:
- **Email**: alerts@company.com
- **Slack**: #sharepoint-governance-alerts
- **PagerDuty**: For P1/P2 incidents

### SLA Targets

- **Uptime**: 99.9% (< 44 minutes downtime/month)
- **API Response Time**: p95 < 500ms, p99 < 2s
- **Background Jobs**: 99% success rate
- **Data Freshness**: < 24 hours for site discovery

---

## Maintenance Windows

### Scheduled Maintenance

- **When**: First Sunday of month, 2:00 AM - 4:00 AM UTC
- **Activities**:
  - Apply security patches
  - Database maintenance (VACUUM, ANALYZE)
  - Clear old audit logs (> 1 year)
  - Review and archive old access reviews
  - Update dependencies

### Pre-Maintenance Checklist

- [ ] Notify users 72 hours in advance
- [ ] Backup database and configuration
- [ ] Test updates in staging environment
- [ ] Prepare rollback plan
- [ ] Have on-call engineer available

### Post-Maintenance Checklist

- [ ] Verify all services running
- [ ] Check metrics dashboard
- [ ] Run smoke tests
- [ ] Monitor for 1 hour
- [ ] Send completion notice

---

## Contact Information

- **Platform Team**: sharepoint-gov-team@company.com
- **On-Call**: Use PagerDuty escalation
- **Documentation**: http://wiki.company.com/sharepoint-governance
- **Support Slack**: #sharepoint-governance-support

---

**Last Updated**: December 5, 2025  
**Maintained By**: Platform Engineering Team
