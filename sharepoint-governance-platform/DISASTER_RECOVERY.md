# SharePoint Governance Platform - Disaster Recovery Plan

## Overview

This document outlines the disaster recovery (DR) procedures for the SharePoint Governance Platform to ensure business continuity in the event of catastrophic failure.

**RTO (Recovery Time Objective)**: 4 hours  
**RPO (Recovery Point Objective)**: 1 hour (database), 24 hours (configuration)

---

## Disaster Scenarios

### Scenario 1: Complete Data Center Failure

**Impact**: Total platform unavailability

**Recovery Steps**:
1. Activate DR site/region
2. Restore database from latest backup (see backup procedures)
3. Deploy application stack from container registry
4. Update DNS to point to DR site
5. Verify all services operational
6. Notify users of recovery completion

**Estimated Recovery Time**: 3-4 hours

### Scenario 2: Database Corruption/Loss

**Impact**: Data loss, platform read-only or unavailable

**Recovery Steps**:
1. Stop all write operations
2. Assess corruption extent
3. Restore from most recent clean backup
4. Apply transaction logs if available (WAL recovery)
5. Verify data integrity
6. Resume operations

**Estimated Recovery Time**: 1-2 hours

### Scenario 3: Application Failure (Container/Code)

**Impact**: API unavailable, frontend not accessible

**Recovery Steps**:
1. Rollback to previous container version
2. If configuration issue: Restore .env from backup
3. If code issue: Revert Git commit and rebuild
4. Redeploy containers
5. Verify functionality

**Estimated Recovery Time**: 30 minutes - 1 hour

### Scenario 4: Security Breach/Ransomware

**Impact**: Potential data compromise, service disruption

**Recovery Steps**:
1. Immediately isolate affected systems
2. Activate incident response team
3. Assess breach scope
4. Restore from clean backup (verified pre-breach)
5. Apply security patches
6. Reset all credentials and secrets
7. Conduct security audit
8. Resume operations with enhanced monitoring

**Estimated Recovery Time**: 4-8 hours (+ forensics time)

---

## Backup Strategy

### Automated Backups

**Database** (PostgreSQL):
- **Frequency**: Every 6 hours
- **Retention**: 30 days
- **Location**: Offsite S3/Azure Blob Storage
- **Method**: pg_dump with compression
- **Encryption**: AES-256

**Configuration**:
- **Frequency**: Daily
- **Retention**: 90 days
- **Includes**: .env, docker-compose files, monitoring configs

**Application Code**:
- **Method**: Git repository (GitHub)
- **Backups**: Automatic via GitHub
- **Tags**: All releases tagged

### Backup Verification

**Monthly**:
- Restore test in isolated environment
- Verify data integrity
- Test application startup with restored data
- Document any issues

---

## Recovery Procedures

### Step 1: Assess Situation

```bash
# Check service status
docker-compose ps
curl -f http://localhost:8000/health || echo "Backend DOWN"
docker-compose exec postgres pg_isready || echo "Database DOWN"

# Review recent logs
docker-compose logs --tail=1000 > incident_logs_$(date +%Y%m%d_%H%M%S).log

# Check metrics
# Navigate to Grafana and review dashboards
```

### Step 2: Activate DR Mode

```bash
# Set maintenance mode (if applicable)
export MAINTENANCE_MODE=true

# Notify users via status page
# curl -X POST https://status.company.com/api/incidents ...

# Alert team
# Send notifications to #incident-response Slack channel
```

### Step 3: Database Recovery

```bash
# Stop current database
docker-compose stop postgres

# Backup current state (if possible)
docker-compose exec postgres pg_dump -U admin sharepoint_gov > pre_recovery_backup.sql

# Identify recovery point
ls -lh /backups/sharepoint_gov_*.sql.gz

# Restore from backup
gunzip -c /backups/sharepoint_gov_20251205.sql.gz | \
  docker-compose exec -T postgres psql -U admin sharepoint_gov

# Start database
docker-compose start postgres

# Verify
docker-compose exec postgres psql -U admin sharepoint_gov -c "SELECT COUNT(*) FROM sharepoint_sites;"
```

### Step 4: Application Recovery

```bash
# Pull latest stable images
docker-compose pull

# Or rollback to specific version
docker-compose down
docker-compose -f docker-compose.yml \
  -e BACKEND_VERSION=v2.0.0 \
  -e FRONTEND_VERSION=v2.0.0 \
  up -d

# Verify deployment
docker-compose ps
curl -f http://localhost:8000/health
```

### Step 5: Verification

```bash
# Run health checks
./scripts/health_check.sh

# Verify critical endpoints
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test@domain.com","password":"test"}'

# Test background jobs
docker-compose exec backend python -c "
from app.tasks.scheduler import scheduler
print('Scheduler running:', scheduler.running)
print('Jobs:', len(scheduler.get_jobs()))
"

# Verify data integrity
docker-compose exec backend python scripts/verify_data_integrity.py
```

### Step 6: Resume Operations

