# 📁 Samba File Server — Setup Guide

## Overview

Samba provides **SMB/CIFS file sharing** for the IRON-GRID infrastructure. Share permissions are mapped to OpenLDAP identities, providing centralized access control consistent with the rest of the lab.

- **Share name:** `IronGrid-Share`
- **Path:** `/srv/samba/shared_folder`
- **Server:** `iron.it.local` — `10.1.20.10`

---

## 1. Installation

```bash
sudo apt update && sudo apt install samba -y
```

---

## 2. Share Configuration (`/etc/samba/smb.conf`)

```ini
[global]
   workgroup = IRONLAB
   server string = IRON-GRID File Server
   security = user
   map to guest = never

   # Hardening
   server min protocol = SMB2     # SMBv1 disabled
   server signing = mandatory     # Enforce packet signing
   ntlm auth = no                 # Disable NTLM (NTLMv2 only)

   # LDAP backend (future phase — LDAPS)
   # passdb backend = ldapsam:ldap://iron.it.local
   # ldap suffix = dc=it,dc=local

[IronGrid-Share]
   path = /srv/samba/shared_folder
   valid users = @IronUsers
   read only = no
   create mask = 0660
   directory mask = 0770
   browseable = yes
   comment = IRON-GRID Shared Storage
```

---

## 3. Setup & Permissions

```bash
# Create share directory
sudo mkdir -p /srv/samba/shared_folder

# Create Samba group
sudo groupadd IronUsers

# Set permissions
sudo chown root:IronUsers /srv/samba/shared_folder
sudo chmod 2770 /srv/samba/shared_folder

# Add a user to Samba (must already exist on the system)
sudo smbpasswd -a moussa
sudo usermod -aG IronUsers moussa
```

---

## 4. Service Management

```bash
sudo systemctl enable smbd nmbd
sudo systemctl start smbd nmbd
sudo systemctl status smbd
```

---

## 5. Accessing the Share

**From Linux:**
```bash
smbclient //10.1.20.10/IronGrid-Share -U moussa
# Or mount permanently:
sudo mount -t cifs //10.1.20.10/IronGrid-Share /mnt/ironshare \
  -o username=moussa,uid=1000,gid=1000
```

**From Windows:**
```
\\10.1.20.10\IronGrid-Share
```

---

## 6. Verification

```bash
# List available shares
smbclient -L //10.1.20.10 -U moussa

# Test null session (should be rejected)
smbclient -L //10.1.20.10 -N
```

**Pentest result:** Null session enumeration was blocked. `enum4linux` returned no share list without valid credentials.

> Screenshot: [`../../../screenshots/samba-config.png`](../../../screenshots/samba-config.png)  
> Screenshot: [`../../../screenshots/samba_share-access.png`](../../../screenshots/samba_share-access.png)  
> Screenshot: [`../../../screenshots/samba-status.png`](../../../screenshots/samba-status.png)
