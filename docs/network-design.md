# 🌐 Network Design & IP Plan — IRON-GRID

---

## 1. Executive Summary

IRON-GRID simulates a corporate HQ network with an isolated Branch office connected via IPSec VPN. All internet egress is managed through a FortiGate HA cluster. The design enforces **Zero-Trust** principles — no implicit trust between zones, all inter-VLAN traffic requires explicit firewall policy.

---

## 2. VLAN Segmentation

| VLAN | Name | Subnet | Gateway | Role |
|------|------|--------|---------|------|
| VLAN 10 | LAN_USERS | `10.1.10.0/24` | `10.1.10.1` | Employee workstations |
| VLAN 20 | SERVERS | `10.1.20.0/24` | `10.1.20.1` | Core services (DNS, LDAP, Samba, Monitoring) |
| VLAN 30 | GUESTS | `10.1.30.0/24` | `10.1.30.1` | Isolated guest internet access |
| N/A | MGMT | `192.168.122.0/24` | `192.168.122.1` | EVE-NG out-of-band management |

**Key isolation rule:** VLAN 30 (GUESTS) has zero access to VLAN 10 and VLAN 20. This is enforced at the FortiGate level with an explicit deny policy.

---

## 3. Host Inventory

| Hostname | IP Address | VLAN | Role |
|----------|-----------|------|------|
| `fg-active.it.local` | `192.168.122.99` / `10.1.10.1` | MGMT / Edge | FortiGate Master |
| `fg-passive.it.local` | `192.168.122.110` | MGMT | FortiGate Slave |
| `iron.it.local` | `10.1.20.10` | VLAN 20 | Ubuntu Server (DNS, LDAP, Samba, Nginx, Wazuh) |
| `kali.it.local` | `192.168.122.160` | MGMT | Attacker / Red Team machine |
| `honeypot.it.local` | `10.1.30.200` | VLAN 30 | Decoy (planned) |

---

## 4. WAN & Inter-Site Addressing

| Link | Network | Description |
|------|---------|-------------|
| FG-Active WAN1 | `1.1.1.0/30` | Primary uplink to ISP simulation |
| FG-Branch WAN2 | `11.11.11.0/30` | Branch primary uplink |
| HA Heartbeat | `2.2.2.0/30` | Dedicated sync link between FG nodes |
| Branch secondary | `22.22.22.0/30` | Branch backup uplink |
| IPSec VPN tunnel | `172.16.0.0/30` | HQ ↔ Branch encrypted overlay |

---

## 5. FortiGate Interface Mapping

| Interface | Type | VLAN/Role |
|-----------|------|-----------|
| `port1` | WAN | ISP uplink (DHCP/Static) |
| `port2` | HA | Heartbeat & config sync |
| `port4` | 802.1Q Trunk | Tagged traffic for VLAN 10, 20, 30 |
| `port4.10` | Subinterface | VLAN 10 gateway `10.1.10.1` |
| `port4.20` | Subinterface | VLAN 20 gateway `10.1.20.1` |
| `port4.30` | Subinterface | VLAN 30 gateway `10.1.30.1` |

---

## 6. DNS Architecture

- **Domain:** `it.local`
- **Authoritative server:** `iron.it.local` (`10.1.20.10`)
- **Upstream forwarder:** FortiGate (`10.1.10.1`) → Cloudflare (`1.1.1.1`)
- **Recursion:** Restricted to trusted subnets only (ACL in `named.conf.options`)
- **Zone transfer:** Disabled for unauthorized clients

> Full DNS config → [`../infrastructure/services/bind9/dns-setup.md`](../infrastructure/services/bind9/dns-setup.md)

---

## 7. SD-WAN Configuration

SD-WAN monitors WAN link health and routes traffic based on performance metrics:

| Rule | Metric | Action |
|------|--------|--------|
| Business-critical apps | Latency < 50ms | Route via WAN1 |
| Background traffic | Best available | Load balance WAN1/WAN2 |
| WAN1 failure | Link down detection | Failover to WAN2 within ~1s |

> Screenshot: [`../screenshots/sd-wan-usage.png`](../screenshots/sd-wan-usage.png)

---

## 8. Security Policy Matrix (Inter-VLAN)

| Source | Destination | Service | Action |
|--------|------------|---------|--------|
| VLAN 10 (Users) | VLAN 20 (Servers) | DNS, LDAP, SMB, HTTP | ALLOW + inspect |
| VLAN 10 (Users) | WAN | HTTP, HTTPS | ALLOW + web filter |
| VLAN 20 (Servers) | WAN | Updates, NTP | ALLOW |
| VLAN 30 (Guests) | WAN | HTTP, HTTPS | ALLOW |
| VLAN 30 (Guests) | VLAN 10/20 | Any | **DENY** |
| Any | Any | Any (unmatched) | **IMPLICIT DENY** |
