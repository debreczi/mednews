#!/usr/bin/env bash
# deploy/setup.sh — MedNews Ubuntu 24 LTS setup
# Usage: bash deploy/setup.sh   (no sudo needed — only apt steps use sudo internally)
set -euo pipefail

APP_DIR="/opt/mednews"
RUN_USER="${SUDO_USER:-$USER}"

RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

[[ $EUID -ne 0 ]] && error "Run with sudo: sudo bash deploy/setup.sh"
[[ ! -d "$APP_DIR" ]] && error "$APP_DIR not found. Clone the repo there first."

info "Setting up MedNews for user: $RUN_USER"

# ── System packages ──────────────────────────────────────────────────────────
info "Installing system packages..."
apt-get update -qq
apt-get install -y --no-install-recommends \
    curl gnupg ca-certificates git build-essential \
    libssl-dev libffi-dev python3 python3-venv python3-dev \
    nginx sqlite3

# ── Node 20 ─────────────────────────────────────────────────────────────────
if ! command -v node &>/dev/null; then
    info "Installing Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi
info "Node $(node --version), npm $(npm --version)"

# ── Ownership: give the real user full control ───────────────────────────────
info "Setting $APP_DIR ownership to $RUN_USER..."
chown -R "$RUN_USER:$RUN_USER" "$APP_DIR"

# ── Python venv ──────────────────────────────────────────────────────────────
info "Creating Python virtual environment..."
cd "$APP_DIR"
sudo -u "$RUN_USER" python3 -m venv .venv
sudo -u "$RUN_USER" .venv/bin/pip install --upgrade pip --quiet
sudo -u "$RUN_USER" .venv/bin/pip install -r requirements.txt --quiet

# ── Playwright ───────────────────────────────────────────────────────────────
info "Installing Playwright system dependencies..."
.venv/bin/playwright install-deps chromium
info "Installing Playwright browsers..."
sudo -u "$RUN_USER" .venv/bin/playwright install chromium

# ── .env ─────────────────────────────────────────────────────────────────────
if [[ ! -f "$APP_DIR/.env" ]]; then
    sudo -u "$RUN_USER" cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    warn "======================================================"
    warn " Edit $APP_DIR/.env — set GROQ_API_KEY + ADMIN_API_KEY"
    warn "======================================================"
    read -rp "Press ENTER after editing .env to continue..."
else
    info ".env already exists, skipping."
fi

# ── DB migration + seed ──────────────────────────────────────────────────────
info "Running database migrations..."
sudo -u "$RUN_USER" .venv/bin/alembic upgrade head

info "Seeding news sources..."
sudo -u "$RUN_USER" .venv/bin/python -m backend.seeds.sources

# ── Frontend build ───────────────────────────────────────────────────────────
info "Building Vue frontend..."
cd "$APP_DIR/frontend"
sudo -u "$RUN_USER" npm install
sudo -u "$RUN_USER" npm run build

# ── systemd service ──────────────────────────────────────────────────────────
info "Installing systemd service..."
# Stamp the real username into the service file
sed "s/User=mednews/User=$RUN_USER/; s/Group=mednews/Group=$RUN_USER/" \
    "$APP_DIR/deploy/mednews.service" > /etc/systemd/system/mednews.service
systemctl daemon-reload
systemctl enable mednews
systemctl restart mednews
systemctl --no-pager status mednews || warn "Check: journalctl -u mednews"

# ── nginx ────────────────────────────────────────────────────────────────────
info "Configuring nginx..."
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/mednews
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/mednews /etc/nginx/sites-enabled/mednews
nginx -t || error "nginx config invalid. Check $APP_DIR/deploy/nginx.conf"
systemctl enable nginx
systemctl restart nginx

# ── Done ─────────────────────────────────────────────────────────────────────
SERVER_IP=$(hostname -I | awk '{print $1}')
info "========================================================"
info " MedNews is live!"
info " Open: http://$SERVER_IP"
info " Logs: journalctl -u mednews -f"
info " Update: cd $APP_DIR && git pull && sudo bash deploy/setup.sh"
info "========================================================"
