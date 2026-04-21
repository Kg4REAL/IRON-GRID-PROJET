# 🔐 OpenLDAP — Identity Management Setup

## Overview

OpenLDAP provides centralized **Identity & Access Management (IAM)** for the IRON-GRID infrastructure. All services (FortiGate, Samba, Nginx) authenticate against the same LDAP directory, creating a single source of truth for user identities.

- **Domain:** `dc=it,dc=local`
- **Server:** `iron.it.local` — `10.1.20.10`
- **Admin DN:** `cn=admin,dc=it,dc=local`
- **GUI:** phpLDAPadmin (Apache2 backend)

---

## 1. Installation

```bash
sudo apt update
sudo apt install slapd ldap-utils phpldapadmin -y
```

During installation, set the admin password when prompted. To reconfigure:

```bash
sudo dpkg-reconfigure slapd
```

Settings:
- Omit OpenLDAP server configuration? **No**
- DNS domain name: `it.local`
- Organization name: `iron-grid`
- Admin password: *(set via env — see security note below)*
- Database: **MDB**
- Remove DB when slapd is purged? **No**
- Move old database? **Yes**

---

## 2. Directory Structure

```
dc=it,dc=local
├── ou=Admins          ← IT administration accounts
│   └── cn=kg4real
└── ou=Users           ← Standard employee accounts
    ├── cn=moussa
    ├── cn=fatou
    └── cn=amadou
```

### Create OUs

```bash
# Save as base.ldif
cat > /tmp/base.ldif << EOF
dn: ou=Admins,dc=it,dc=local
objectClass: organizationalUnit
ou: Admins

dn: ou=Users,dc=it,dc=local
objectClass: organizationalUnit
ou: Users
EOF

ldapadd -x -D "cn=admin,dc=it,dc=local" -W -f /tmp/base.ldif
```

---

## 3. User Provisioning

Use the automated provisioning script:

```bash
LDAP_ADMIN_PW="yourpassword" bash infrastructure/scripts/create_user.sh
```

> ⚠️ Never hardcode passwords in scripts. Always pass credentials via environment variables.

To generate a secure hashed password for LDIF entries:
```bash
slappasswd -h {SSHA}
```

---

## 4. FortiGate Integration

The FortiGate authenticates admin users via LDAP. See [`../../fortigate/authentication.conf`](../../fortigate/authentication.conf) for the FortiGate-side config.

LDAP Group mapped:
- `ou=Admins,dc=it,dc=local` → FortiGate admin group `LDAP-Admins`

> Screenshot: [`../../../screenshots/fortigate-ldap-config.png`](../../../screenshots/fortigate-ldap-config.png)  
> Screenshot: [`../../../screenshots/ldap-tree-view.png`](../../../screenshots/ldap-tree-view.png)

---

## 5. Verification

```bash
# Test anonymous bind (should return nothing)
ldapsearch -x -H ldap://10.1.20.10 -b "dc=it,dc=local"

# Test authenticated query
ldapsearch -x -H ldap://10.1.20.10 -D "cn=admin,dc=it,dc=local" -W -b "dc=it,dc=local"

# List all users in ou=Users
ldapsearch -x -H ldap://10.1.20.10 -D "cn=admin,dc=it,dc=local" -W \
  -b "ou=Users,dc=it,dc=local" "(objectClass=inetOrgPerson)" cn uid
```

---

## 6. Hardening

- Anonymous bind returns no data (verified in pentest report)
- LDAPS (port 636) migration is pending — plain LDAP (389) currently in use for lab simplicity
- phpLDAPadmin restricted to `127.0.0.1` access only via Apache2 config

> **Next step:** Generate a self-signed TLS cert and enforce LDAPS across all LDAP consumers.