```bash
# Disable maintenance mode
export MAINTENANCE_MODE=false

# Monitor metrics for 1 hour
echo "Monitoring metrics at http://localhost:3001"

# Notify users
# Update status page: "All systems operational"

# Post-incident review
# Schedule within 48 hours
```

---

## Failover Architecture

### Primary Site
- **Location**: us-east-1
- **Components**: Full stack (PostgreSQL, Redis, Backend, Frontend)

### DR Site
- **Location**: us-west-2
- **Components**: Standby database replica, container images
- **Sync**: Database streaming replication (async)

### DNS Failover
```bash
# Manual DNS update (example)
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456 \
  --change-batch file://failover-to-dr.json

# Or automated health-check based failover
# Configure in Route53 health checks
```

---

## Data Retention

| Data Type | Retention | Archive After | Delete After |
|-----------|-----------|---------------|--------------|
| Audit Logs | Active | 1 year | 7 years |
| Access Review Data | Active | 2 years | 5 years |
| Site Metadata | Active | Never | On site deletion |
| Database Backups | Hot | 30 days | 90 days |
| Configuration Backups | Hot | 90 days | 1 year |
| Application Logs | Active | 30 days | 90 days |

---

## Security in DR

### Credentials Management

**Post-Recovery Actions**:
1. Rotate all secrets and API keys
2. Force password reset for all admin users
3. Re-issue JWT signing keys
4. Update service-to-service credentials

**Secrets Storage**:
- Use Azure Key Vault or AWS Secrets Manager
- Never commit secrets to Git
- Environment-specific secrets

### Access Control

**DR Access**:
- Limited to DR team members only
- MFA required
- All actions logged and audited
- Separate credentials from production

---

## Communication Plan

### Stakeholders

| Role | Contact | When to Notify |
|------|---------|----------------|
| CTO | cto@company.com | Immediately (< 15 min) |
| VP Engineering | vp-eng@company.com | Immediately (< 15 min) |
| Platform Team | team@company.com | Immediately (< 15 min) |
| All Users | all-users@company.com | Within 1 hour |
| Customers | Via status page | Within 30 minutes |

### Communication Templates

**Initial Notification** (< 30 min):
```
Subject: [INCIDENT] SharePoint Governance Platform Service Disruption

We are experiencing a service disruption affecting the SharePoint 
Governance Platform. Our team is actively investigating and working 
to restore service.

Status: Investigating
ETA: TBD (updates every 30 minutes)
Affected: [List affected components]

Updates: https://status.company.com
```

**Progress Update** (Every 30 min):
```
Subject: [UPDATE] SharePoint Governance Platform Service Disruption

Update: [Progress description]
Current Status: [Investigating/Identified/Implementing/Monitoring]
ETA: [Updated estimate]
Next Update: [Time]
```

**Resolution** (Upon completion):
```
Subject: [RESOLVED] SharePoint Governance Platform Service Disruption

The SharePoint Governance Platform is now fully operational. All 
services have been restored and verified.

Downtime: [Duration]
Root Cause: [Brief description]
Prevented Future Occurrences: [Actions taken]

A full post-mortem will be published within 48 hours.
```

---

## Testing & Drills

### Quarterly DR Drill

**Objectives**:
- Validate backup restoration
- Practice failover procedures
- Measure actual RTO/RPO
- Train team members

**Procedure**:
1. Schedule drill (off-peak hours)
2. Select random backup to restore
3. Execute recovery procedure
4. Measure time to recovery
5. Document lessons learned
6. Update DR plan as needed

**Last Drill**: [To be scheduled]  
**Next Drill**: Q1 2026

---

## Post-Incident Process

### Immediate (< 24 hours)
- [ ] Document incident timeline
- [ ] Preserve logs and evidence
- [ ] Initial impact assessment
- [ ] Communicate resolution to stakeholders

### Short-term (< 48 hours)
- [ ] Conduct post-mortem meeting
- [ ] Create action items for prevention
- [ ] Update runbook with learnings
- [ ] Review and update alerts

### Long-term (< 2 weeks)
- [ ] Implement prevention measures
- [ ] Update DR plan if needed
- [ ] Conduct training if gaps identified
- [ ] Share lessons learned with org

---

## Appendix

### Emergency Contacts

- **On-Call Engineer**: Use PagerDuty escalation
- **Database Admin**: dba-team@company.com
- **Security Team**: security@company.com
- **Cloud Provider Support**: [Support portal links]

### Recovery Scripts

Located in `/scripts/disaster-recovery/`:
- `restore_database.sh`
- `failover_to_dr.sh`
- `rollback_deployment.sh`
- `verify_recovery.sh`

### External Dependencies

- Microsoft Graph API: monitor.graph.microsoft.com
- Azure AD: status.azure.com
- GitHub: githubstatus.com

---

**Document Version**: 1.0  
**Last Updated**: December 5, 2025  
**Next Review**: March 5, 2026  
**Owner**: Platform Engineering Team
