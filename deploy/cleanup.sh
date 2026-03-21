#!/usr/bin/env bash
# deploy/cleanup.sh — Remove everything MedNews installed on this server
# Usage: sudo bash deploy/cleanup.sh
set -euo pipefail

echo "[cleanup] Stopping and disabling mednews service..."
systemctl stop mednews 2>/dev/null || true
systemctl disable mednews 2>/dev/null || true
rm -f /etc/systemd/system/mednews.service
systemctl daemon-reload

echo "[cleanup] Removing nginx config..."
rm -f /etc/nginx/sites-enabled/mednews
rm -f /etc/nginx/sites-available/mednews
ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default 2>/dev/null || true
nginx -t 2>/dev/null && systemctl reload nginx || true

echo "[cleanup] Removing mednews system user..."
userdel mednews 2>/dev/null || true

echo "[cleanup] Removing /opt/mednews..."
rm -rf /opt/mednews

echo "[cleanup] Done. Server is clean."
