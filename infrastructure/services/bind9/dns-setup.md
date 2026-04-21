# 🌐 Internal DNS — BIND9 Setup Guide

## Overview

BIND9 serves as the authoritative DNS server for the `it.local` internal domain. It provides **Service Discovery** for all infrastructure nodes, enabling communication via FQDNs instead of volatile IP addresses. This is a prerequisite for LDAPS and HTTPS certificate validation across the lab.

- **FQDN:** `iron.it.local`
- **Domain:** `it.local`
- **IP:** `10.1.20.10`
- **Upstream forwarder:** FortiGate (`10.1.10.1`) → Cloudflare (`1.1.1.1`)

---

## 1. Installation

```bash
sudo apt update && sudo apt install bind9 bind9utils bind9-doc -y
```

---

## 2. Hardening — ACL & Options (`/etc/bind/named.conf.options`)

Recursion is restricted to trusted internal subnets only, preventing DNS amplification attacks and cache poisoning from untrusted sources.

```bash
acl "trusted" {
    10.1.10.0/24;   # VLAN 10 — LAN_USERS
    10.1.20.0/24;   # VLAN 20 — SERVERS
    10.1.30.0/24;   # VLAN 30 — GUESTS
    127.0.0.1;      # Localhost
};

options {
    directory "/var/cache/bind";

    recursion yes;
    allow-query     { trusted; };
    allow-recursion { trusted; };

    forwarders {
        10.1.10.1;  # FortiGate SD-WAN gateway
    };

    dnssec-validation auto;
    listen-on-v6 { any; };

    # Hide BIND version from reconnaissance scans
    version "Not disclosed";
};
```

---

## 3. Zone Declaration (`/etc/bind/named.conf.local`)

```bash
zone "it.local" {
    type master;
    file "/etc/bind/zones/db.it.local";
};

zone "20.1.10.in-addr.arpa" {
    type master;
    file "/etc/bind/zones/db.10.1.20";
};
```

---

## 4. Forward Zone File (`/etc/bind/zones/db.it.local`)

```bash
$TTL    604800
@   IN  SOA     iron.it.local. admin.it.local. (
                    2026033101  ; Serial (YYYYMMDDNN)
                    604800      ; Refresh
                    86400       ; Retry
                    2419200     ; Expire
                    604800 )    ; Negative Cache TTL
;
@   IN  NS      iron.it.local.

; ── Core Infrastructure ──────────────────────────────
iron            IN  A       10.1.20.10
ldap            IN  CNAME   iron
dns             IN  CNAME   iron

; ── FortiGate Nodes ──────────────────────────────────
fortigate       IN  A       10.1.10.1
fg-active       IN  A       10.1.10.2
fg-passive      IN  A       10.1.10.3

; ── Monitoring Stack ─────────────────────────────────
grafana         IN  A       10.1.20.50
prometheus      IN  A       10.1.20.50
loki            IN  A       10.1.20.50

; ── Security ─────────────────────────────────────────
kali            IN  A       192.168.122.160
honeypot        IN  A       10.1.30.200
```

---

## 5. Verification

### Syntax validation (before restarting)

```bash
named-checkconf
named-checkzone it.local /etc/bind/zones/db.it.local
```

### Resolution tests

```bash
# Forward lookup
dig +short iron.it.local @localhost
dig +short ldap.it.local @localhost
dig +short fg-active.it.local @localhost

# Verify ACL blocks untrusted clients
# From an unauthorized subnet, this should return REFUSED:
dig @10.1.20.10 iron.it.local
```

### Proof — successful resolution

```
root@ubuntu:/etc/bind# dig @localhost iron.it.local

;; ANSWER SECTION:
iron.it.local.   604800  IN  A  10.1.20.10

;; SERVER: ::1#53(::1)
;; Query time: 0 msec
```

> Screenshot: [`../../../screenshots/dns-records.png`](../../../screenshots/dns-records.png)  
> Screenshot: [`../../../screenshots/dns-resolution-test.png`](../../../screenshots/dns-resolution-test.png)

---

## 6. Red Team Perspective

From an untrusted subnet (e.g., VLAN 30 or external attacker), the server **must refuse DNS queries** due to the ACL:

```bash
# Expected result from unauthorized source:
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: REFUSED
```

This prevents DNS zone enumeration and internal hostname disclosure to attackers who gain a foothold outside VLAN 10/20.
