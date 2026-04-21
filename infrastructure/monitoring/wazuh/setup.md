# 🛡️ Wazuh SIEM/XDR — Deployment Guide

## Overview

Wazuh acts as the central **Security Operations Center (SOC)** for IRON-GRID. It provides real-time threat detection, log correlation, file integrity monitoring (FIM), and active response across all infrastructure nodes.

- **Manager:** `iron.it.local` — `10.1.20.10`
- **Dashboard:** `https://10.1.20.10` (Wazuh built-in dashboard)
- **Indexer:** OpenSearch (bundled)
- **Last audit:** April 20, 2026

---

## 1. Architecture

```
[FortiGate HA] ──Syslog──►┐
[Ubuntu Server] ──Agent──►│  Wazuh Manager (10.1.20.10)
[Kali Linux]   ──Agent──►│       │
                           └───────┤
                                   ├── OpenSearch Indexer
                                   └── Wazuh Dashboard
```

---

## 2. Installation

```bash
# Install Wazuh manager (single-node deployment)
curl -sO https://packages.wazuh.com/4.7/wazuh-install.sh
sudo bash wazuh-install.sh -a
```

This installs: Wazuh Manager + Indexer + Dashboard in one step.

Default dashboard: `https://10.1.20.10` — credentials shown at end of install.

---

## 3. Key Security Capabilities

### A. File Integrity Monitoring (FIM)

Monitors critical config files for unauthorized changes. Any modification triggers an immediate alert.

**Monitored paths** (configured in `/var/ossec/etc/ossec.conf`):
```xml
<syscheck>
  <directories check_all="yes" realtime="yes">/etc/ssh/sshd_config</directories>
  <directories check_all="yes" realtime="yes">/etc/bind/</directories>
  <directories check_all="yes" realtime="yes">/etc/ldap/</directories>
  <directories check_all="yes" realtime="yes">/etc/samba/smb.conf</directories>
  <directories check_all="yes" realtime="yes">/etc/nginx/sites-available/</directories>
</syscheck>
```

**Tested:** Manual modification of `/etc/ssh/sshd_config` → Level 7 FIM alert in under 5 seconds.

---

### B. FortiGate Log Ingestion (Syslog)

FortiGate sends logs to Wazuh via UDP Syslog on port 514.

**FortiGate config:**
```
config log syslogd setting
    set status enable
    set server "10.1.20.10"
    set port 514
    set facility local7
end
```

**Wazuh rule IDs observed:**

| Rule ID | Event | Level |
|---------|-------|-------|
| 81612 | FortiGate config change | 10 |
| 81626 | Admin login success | 5 |
| 81619 | High traffic anomaly | 8 |

---

### C. Vulnerability Detection

Wazuh scans installed packages against the NVD CVE database continuously.

**Results from last scan:**
- Critical: 0
- High: 2 (outdated Django packages — patched)
- Medium: 5

---

### D. Active Response — Brute-Force Blocking

When Wazuh detects SSH brute-force activity (>3 failed attempts in 10 minutes), it automatically blocks the source IP via UFW:

```xml
<active-response>
  <command>firewall-drop</command>
  <location>local</location>
  <rules_id>5763</rules_id>
  <timeout>3600</timeout>
</active-response>
```

**Tested:** `hydra` attack from `192.168.122.160` → source IP blocked after 3rd failure, Wazuh alert generated, UFW DROP rule confirmed.

---

## 4. Dashboard Views

| View | Purpose |
|------|---------|
| Security Events | Real-time alert stream from all agents |
| Integrity Monitoring | File change history with diffs |
| Vulnerability Detection | CVE list by severity |
| Agents | Health status of all monitored nodes |

> Screenshot: [`../../../screenshots/security-hardening.png`](../../../screenshots/security-hardening.png)

---

## 5. Agent Deployment (on monitored hosts)

```bash
# On the Kali or any Ubuntu host to monitor:
curl -sO https://packages.wazuh.com/4.7/wazuh-agent_4.7.0-1_amd64.deb
sudo WAZUH_MANAGER='10.1.20.10' dpkg -i wazuh-agent_4.7.0-1_amd64.deb
sudo systemctl enable wazuh-agent
sudo systemctl start wazuh-agent
```

---

## 6. Status

| Capability | Status |
|-----------|--------|
| Manager installed | ✅ Active |
| FortiGate Syslog ingestion | ✅ Active |
| FIM on Ubuntu Server | ✅ Active |
| Active response (Fail2Ban integration) | ✅ Active |
| Vulnerability detection | ✅ Active |
| Agent on Kali | 📋 Planned |
