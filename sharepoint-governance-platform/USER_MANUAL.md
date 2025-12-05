# SharePoint Governance Platform - User Manual

## Table of Contents
1. [Getting Started](#getting-started)
2. [For Site Owners](#for-site-owners)
3. [For Administrators](#for-administrators)
4. [For Compliance Officers](#for-compliance-officers)
5. [For Executives](#for-executives)
6. [FAQ](#faq)

---

## Getting Started

### Logging In

1. Navigate to the platform URL (e.g., https://sharepoint-governance.company.com)
2. Click **"Sign In"**
3. Enter your **Active Directory credentials**
4. Click **"Login"**

Your role is automatically assigned based on your AD group membership.

### Dashboard Overview

After logging in, you'll see your role-specific dashboard:
- **Site Owners**: My sites and pending reviews
- **Administrators**: System-wide metrics and operations
- **Compliance Officers**: Audit reports and compliance status
- **Executives**: High-level governance metrics

---

## For Site Owners

### Viewing Your Sites

**Location**: Dashboard → My Sites

**What You'll See**:
- List of SharePoint sites you own
- Health score for each site
- Last activity date
- Storage usage
- Pending actions

**Actions Available**:
- View site details
- Check access permissions
- Complete access reviews
- View audit trail

### Completing Access Reviews

Access reviews are required **quarterly** to certify that all users still need access to your sites.

**Step 1: Access Review Notification**
- You'll receive an email when a review is assigned
- Email contains direct link to the review

**Step 2: Review Access**
1. Click **"Access Reviews"** in the navigation
2. Select the **pending review** for your site
3. Review each user's access permissions
4. For each user, choose:
   - ✅ **Approve** - User still needs access
   - ❌ **Revoke** - User no longer needs access
   - 📝 **Add comments** (optional but recommended)

**Step 3: Certify Review**
1. After reviewing all users, click **"Certify Review"**
2. Confirm certification
3. Review is marked as complete

**Important**:
- Reviews must be completed within **30 days**
- Overdue reviews appear in red
- Your manager will be notified of overdue reviews

### Understanding Site Health Score

Each site has a health score (0-100):

- **90-100**: ✅ Excellent - No issues
- **70-89**: ⚠️ Good - Minor issues
- **50-69**: ⚡ Fair - Attention needed
- **<50**: 🔴 Poor - Immediate action required

**Factors Affecting Score**:
- Overdue access reviews (-30 points)
- Inactive site >180 days (-20 points)
- High external user count (-20 points)
- Storage >90% full (-15 points)
- No activity in 90 days (-15 points)

### Managing Site Users

**View Current Access**:
1. Navigate to **My Sites**
2. Click on a site name
3. Click **"Access Matrix"** tab
4. View all users, groups, and permission levels

**Requesting Access Changes**:
1. Contact your IT administrator
2. Or use the **"Request Change"** button (if enabled)

---

## For Administrators

### Site Discovery

**Automated Discovery**:
- Runs automatically **daily at 2:00 AM**
- Discovers new SharePoint sites
- Updates existing site metadata
- Classifies sites (Team, Communication, Hub, etc.)

**Manual Discovery**:
1. Navigate to **Admin → Sites**
2. Click **"Trigger Discovery"**
3. Wait for job to complete (may take 5-30 minutes)
4. Refresh page to see results

### Monitoring Access Reviews

**View All Reviews**:
1. Navigate to **Admin → Access Reviews**
2. Filter by status: Pending, In Progress, Completed, Overdue
3. View completion rates by site owner

**Taking Action on Overdue Reviews**:
1. Select overdue reviews
2. Click **"Send Reminder"** to notify site owner
3. Or **"Escalate"** to owner's manager

### Storage Management

**View Storage Analytics**:
1. Navigate to **Admin → Storage**
2. View:
   - Total storage usage across tenant
   - Top storage consumers
   - Sites approaching quota limits
   - Storage trends over time

**Version Cleanup**:
1. Navigate to **Admin → Version Management**
2. View libraries with excessive versions
3. Select libraries to clean up
4. Configure:
   - **Retention days** (default: 90 days)
   - **Minimum versions to keep** (default: 3)
5. Click **"Start Cleanup"**
6. Monitor progress

**Recycle Bin Management**:
1. Navigate to **Admin → Recycle Bin**
2. View first-stage and second-stage bin contents
3. Actions:
   - **Restore items** from recycle bin
   - **Permanent delete** second-stage items >90 days
   - **Schedule automated cleanup**

### User Management

**Sync Users from Active Directory**:
- Runs automatically **daily at 1:00 AM**
- Manual sync: **Admin → Users → Sync Now**

**Assign Roles**:
Roles are assigned based on AD group membership:
- `SP-Gov-SiteOwners` → Site Owner
- `SP-Gov-Admins` → Administrator
- `SP-Gov-Auditors` → Auditor
- `SP-Gov-Compliance` → Compliance Officer
- `SP-Gov-Executives` → Executive

### Retention Policy Management

**View Retention Policies**:
1. Navigate to **Admin → Retention**
2. View all policies synced from Microsoft Purview
3. Last sync time displayed

**Manage Exclusions**:
1. Navigate to **Retention → Exclusions**
2. View pending exclusion requests from site owners
3. Review and **Approve** or **Reject**
4. Add **comments** before approving

**Request Exclusion** (for a site owner):
1. Navigate to site details
2. Click **"Request Retention Exclusion"**
3. Select policy
4. Provide business justification
5. Submit for approval

---

## For Compliance Officers

### Generating Compliance Reports

**GDPR Compliance Report**:
1. Navigate to **Compliance → Reports**
2. Select **"GDPR Report"**
3. Choose date range
4. Click **"Generate"**
5. Download PDF or Excel

**Report Includes**:
- Data access logs
- User consent tracking
- Data deletion evidence
- Processing records

**ISO 27001 Audit Report**:
1. Navigate to **Compliance → Reports**
2. Select **"ISO 27001 Audit Report"**
3. Choose date range
4. Click **"Generate"**

**Report Includes**:
- Access control logs
- Security incidents
- Change management records
- Asset inventory

**SOX Compliance Report**:
1. Navigate to **Compliance → Reports**
2. Select **"SOX Compliance"**
3. Choose date range
4. Click **"Generate"**

**Report Includes**:
- Financial data access logs
- Segregation of duties verification
- Configuration changes
- Approval workflows

### Audit Log Viewer

**Search Audit Logs**:
1. Navigate to **Compliance → Audit Logs**
2. Filter by:
   - Date range
   - User email
   - Operation type (Access, Modify, Delete, etc.)
   - Site URL
   - Result status (Success, Failed)
3. Click **"Search"**

**Export Audit Logs**:
1. After searching, click **"Export"**
2. Choose format: CSV or JSON
3. Download file

**Viewing Anomalies**:
1. Navigate to **Compliance → Anomalies**
2. View AI-detected anomalies:
   - Off-hours access
   - Unusual download patterns
   - Permission changes during weekends
   - Bulk operations
3. Click anomaly to view details
4. Mark as **"False Positive"** or **"Confirmed"**

---

## For Executives

### Executive Dashboard

**Key Metrics**:
- Total active SharePoint sites
- Access review completion rate
- Compliance status (% compliant)
- Storage utilization
- Security anomalies detected
- Risk score (tenant-wide)

**Viewing Trends**:
- All metrics show 30-day trends
- Click any metric to drill down
- Export data to Excel

### Power BI Integration

**Accessing Power BI Dashboards**:
1. Open Power BI Desktop or Power BI Service
2. Connect to SharePoint Governance Platform
3. Use provided connection string
4. Select pre-built dashboard templates

**Available Dashboards**:
- **Executive Summary** - High-level KPIs
- **Compliance Dashboard** - Compliance metrics
- **Storage Analytics** - Storage trends and forecasts
- **Access Review Status** - Review completion tracking
- **Security Overview** - Anomalies and risk scores

**Refreshing Data**:
- Automatic refresh: Every 6 hours
- Manual refresh: Click **"Refresh Now"** in Power BI

---

## FAQ

### General Questions

**Q: How often should I complete access reviews?**  
A: Access reviews are required **quarterly** (every 3 months). You'll receive email notifications when a review is assigned.

**Q: What happens if I don't complete an access review on time?**  
A: Overdue reviews are escalated to your manager. The site may be marked as non-compliant, affecting governance metrics.

**Q: Can I delegate my access review to someone else?**  
A: No, access reviews must be completed by the designated site owner. If you're no longer the owner, contact IT to update ownership.

**Q: How is my role determined?**  
A: Your role is automatically assigned based on your Active Directory group membership. Contact IT to request a role change.

### Site Owners

**Q: Why is my site health score low?**  
A: Common reasons:
- Overdue access reviews
- Site hasn't been accessed in 90+ days
- Storage quota near limit
- High number of external users

**Q: How do I improve my site health score?**  
A: 
1. Complete pending access reviews
2. Clean up old content
3. Remove unnecessary external users
4. Archive or delete inactive sites

**Q: What is an "external user"?**  
A: An external user is someone outside your organization (e.g., partners, vendors). They're tracked for security and compliance.

### Administrators

**Q: How often does site discovery run?**  
A: Automatically every day at 2:00 AM. You can also trigger manual discovery anytime.

**Q: Can I exclude sites from governance?**  
A: Yes, through retention policy exclusions. Site owners must submit a request with business justification for approval.

**Q: What's the difference between first-stage and second-stage recycle bin?**  
A: 
- **First-stage**: Items deleted by users (restorable by users)
- **Second-stage**: Items deleted from first-stage (admin-only restoration)

**Q: How long are audit logs retained?**  
A: Audit logs are retained for **7 years** in compliance with regulations. Logs older than 1 year are archived.

### Compliance Officers

**Q: Are the compliance reports auditor-ready?**  
A: Yes, all reports include:
- Evidence collection
- Timestamp and attribution
- Digital signatures
- Comprehensive audit trails

**Q: How accurate is the anomaly detection?**  
A: The AI model has 85%+ accuracy. All anomalies should be reviewed and confirmed or marked as false positives.

**Q: Can I schedule automated report delivery?**  
A: Yes, navigate to **Compliance → Scheduled Reports** to set up automated delivery via email.

---

## Getting Help

**Technical Support**:
- Email: sharepoint-gov-support@company.com
- Slack: #sharepoint-governance-support
- Phone: ext. 5555 (Mon-Fri, 9 AM - 5 PM)

**Documentation**:
- **User Manual**: This document
- **Admin Guide**: For detailed administrative procedures
- **API Documentation**: https://sharepoint-governance.company.com/api/v1/docs
- **Runbook**: For operational procedures

**Training**:
- New user orientation: First Tuesday of each month
- Advanced training: On request
- Video tutorials: Coming soon

---

**Document Version**: 1.0  
**Last Updated**: December 5, 2025  
**Maintained By**: Platform Team
