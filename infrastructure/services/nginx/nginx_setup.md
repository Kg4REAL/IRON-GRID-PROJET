# 🌍 Nginx Web Server — Setup Guide

## Overview

Nginx hosts the internal **portfolio and project documentation** site for the IRON-GRID lab. It is hardened with security headers and integrated with the internal DNS (`portfolio.it.local`).

- **Domain:** `portfolio.it.local`
- **Root:** `/var/www/ibrahima-portfolio`
- **Port:** 80 (HTTP) — HTTPS planned with self-signed cert
- **Engine:** Nginx 1.10.3+

---

## 1. Installation

```bash
# Disable Apache2 first to avoid port 80 conflict
sudo systemctl stop apache2
sudo systemctl disable apache2

sudo apt install nginx -y
```

---

## 2. Virtual Host Configuration (`/etc/nginx/sites-available/iron-portfolio`)

```nginx
server {
    listen 80;
    server_name portfolio.it.local;

    root /var/www/ibrahima-portfolio;
    index index.html;

    # ── Security Headers ───────────────────────────────────────────────
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';" always;

    # ── Hide server version ────────────────────────────────────────────
    server_tokens off;

    location / {
        try_files $uri $uri/ =404;
    }

    # ── Block access to hidden files (.env, .git, etc.) ───────────────
    location ~ /\. {
        deny all;
        return 404;
    }
}
```

---

## 3. Enable & Deploy

```bash
# Create web root
sudo mkdir -p /var/www/ibrahima-portfolio
sudo chown -R www-data:www-data /var/www/ibrahima-portfolio

# Enable site
sudo ln -s /etc/nginx/sites-available/iron-portfolio /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test config syntax
sudo nginx -t

# Reload
sudo systemctl reload nginx
sudo systemctl enable nginx
```

---

## 4. DNS Integration

The site resolves via the internal BIND9 server:

```bash
# Forward zone entry (already in db.it.local)
portfolio   IN  CNAME   iron
```

From any VLAN 10/20 host:
```bash
curl http://portfolio.it.local
```

---

## 5. Verification

```bash
sudo nginx -t
sudo systemctl status nginx
curl -I http://portfolio.it.local
```

Expected headers in response:
```
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
```

> Screenshot: [`../../../screenshots/portfolio-conf.png`](../../../screenshots/portfolio-conf.png)  
> Screenshot: [`../../../screenshots/portfolio-preview.png`](../../../screenshots/portfolio-preview.png)

---

## 6. Next Step — HTTPS

```bash
# Generate self-signed cert (lab use only)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/iron-portfolio.key \
  -out /etc/ssl/certs/iron-portfolio.crt \
  -subj "/CN=portfolio.it.local/O=IRON-GRID/C=SN"
```

Then update the vhost to listen on 443 and add HSTS + TLS 1.3 only.
