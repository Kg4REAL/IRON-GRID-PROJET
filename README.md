# 🛡️ IRON-GRID — Enterprise Network Lab with Purple Team Operations

> **Zero-Trust architecture meets Purple Team methodology** — Hardened enterprise network with FortiGate HA, Wazuh SIEM, and documented attack-defense scenarios in EVE-NG

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-EVE--NG-blue)](https://www.eve-ng.net/)
[![Firewall](https://img.shields.io/badge/Firewall-FortiGate%20HA-red)](https://www.fortinet.com/)
[![Monitoring](https://img.shields.io/badge/SIEM-Wazuh%20XDR-purple)](https://wazuh.com/)
[![Architecture](https://img.shields.io/badge/Design-Zero--Trust-green)](https://en.wikipedia.org/wiki/Zero_trust_security_model)
[![Status](https://img.shields.io/badge/Status-Production--Ready-brightgreen)]()

---

## 🎯 What is IRON-GRID?

**IRON-GRID** is a **professional-grade enterprise network lab** built from scratch on EVE-NG that simulates a real corporate infrastructure. It combines:

✅ **Blue Team** — Hardened network with layered defenses  
✅ **Red Team** — Real attack scenarios with full documentation  
✅ **Purple Team** — Attack → Detection → Tuning feedback loop  
✅ **Production-Ready** — Zero-Trust, HA, encryption, monitoring at every layer

This isn't a toy project — it's a **complete SOC simulation** you can learn from or replicate.

---

## 🏢 Real-World Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    IRON-GRID Enterprise Lab                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────  INTERNET (ISP 1 & 2) ─────────────┐   │
│  │                                                        │   │
│  ▼ WAN1 (Active)          ▼ WAN2 (Passive)              │   │
│  
│  ┌─────────────────────────────────────────────────────┐   │
│  │         FortiGate HA Cluster (Active/Passive)      │   │
│  │  FG-Active (Master)  ←→HA Sync ←→  FG-Passive     │   │
│  │     192.168.122.99         (Heartbeat)  .110      │   │
│  │                                                    │   │
│  │  ★ Zero-Trust Firewall                            │   │
│  │  ★ IPS/AV/Web Filter                              │   │
│  │  ★ LDAP Authentication                            │   │
│  │  ★ SD-WAN + IPSec VPN                             │   │
│  └─────┬─────────────────────────────────────────────┘   │
│        │                                                  │
│    ┌───┴────────────────────────────────────┐            │
│    │  Internal LAN (Zero-Trust Zone)        │            │
│    │                                         │            │
│    ├─ VLAN 10: Users (10.1.10.0/24)        │            │
│    ├─ VLAN 20: Servers (10.1.20.0/24)      │            │
│    ├─ VLAN 30: Guests (10.1.30.0/24)       │            │
│    │                                         │            │
│    └─ Wazuh SIEM + Services                │            │
│       (DNS, LDAP, Samba, Nginx)            │            │
│                                             │            │
│    🔴 Kali Linux (Red Team)                │            │
│       192.168.122.160 (Isolated Guest)     │            │
│                                             │            │
│  Implicit Deny → Explicit Allow Only       │            │
└────────────────────────────────────────────┘            │
```

---

## 🏗️ Network Design

### VLAN Segmentation & Zero-Trust

| Zone | VLAN | Subnet | Purpose | Trust Level |
|------|------|--------|---------|------------|
| **LAN_USERS** | 10 | 10.1.10.0/24 | Employee workstations | Low |
| **SERVERS** | 20 | 10.1.20.0/24 | DNS, LDAP, Samba, Monitoring | Medium |
| **GUESTS** | 30 | 10.1.30.0/24 | Guest + isolated test machines | Untrusted |
| **MGMT** | — | 192.168.122.0/24 | EVE-NG out-of-band management | Restricted |

### Firewall Rules Philosophy

**Default: DENY ALL**  
**Allow by exception** → Each inter-VLAN flow explicitly approved

```
Example Rules (FortiGate):
- VLAN 10 → VLAN 20: DNS (53), LDAP (389), SMB (445) only
- VLAN 30 → Others: Blocked (guests isolated)
- VLAN 20 → Internet: HTTP/HTTPS only (no SSH egress)
- All zones → SIEM: Syslog (514) for monitoring
```

### WAN Redundancy

| Link | Network | Purpose | Status |
|------|---------|---------|--------|
| **WAN1 (Active)** | 1.1.1.0/30 | Primary ISP connection | Primary |
| **WAN2 (Backup)** | 11.11.11.0/30 | Secondary ISP failover | Standby |
| **VPN Backup** | 22.22.22.0/30 | Branch secondary uplink | Reserved |

---

## 🛡️ Security Stack

### Perimeter Defense
- **FortiGate VM64-KVM HA** — Next-Gen Firewall (IPS, AV, Web Filter active)
- **Active/Passive Cluster** — Sub-second failover, synchronized state
- **Implicit Deny Architecture** — No inter-VLAN traffic unless explicitly allowed
- **LDAP Integration** — Centralized identity for firewall auth policies

### Identity & Access
- **OpenLDAP** — Centralized user/group management (dc=it,dc=local)
- **LDAPS Enforced** — TLS-encrypted LDAP (reject plain LDAP at firewall)
- **SSH Hardening** — Ed25519 keys only, non-standard port 2222, no root login
- **Fail2Ban + UFW** — Layer 2 host firewall with dynamic IPS injection

### Detection & Response
- **Wazuh SIEM/XDR** — Real-time threat detection
- **File Integrity Monitoring** — SSH configs, DNS zones, LDAP schema watched
- **FortiGate Log Ingestion** — All firewall events correlated with host events
- **Active Response** — Automated UFW blocks on detected brute-force sources

### Hardening Baseline
- **CIS Benchmark** applied to Ubuntu servers
- **Automatic security patching** via unattended-upgrades
- **Unnecessary services disabled** (avahi, cups, etc.)
- **Packet signing enforced** — SMBv1 disabled, Samba v3+ only

---

## ⚔️ Red Team: Attack Scenarios

All attacks originate from **Kali Linux** (192.168.122.160) on the isolated GUEST network. Each scenario includes commands, expected output, and detection bypass techniques.

### Phase 1: Reconnaissance ✅
```bash
# Stealth network scan
nmap -sV -sS -T2 10.1.10.0/24          # Service enumeration
nmap -O 10.1.20.0/24                   # OS fingerprinting
netstat -tan | grep LISTEN             # Internal port discovery

# Expected findings:
# - DNS (port 53) on 10.1.20.10
# - LDAP (port 389) on 10.1.20.11
# - SMB (port 445) on 10.1.20.12
# - HTTP (port 80) on 10.1.20.20
```

### Phase 2: Brute-Force SSH → Fail2Ban Trigger ⚠️
```bash
# Hydra password attack
hydra -l admin -P /usr/share/wordlists/rockyou.txt \
  -s 2222 10.1.20.10 ssh

# Wazuh Alert: "Brute-force attack detected"
# → Fail2Ban triggers after 3 failures
# → UFW dynamically blocks attacker IP
# → Session terminates, can't continue
```

### Phase 3: LDAP Enumeration 🔍
```bash
# Test anonymous LDAP bind
ldapsearch -h 10.1.20.11 -x -b "dc=it,dc=local"

# FortiGate blocks anonymous LDAP (policy: LDAPS only)
# → Attack fails at firewall level
# → Wazuh logs unauthorized LDAP attempt
```

### Phase 4: SMB Enumeration & Null Session ⛔
```bash
# Try null session mount
smbclient -L //10.1.20.12 -U ""

# Result: Packet signing enforced → blocks unsigned SMB packets
# Samba only accepts SMBv3 with encryption
# → Attack fails, logged in Wazuh
```

### Phase 5: File Integrity Monitoring (FIM) Evasion 📝
```bash
# Attempt to modify SSH config
ssh -p 2222 admin@10.1.20.10
  $ sudo nano /etc/ssh/sshd_config    # Modify allowed users

# Wazuh FIM detects change immediately
# → Alert: "Unauthorized modification: /etc/ssh/sshd_config"
# → File automatically restored from backup
# → Attacker action is documented
```

### Phase 6: Lateral Movement (VLAN Pivot) 🔀
```bash
# From GUEST VLAN (10.1.30.0/24), try to reach USERS (10.1.10.0/24)
ping 10.1.10.5
  # Blocked by FortiGate policy (VLAN 30 has no egress)

# Try via compromised VLAN 20 host:
arp -a; route -n                       # Enumerate routing
# FortiGate ZERO-TRUST blocks inter-VLAN traffic
```

### Phase 7: DNS Tunneling (Exfiltration Test) 📤
```bash
# Use DNS to tunnel data out
iodine -f -r -P password 10.1.20.10

# FortiGate IPS detects DNS tunneling pattern
# → Connection blocked, alert triggered
# → Wazuh correlates multiple detection vectors
```

### Phase 8: Web Exploitation (SQLi + JWT Bypass) 🌐
```bash
# Test SQLi on portfolio app
sqlmap -u "http://portfolio.it.local/search?q=" --dbs

# Web Filter in FortiGate detects SQLi payload
# → Request blocked before reaching web server
# → Firewall logs malicious signature
```

---

## 📊 Attack-Defense Matrix

| # | Attack Technique | Blue Defense | Detection | Status |
|---|---|---|---|---|
| **01** | Network Scan | IPS signature matching | FortiGate IPS log | ✅ Detected |
| **02** | Brute-Force SSH | Fail2Ban + UFW block | Wazuh active response | ✅ Blocked & Logged |
| **03** | LDAP Enumeration | Firewall: deny anonymous | FortiGate policy deny | ✅ Rejected |
| **04** | SMB Null Session | SMBv3 + packet signing | Samba logs | ✅ Rejected |
| **05** | FIM Evasion | File integrity monitoring | Wazuh FIM alert + restore | ✅ Detected & Reverted |
| **06** | Lateral Movement | Zero-Trust inter-VLAN ACL | FortiGate drop log | ✅ Blocked |
| **07** | DNS Tunneling | IPS + DNS Filter | FortiGate signature match | ✅ Blocked |
| **08** | SQLi Injection | Web Filter + SQLi inspection | FortiGate Web Filter log | ✅ Blocked |

---

## 📁 Repository Structure

```
IRON-GRID-PROJET/
├── README.md                           # This file
├── topologie.png                       # EVE-NG visual topology
│
├── docs/                               # Detailed documentation
│   ├── 01-architecture.md              # Zero-Trust design philosophy
│   ├── 02-network-design.md            # IP plan, VLAN schema, routing
│   ├── 03-security-hardening.md        # Step-by-step hardening guide
│   ├── 04-fortigate-config.md          # HA cluster, policies, authentication
│   ├── 05-services-setup.md            # DNS, LDAP, Samba, Nginx
│   ├── 06-wazuh-deployment.md          # SIEM setup & custom rules
│   ├── 07-attack-vectors.md            # Detailed attack methodology
│   └── 08-pentest-report.md            # Purple Team assessment findings
│
├── infrastructure/                     # Configuration files
│   ├── fortigate/
│   │   ├── ha-cluster.conf             # Active/Passive cluster config
│   │   ├── firewall-policies.conf      # Zero-Trust inter-VLAN ACLs
│   │   ├── authentication.conf         # LDAP integration
│   │   ├── sd-wan.conf                 # Dual-WAN load balancing
│   │   ├── ipsec-vpn.conf              # Site-to-site VPN (HQ ↔ Branch)
│   │   └── ids-ips-config.conf         # IPS signatures & tuning
│   │
│   ├── services/
│   │   ├── bind9/
│   │   │   ├── setup.md                # Zone configuration
│   │   │   ├── named.conf              # ACLs & security
│   │   │   └── zones/it.local          # Internal domain
│   │   │
│   │   ├── openldap/
│   │   │   ├── setup.md                # LDAP installation
│   │   │   ├── slapd.conf              # Directory config
│   │   │   └── schema/it-users.ldif    # User & group schema
│   │   │
│   │   ├── samba/
│   │   │   ├── setup.md                # SMB configuration
│   │   │   ├── smb.conf                # Share definitions
│   │   │   └── ldap-mapping.conf       # LDAP permission sync
│   │   │
│   │   └── nginx/
│   │       ├── setup.md                # Vhost config
│   │       ├── nginx.conf              # Security headers, TLS
│   │       └── portfolio.it.local      # Internal portfolio app
│   │
│   ├── monitoring/
│   │   └── wazuh/
│   │       ├── setup.md                # SIEM deployment
│   │       ├── wazuh-agents.conf       # Agent configurations
│   │       ├── custom-rules.xml        # Detection rules (brute-force, FIM, DNS tunnel)
│   │       └── fortigate-decoder.xml   # FortiGate syslog parsing
│   │
│   ├── scripts/
│   │   ├── iron-check.py               # Service health check + backup automation
│   │   ├── create_users.sh             # Bulk LDAP user provisioning
│   │   ├── failover-test.sh            # HA failover simulation
│   │   └── compliance-check.sh         # CIS benchmark validator
│   │
│   └── automation/
│       └── cron-jobs.txt               # Backup, patch, health check scheduling
│
├── eve-ng/
│   └── topology.unl                    # Import this into EVE-NG
│
└── screenshots/                        # Proof & test results
    ├── 01-ha-failover-test.png         # HA failover working
    ├── 02-firewall-policies.png        # Inter-VLAN ACL rules
    ├── 03-wazuh-dashboard.png          # Live threat dashboard
    ├── 04-ssh-brute-force-blocked.png  # Fail2Ban in action
    ├── 05-ldap-enumeration-denied.png  # LDAP anonymous denied
    ├── 06-fim-change-detected.png      # SSH config modification caught
    └── 07-zerotrust-block-flow.png     # Lateral movement blocked
```

---

## 🚀 Quick Start

### Prerequisites
- EVE-NG (Community or Pro)
- 16GB RAM minimum (32GB recommended for smooth operation)
- 50GB free disk space
- VirtualBox or KVM backend

### Import & Launch Lab

**Step 1: Download the lab**
```bash
git clone https://github.com/Kg4REAL/IRON-GRID-PROJET.git
cd IRON-GRID-PROJET
```

**Step 2: Import topology into EVE-NG**
```
1. Open EVE-NG WebUI
2. Import → Upload topology.unl
3. Extract images (wait 10-15 minutes)
```

**Step 3: Start lab**
```
1. Click "Start Lab"
2. Wait for FortiGate HA sync (3-5 minutes)
3. Verify all devices are RUNNING (green status)
```

**Step 4: Access consoles**
- **FortiGate-Active**: `https://192.168.122.99` (admin/fortinet)
- **FortiGate-Passive**: `https://192.168.122.110`
- **Ubuntu-Server**: SSH → `ssh -p 2222 admin@192.168.122.100`
- **Kali-Linux**: SSH → `ssh root@192.168.122.160` (password: toor)
- **Wazuh Dashboard**: `https://192.168.122.50:443`

---

## 🎓 Learning Path

**Week 1: Infrastructure**
- [ ] Review network architecture (docs/01-architecture.md)
- [ ] Examine IP plan & VLAN design (docs/02-network-design.md)
- [ ] Understand FortiGate HA cluster (infrastructure/fortigate/)
- [ ] Test failover scenario

**Week 2: Services & Hardening**
- [ ] Deploy DNS (BIND9) with security ACLs
- [ ] Configure OpenLDAP identity management
- [ ] Set up Samba with LDAP-mapped permissions
- [ ] Apply CIS hardening baseline

**Week 3: Monitoring & Detection**
- [ ] Deploy Wazuh SIEM
- [ ] Configure FortiGate log ingestion
- [ ] Create custom detection rules
- [ ] Test File Integrity Monitoring (FIM)

**Week 4: Attack & Defense**
- [ ] Execute attack scenarios (docs/07-attack-vectors.md)
- [ ] Observe detection in Wazuh dashboard
- [ ] Review FortiGate blocking logs
- [ ] Document findings (docs/08-pentest-report.md)

---

## ✅ Completion Status

- [x] FortiGate HA Cluster (Active/Passive with sub-second failover)
- [x] VLAN segmentation (10, 20, 30) with Zero-Trust firewall
- [x] SD-WAN with dual-WAN link health monitoring
- [x] IPSec VPN (HQ ↔ Branch site-to-site)
- [x] OpenLDAP centralized identity + LDAPS enforcement
- [x] BIND9 DNS with security ACLs + DNSSEC ready
- [x] Samba SMBv3 with packet signing + LDAP mapping
- [x] Ubuntu hardening (CIS Benchmark, UFW, SSH keys)
- [x] Wazuh SIEM with FortiGate log ingestion + custom rules
- [x] Fail2Ban + Active Response automation
- [x] File Integrity Monitoring on critical configs
- [x] Red Team attack scenarios (8 phases) fully documented
- [x] Attack-Defense matrix with detection/blocking proof
- [ ] Advanced lateral movement (kerberoasting, delegation)
- [ ] Threat hunting playbooks
- [ ] Video walkthrough of attack-defense scenarios

---

## 📚 Technologies Deployed

| Category | Tools/Tech |
|----------|---|
| **Networking** | Cisco ASAv · BGP · OSPF · HSRP · VLAN · STP |
| **Firewall** | FortiGate (IPS, AV, Web Filter, AV, SSL Inspection) |
| **Identity** | OpenLDAP · LDAPS · SSH keys |
| **Directory Services** | BIND9 DNS · Samba SMB/CIFS |
| **Monitoring** | Wazuh SIEM · Elasticsearch · Kibana |
| **Host Defense** | UFW · Fail2Ban · CIS Benchmark |
| **Lab Environment** | EVE-NG · KVM · Terraform (infrastructure-as-code ready) |

---

## 🔒 Security & Compliance

- ✅ **Zero-Trust Architecture** — Implicit deny, explicit allow
- ✅ **Defense-in-Depth** — Multiple layers of security
- ✅ **Encryption Everywhere** — LDAPS, TLS, IPSec
- ✅ **Audit Logging** — All flows logged and analyzed
- ✅ **Active Response** — Automated threat blocking
- ✅ **CIS Baseline** — Operating system hardening
- ✅ **SIEM Integration** — Centralized threat detection

---

## 📝 Documentation

See `/docs/` for complete methodology:
- Network architecture & design principles
- Security hardening step-by-step
- FortiGate cluster configuration & failover
- Attack vectors with PoC commands
- Purple Team assessment findings
- Mitigation strategies

---

## 🤝 Contributing

Found an issue? Have improvements? Submit an issue or PR!

---

## 📞 Contact & Support

🔗 **GitHub**: [@Kg4REAL](https://github.com/Kg4REAL)  
🔗 **LinkedIn**: [Ibrahima Dia - Cybersecurity](https://www.linkedin.com/in/ibrahima-dia-cyber)  
📧 **Questions?** Open a GitHub issue

---

## 📜 License & Disclaimer

**License**: MIT  
**Educational Use Only** — This lab is designed for learning cybersecurity concepts. All attacks are performed in an isolated, controlled environment with no external connectivity.

**Ethical Use**: Use this knowledge responsibly. Unauthorized access to computer systems is illegal.

---

**Last Updated**: May 17, 2026  
**Status**: ✅ **Production-Ready** — Fully tested, hardened, documented
