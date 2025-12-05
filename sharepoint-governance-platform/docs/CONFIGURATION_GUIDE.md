# Configuration Credentials Guide

This document provides detailed information on where and how to obtain each configuration value required by the SharePoint Governance Platform.

---

## 📊 Database Configuration

### `DATABASE_URL`
**Format**: `postgresql://username:password@host:port/database`

**Where to Get**:
1. **Install PostgreSQL** (if not already installed):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   
   # RHEL/CentOS
   sudo yum install postgresql-server postgresql-contrib
   
   # macOS
   brew install postgresql
   ```

2. **Create Database and User**:
   ```sql
   sudo -u postgres psql
   CREATE DATABASE spg_db;
   CREATE USER spg_user WITH ENCRYPTED PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE spg_db TO spg_user;
   \q
   ```

3. **Build Connection String**:
   - **Host**: `localhost` (local) or server IP/hostname
   - **Port**: `5432` (default)
   - **Example**: `postgresql://spg_user:SecurePass123@localhost:5432/spg_db`

**Testing**: The setup wizard will test this connection automatically.

### `DATABASE_POOL_SIZE` & `DATABASE_MAX_OVERFLOW`
**Recommended Values**:
- Pool Size: `20` (small/medium deployments), `50` (large deployments)
- Max Overflow: `10` (allows burst capacity)

---

## 🔴 Redis Configuration

### `REDIS_URL`
**Format**: `redis://host:port/database_number`

**Where to Get**:
1. **Install Redis**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install redis-server
   
   # RHEL/CentOS
   sudo yum install redis
   
   # macOS
   brew install redis
   ```

2. **Start Redis**:
   ```bash
   sudo systemctl start redis
   sudo systemctl enable redis
   ```

3. **Default URL**: `redis://localhost:6379/0`

**Testing**: Setup wizard provides connection test.

---

## ☁️ Microsoft 365 Configuration

