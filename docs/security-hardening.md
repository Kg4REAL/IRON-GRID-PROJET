# 🛡️ Security Hardening Guide — IRON-GRID

This document details the security hardening measures applied to the primary **Ubuntu Server (10.1.20.10)** running the core infrastructure services (LDAP, DNS, Samba, Nginx). The goal is to minimize the attack surface and guarantee service integrity across all layers.

---

## 1. OS Hardening

### Update & Patch Management
- Automated security patching enabled via `unattended-upgrades`:
```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

### Attack Surface Reduction
Unnecessary services disabled to eliminate unused entry points:
```bash
sudo systemctl disable avahi-daemon cups bluetooth
sudo systemctl stop avahi-daemon cups bluetooth
```

---

## 2. Network Access Control (UFW)

Default policy: **deny-all inbound, allow-all outbound**.

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

| Service | Port | Protocol | Justification |
|---------|------|----------|---------------|
| SSH | 2222 | TCP | Admin access (non-standard port) |
| DNS | 53 | TCP/UDP | Internal name resolution |
| LDAP | 389 | TCP | Centralized authentication |
| Samba | 445 | TCP | File sharing |
| HTTP/S | 80, 443 | TCP | Portfolio / web interface |

```bash
sudo ufw allow 2222/tcp
sudo ufw allow 53
sudo ufw allow 389/tcp
sudo ufw allow 445/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

Verify:
```bash
sudo ufw status verbose
```

> Screenshot: [`../screenshots/security-hardening.png`](../screenshots/security-hardening.png)

---

## 3. SSH Hardening

All remote administration is secured through multiple layers:

### Key Changes in `/etc/ssh/sshd_config`
```
Port 2222
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
AllowUsers <your_admin_user>
```

Apply:
```bash
sudo systemctl restart ssh
```

### Key Generation (Ed25519)
```bash
ssh-keygen -t ed25519 -C "iron-grid-admin"
ssh-copy-id -p 2222 user@10.1.20.10
```

---

## 4. Brute-Force Protection (Fail2Ban)

Fail2Ban monitors SSH logs in real-time and dynamically injects ban rules into UFW.

### SSH Jail Configuration (`/etc/fail2ban/jail.local`)
```ini
[sshd]
enabled  = true
port     = 2222
filter   = sshd
logpath  = /var/log/auth.log
maxretry = 3
findtime = 600
bantime  = 3600
```

Verify active bans:
```bash
sudo fail2ban-client status sshd
```

**Tested result:** After 3 failed SSH attempts, the attacker IP is automatically banned for 1 hour via a UFW rule. Wazuh logs the event as a Level 7 alert.

---

## 5. Integrity Monitoring (Wazuh FIM)

Wazuh File Integrity Monitoring watches critical config files for unauthorized changes.

### Monitored Paths
```xml
<directories check_all="yes">/etc/ssh/sshd_config</directories>
<directories check_all="yes">/etc/bind/</directories>
<directories check_all="yes">/etc/ldap/</directories>
<directories check_all="yes">/etc/samba/smb.conf</directories>
```

**Tested result:** Manual modification of `/etc/ssh/sshd_config` triggered an immediate **Level 7 FIM alert** on the Wazuh dashboard within seconds.

---

## 6. Log Rotation

`logrotate` is configured to prevent disk saturation (local DoS via log flooding):

```bash
# /etc/logrotate.d/iron-grid
/var/log/auth.log
/var/log/syslog
/var/log/nginx/*.log {
    daily
    rotate 14
    compress
    missingok
    notifempty
    sharedscripts
}
```

---

## 7. Automated Health Check

The custom `iron-check.py` script validates the status of all critical services at boot and generates timestamped configuration backups:

```bash
python3 /opt/iron-grid/scripts/iron-check.py
```

> See [`../infrastructure/scripts/iron-check.py`](../infrastructure/scripts/iron-check.py)

---

## ✅ Hardening Status

| Control | Status | Standard |
|---------|--------|---------|
| Automated patching | ✅ Active | CIS 1.9 |
| Unnecessary services disabled | ✅ Active | CIS 2.x |
| UFW deny-all default | ✅ Active | CIS 3.5 |
| SSH non-standard port | ✅ Active | CIS 5.2 |
| Root login disabled | ✅ Active | CIS 5.2.8 |
| Password auth disabled | ✅ Active | CIS 5.2.11 |
| Fail2Ban active | ✅ Active | Custom |
| FIM (Wazuh) active | ✅ Active | CIS 5.3 |
| Log rotation configured | ✅ Active | CIS 4.2 |

> **Final status:** Server hardened to CIS Benchmark Level 1 baseline, adapted for lab environment.
