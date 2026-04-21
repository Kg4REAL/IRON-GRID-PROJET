#!/usr/bin/env python3
"""
iron-check.py — IRON-GRID Service Health Monitor & Config Backup Utility

Checks the status of critical infrastructure services and creates
timestamped backups of key configuration files.

Usage:
    python3 iron-check.py            # Run health check + backup
    python3 iron-check.py --check    # Health check only
    python3 iron-check.py --backup   # Backup only

Author: Ibrahima Dia
Project: IRON-GRID
"""

import os
import sys
import subprocess
import datetime
import argparse
import shutil


# ─── Configuration ────────────────────────────────────────────────────────────

SERVICES = ["nginx", "bind9", "smbd", "slapd", "fail2ban", "wazuh-agent"]

BACKUP_DIR = "/var/backups/iron_grid"

CONFIG_FILES = {
    "dns":   "/etc/bind/zones/db.it.local",
    "nginx": "/etc/nginx/sites-available/default",
    "sshd":  "/etc/ssh/sshd_config",
    "samba": "/etc/samba/smb.conf",
}

TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d_%Hh%M")


# ─── Core Functions ────────────────────────────────────────────────────────────

def check_service(service: str) -> str:
    """Return the systemctl is-active status of a service."""
    try:
        proc = subprocess.Popen(
            ["systemctl", "is-active", service],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, _ = proc.communicate()
        return stdout.decode("utf-8").strip()
    except Exception as e:
        return f"error ({e})"


def run_health_check() -> bool:
    """
    Check all configured services and print a status report.
    Returns True if all services are active, False otherwise.
    """
    print(f"\n{'═' * 50}")
    print(f"  IRON-GRID SYSTEM AUDIT — {TIMESTAMP}")
    print(f"{'═' * 50}")

    all_ok = True
    for service in SERVICES:
        state = check_service(service)
        if state == "active":
            status_icon = "✔"
            label = "ACTIVE"
        else:
            status_icon = "✘"
            label = state.upper()
            all_ok = False
        print(f"  [{status_icon}] {service:<20} {label}")

    print(f"{'─' * 50}")
    overall = "ALL SYSTEMS OPERATIONAL" if all_ok else "⚠ ONE OR MORE SERVICES DOWN"
    print(f"  {overall}")
    print(f"{'═' * 50}\n")

    return all_ok


def run_backup():
    """Create timestamped backups of critical configuration files."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    print(f"[*] Starting config backup → {BACKUP_DIR}")
    success_count = 0

    for name, src_path in CONFIG_FILES.items():
        if not os.path.isfile(src_path):
            print(f"  [!] Skipped {name}: source not found ({src_path})")
            continue

        dest_filename = f"{name}_backup_{TIMESTAMP}.conf"
        dest_path = os.path.join(BACKUP_DIR, dest_filename)

        try:
            shutil.copy2(src_path, dest_path)
            print(f"  [+] {name:<10} → {dest_filename}")
            success_count += 1
        except PermissionError:
            print(f"  [!] {name:<10} → Permission denied (run as root?)")
        except Exception as e:
            print(f"  [!] {name:<10} → Failed: {e}")

    print(f"\n[+] Backup complete: {success_count}/{len(CONFIG_FILES)} files saved.\n")


# ─── CLI Entry Point ───────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="IRON-GRID Service Health Monitor & Config Backup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run service health check only (no backup)",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Run config backup only (no health check)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Default: run both if no flag is specified
    if not args.check and not args.backup:
        args.check = True
        args.backup = True

    exit_code = 0

    if args.check:
        all_ok = run_health_check()
        if not all_ok:
            exit_code = 1

    if args.backup:
        run_backup()

    sys.exit(exit_code)