### `TENANT_ID`
**Where to Get**:
1. Navigate to [Azure Portal](https://portal.azure.com)
2. Go to **Azure Active Directory**
3. Click **Overview** in left sidebar
4. Copy **Tenant ID** (also called Directory ID)

**Example**: `12345678-1234-1234-1234-123456789abc`

### `CLIENT_ID` & `CLIENT_SECRET`
**Where to Get** (Azure AD App Registration):

> [!IMPORTANT]
> You need **Azure AD Administrator** or **Application Administrator** role to create app registrations.

1. **Navigate to Azure Portal** → **Azure Active Directory** → **App Registrations**

2. **Click "New registration"**:
   - **Name**: `SharePoint Governance Platform`
   - **Supported account types**: `Accounts in this organizational directory only`
   - **Redirect URI**: Leave blank for now
   - Click **Register**

3. **Copy Application (client) ID** → This is your `CLIENT_ID`

4. **Create Client Secret**:
   - In your app registration, go to **Certificates & secrets**
   - Click **New client secret**
   - **Description**: `SPG Backend Secret`
   - **Expires**: Choose duration (12 months, 24 months, or custom)
   - Click **Add**
   - **⚠️ IMPORTANT**: Copy the **Value** immediately (you can't see it again!)
   - This value is your `CLIENT_SECRET`

5. **Configure API Permissions**:
   - Go to **API permissions**
   - Click **Add a permission** → **Microsoft Graph** → **Application permissions**
   - Add these permissions:
     - `Sites.Read.All` - Read SharePoint sites
     - `Sites.ReadWrite.All` - Manage SharePoint sites
     - `User.Read.All` - Read user profiles
     - `Group.Read.All` - Read groups
     - `Files.Read.All` - Read files metadata
     - `AuditLog.Read.All` - Read audit logs
     - `Mail.Send` - Send email notifications
   - Click **Grant admin consent** (requires Global Admin)

**PowerShell Alternative**:
```powershell
# Install Azure AD module if needed
Install-Module -Name Az -AllowClobber -Scope CurrentUser

# Connect to Azure
Connect-AzAccount

# Create App Registration
$app = New-AzADApplication -DisplayName "SharePoint Governance Platform"
$clientId = $app.AppId

# Create Service Principal
$sp = New-AzADServicePrincipal -ApplicationId $clientId

# Create Client Secret
$secret = New-AzADAppCredential -ApplicationId $clientId -EndDate (Get-Date).AddYears(2)
$clientSecret = $secret.SecretText

Write-Host "CLIENT_ID: $clientId"
Write-Host "CLIENT_SECRET: $clientSecret"
Write-Host "⚠️ Save the CLIENT_SECRET now - you won't be able to retrieve it later!"
```

### `SHAREPOINT_SITE_URL`
**Where to Get**:
1. Open your SharePoint Online site in browser
2. Copy the URL from address bar
3. Use the root site URL: `https://[yourtenant].sharepoint.com`

**Example**: `https://contoso.sharepoint.com`

---

## 🔐 Active Directory / LDAP Configuration

### `LDAP_SERVER`
**Where to Get**:

**Option 1 - Query from Domain-Joined Windows Machine**:
```powershell
# Find domain controllers
$env:LOGONSERVER
# Returns: \\DC01

# Get full LDAP URL
nslookup $env:LOGONSERVER
# Use the IP or hostname: ldap://dc01.company.com:389
```

**Option 2 - DNS Query**:
```bash
nslookup -type=SRV _ldap._tcp.dc._msdcs.company.com
```

**Format**: `ldap://server:389` (standard) or `ldaps://server:636` (SSL)

### `LDAP_BASE_DN`
**Where to Get**:

**Option 1 - From Domain Name**:
- Domain: `company.com` → Base DN: `dc=company,dc=com`
- Domain: `subdomain.company.com` → Base DN: `dc=subdomain,dc=company,dc=com`

**Option 2 - Query AD**:
```powershell
# From domain-joined machine
([ADSI]"LDAP://RootDSE").defaultNamingContext
# Returns: DC=company,DC=com
```

**Option 3 - Using ldapsearch**:
```bash
ldapsearch -x -H ldap://dc01.company.com -s base -b "" defaultNamingContext
```

### `LDAP_BIND_DN` & `LDAP_BIND_PASSWORD`
**What**: Service account credentials for LDAP queries

**How to Create Service Account**:

> [!WARNING]
> The service account password will be stored in the .env file. Use a dedicated service account with minimum required permissions, not a user account.

```powershell
# Create service account in AD
New-ADUser -Name "SPG-Service" `
  -SamAccountName "svc_spg" `
  -UserPrincipalName "svc_spg@company.com" `
  -AccountPassword (ConvertTo-SecureString "YourSecurePassword123!" -AsPlainText -Force) `
  -Enabled $true `
  -PasswordNeverExpires $true `
  -Description "SharePoint Governance Platform LDAP Service Account"

# Add to required groups for read access
Add-ADGroupMember -Identity "Domain Users" -Members "svc_spg"
```

**Bind DN Format**: `cn=svc_spg,ou=ServiceAccounts,dc=company,dc=com`

**Required Permissions**:
- Read access to User objects
- Read access to Group objects
- No write or admin permissions needed

### `LDAP_USER_SEARCH_BASE`
**What**: Organizational Unit (OU) where user accounts are stored

**Where to Get**:
```powershell
# Find common user locations
Get-ADUser -Filter * -SearchBase "DC=company,DC=com" | 
  Select-Object DistinguishedName | 
  Group-Object {$_.DistinguishedName -replace '^CN=[^,]+,'} | 
  Sort-Object Count -Descending | 
  Select-Object -First 5
```

**Common Values**:
- `ou=Users,dc=company,dc=com`
- `ou=Employees,ou=Users,dc=company,dc=com`
- `cn=Users,dc=company,dc=com` (default container)

### `LDAP_GROUP_SEARCH_BASE`
**What**: OU where security groups are stored

**Common Values**:
- `ou=Groups,dc=company,dc=com`
- `ou=Security Groups,dc=company,dc=com`
- `cn=Users,dc=company,dc=com` (if groups and users are together)

---

## 🔑 JWT Authentication

### `SECRET_KEY`
**What**: Cryptographic key for signing JWT tokens

**How to Generate**:

**Option 1 - OpenSSL**:
```bash
openssl rand -hex 32
```

**Option 2 - Python**:
```python
import secrets
print(secrets.token_hex(32))
```

**Option 3 - PowerShell**:
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | % {[char]$_})
```

**Requirements**:
- Minimum 32 characters
- Use cryptographically secure random generation
- Never share or commit to version control
- Rotate periodically (every 6-12 months)

### `ALGORITHM`
**Default**: `HS256` (HMAC with SHA-256)
**Alternative**: `HS512` (stronger, slightly slower)

### `ACCESS_TOKEN_EXPIRE_MINUTES`
**Recommended**: `30` (30 minutes)
**Alternatives**:
- `15` - High security environments
- `60` - Standard environments
- `120` - Low-risk internal tools

### `REFRESH_TOKEN_EXPIRE_DAYS`
**Recommended**: `7` (7 days)
**Alternatives**:
- `1` - High security
- `30` - User convenience
- `90` - Long-lived sessions

---

## 🌐 CORS Configuration

### `CORS_ORIGINS`
**What**: Allowed frontend URLs

**Development**:
```
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000
```

**Production**:
```
CORS_ORIGINS=https://spg.company.com,https://sharepoint-governance.company.com
```

**Format**: Comma-separated list, no spaces, include protocol

---

## ⏰ Background Jobs (Cron Schedules)

### Cron Format Reference
```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday=0)
│ │ │ │ │
* * * * *
```

### `SITE_DISCOVERY_SCHEDULE_CRON`
**Default**: `0 2 * * *` (Daily at 2:00 AM)
**Alternatives**:
- `0 */6 * * *` - Every 6 hours
- `0 0 * * 0` - Weekly on Sunday at midnight

### `AUDIT_SYNC_SCHEDULE_CRON`
**Default**: `0 */6 * * *` (Every 6 hours)
**Recommended**: Run frequently for compliance

### `ACCESS_REVIEW_SCHEDULE_CRON`
**Default**: `0 0 1 */3 *` (Quarterly on 1st day of month)
**Compliance**: Adjust based on policy requirements

### `USER_SYNC_SCHEDULE_CRON`
**Default**: `0 1 * * *` (Daily at 1:00 AM)

---

## 📧 Email Notifications

### `EMAIL_FROM`
**What**: Sender address for notifications

**Where to Get**:
- Use a monitored mailbox: `noreply@company.com`
- Or dedicated: `sharepoint-governance@company.com`

**Requirements**:
- Must exist in your Microsoft 365 tenant
- The Azure AD app needs `Mail.Send` permission
- Consider using a shared mailbox

---

## 🔐 Two-Factor Authentication (2FA)

### `TOTP_ISSUER_NAME`
**What**: Name shown in authenticator apps
**Default**: `SharePoint Governance Platform`
**Appears as**: `SharePoint Governance Platform (user@company.com)`

### `TOTP_DIGITS`
**Default**: `6` (standard)
**Alternative**: `8` (higher security, less compatible)

### `TOTP_INTERVAL`
**Default**: `30` (seconds)
**Standard**: Do not change unless required

### `BACKUP_CODES_COUNT`
**Default**: `10` codes
**Range**: 5-20 codes

### `TRUSTED_DEVICE_EXPIRY_DAYS`
**Default**: `30` days
**Alternatives**:
- `7` - High security
- `60` - User convenience
- `90` - Extended trust

---

## 🛠️ Quick Setup Checklist

Use this checklist to gather all required information:

- [ ] PostgreSQL database created and accessible
- [ ] Redis server installed and running
- [ ] Azure AD Tenant ID copied
- [ ] Azure App Registration created
- [ ] Azure App Client ID copied
- [ ] Azure App Client Secret saved
- [ ] Azure App permissions configured and consented
- [ ] SharePoint root site URL identified
- [ ] Active Directory domain controller identified
- [ ] LDAP base DN determined
- [ ] AD service account created
- [ ] AD service account permissions configured
- [ ] User and group search bases identified
- [ ] JWT secret key generated (32+ chars)
- [ ] CORS origins list prepared
- [ ] Email sender address identified
- [ ] Cron schedules reviewed

---

## 🔗 Helpful Links

- [Azure Portal](https://portal.azure.com)
- [Azure AD App Registrations](https://portal.azure.com/#view/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/~/RegisteredApps)
- [Microsoft Graph Permissions Reference](https://docs.microsoft.com/en-us/graph/permissions-reference)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [LDAP Query Basics](https://ldap.com/ldap-filters/)
- [Cron Expression Generator](https://crontab.guru/)

---

## ⚠️ Security Best Practices

1. **Never commit .env files** to version control
2. **Use strong, unique passwords** for all service accounts
3. **Rotate secrets regularly** (every 6-12 months)
4. **Use least privilege** for service accounts
5. **Enable audit logging** for all credential usage
6. **Encrypt secrets at rest** in production
7. **Use Azure Key Vault** or similar for production secrets
8. **Restrict access** to configuration files (chmod 600)
9. **Monitor for** unusual access patterns
10. **Document** credential rotation procedures
