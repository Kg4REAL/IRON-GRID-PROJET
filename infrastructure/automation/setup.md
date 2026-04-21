# ⚙️ Automation & Self-Healing — IRON-GRID

## Overview

IRON-GRID uses a lightweight automation layer built with Python and Bash to ensure **infrastructure resilience** and **auditability**. Scripts run at boot and on a daily cron schedule to catch service failures early and maintain configuration history.

---

## 1. Scripts

### `iron-check.py` — Service Health Monitor & Config Backup

**Language:** Python 3  
**Location:** `infrastructure/scripts/iron-check.py`

**What it does:**
- Checks the systemd status of all critical services (`nginx`, `bind9`, `smbd`, `slapd`, `fail2ban`, `wazuh-agent`)
- Creates timestamped backups of key config files (`sshd_config`, `named.conf`, `smb.conf`, `nginx default`)
- Returns exit code `1` if any service is down — usable in alerting pipelines

**Usage:**
```bash
python3 iron-check.py            # Run health check + backup (default)
python3 iron-check.py --check    # Health check only
python3 iron-check.py --backup   # Backup only
```

**Sample output:**
```
══════════════════════════════════════════════════
  IRON-GRID SYSTEM AUDIT — 2026-04-20_09h00
══════════════════════════════════════════════════
  [✔] nginx                ACTIVE
  [✔] bind9                ACTIVE
  [✔] smbd                 ACTIVE
  [✔] slapd                ACTIVE
  [✔] fail2ban             ACTIVE
  [✔] wazuh-agent          ACTIVE
──────────────────────────────────────────────────
  ALL SYSTEMS OPERATIONAL
══════════════════════════════════════════════════

[*] Starting config backup → /var/backups/iron_grid
  [+] dns        → dns_backup_2026-04-20_09h00.conf
  [+] nginx      → nginx_backup_2026-04-20_09h00.conf
  [+] sshd       → sshd_backup_2026-04-20_09h00.conf
  [+] samba      → samba_backup_2026-04-20_09h00.conf
```

---

### `create_user.sh` — LDAP Bulk User Provisioning

**Language:** Bash  
**Location:** `infrastructure/scripts/create_user.sh`

**What it does:**
- Generates an LDIF file from a configured user list
- Injects entries into OpenLDAP via `ldapadd`
- Reads LDAP admin password from environment variable (no hardcoded secrets)

**Usage:**
```bash
LDAP_ADMIN_PW="yourpassword" bash create_user.sh
```

> Screenshot: [`../../screenshots/ldap-script-execution.png`](../../screenshots/ldap-script-execution.png)

---

## 2. Scheduling (Crontab)

Both scripts are scheduled via cron for daily automated execution.

```bash
crontab -e
```

```cron
# IRON-GRID — Daily automation (runs at 00:00 every day)
0 0 * * * python3 /opt/iron-grid/scripts/iron-check.py >> /var/log/iron-check.log 2>&1

# Weekly backup cleanup — keep only last 14 days
0 1 * * 0 find /var/backups/iron_grid/ -mtime +14 -delete
```

> Screenshot: [`../../screenshots/crontab-config.png`](../../screenshots/crontab-config.png)  
> Screenshot: [`../../screenshots/automation-success.png`](../../screenshots/automation-success.png)

---

## 3. FortiGate Config Backup

A separate backup mechanism handles FortiGate config exports. On the FortiGate CLI:

```bash
# Enable SCP-based config backup
config system global
    set admin-scp enable
end

# From the Ubuntu server, pull the config via SCP:
scp admin@192.168.122.99:sys_config /var/backups/iron_grid/fortigate_backup_$(date +%Y%m%d).conf
```

This produces the timestamped `.conf` files stored in `infrastructure/configs/`.

---

## 4. Log Monitoring

The `iron-check.py` output is logged for audit trail:

```bash
tail -f /var/log/iron-check.log
```

Wazuh also monitors this log file for any `[✘]` patterns that indicate service failures, generating an alert if a service goes down between cron runs.
