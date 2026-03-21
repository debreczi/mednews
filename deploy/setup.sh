#!/usr/bin/env bash
# deploy/setup.sh — MedNews Ubuntu 24 LTS bootstrap
# Usage: sudo bash deploy/setup.sh
# Run from project root as root or with sudo
set -euo pipefail

APP_DIR="/opt/mednews"
APP_USER="mednews"
PYTHON="python3"
NODE_VERSION="20"

# ── Colors ──────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

info()    { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── Checks ──────────────────────────────────────────────────────────────────────

[[ $EUID -ne 0 ]] && error "This script must be run as root or with sudo."
[[ ! -d "$APP_DIR" ]] && error "Project directory $APP_DIR not found. Copy the project there first."

info "Starting MedNews setup on Ubuntu 24 LTS..."

# ── System packages ─────────────────────────────────────────────────────────────

info "Updating package lists..."
apt-get update -qq

info "Installing system dependencies..."
apt-get install -y --no-install-recommends \
    software-properties-common \
    curl \
    gnupg \
    ca-certificates \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    nginx \
    sqlite3

# ── Python (Ubuntu 24 ships with 3.12) ──────────────────────────────────────────

info "Installing Python 3 + venv..."
apt-get install -y --no-install-recommends \
    python3 \
    python3-venv \
    python3-dev \
    python3-pip

# Verify
$PYTHON --version || error "Python 3 installation failed."

# ── Node 20 (via NodeSource) ────────────────────────────────────────────────────

info "Installing Node.js $NODE_VERSION via NodeSource..."
curl -fsSL "https://deb.nodesource.com/setup_${NODE_VERSION}.x" | bash -
apt-get install -y nodejs
node --version || error "Node.js installation failed."
npm --version

# ── Create app user ─────────────────────────────────────────────────────────────

if ! id "$APP_USER" &>/dev/null; then
    info "Creating system user '$APP_USER'..."
    useradd --system --no-create-home --shell /usr/sbin/nologin "$APP_USER"
else
    info "User '$APP_USER' already exists, skipping."
fi

# ── Set up project directory ownership ─────────────────────────────────────────

info "Setting ownership of $APP_DIR to $APP_USER..."
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# ── Python virtual environment ──────────────────────────────────────────────────

info "Creating Python virtual environment..."
cd "$APP_DIR"
if [[ ! -d ".venv" ]]; then
    sudo -u "$APP_USER" $PYTHON -m venv .venv
fi

info "Installing Python dependencies..."
sudo -u "$APP_USER" .venv/bin/pip install --upgrade pip --quiet
sudo -u "$APP_USER" .venv/bin/pip install -r requirements.txt --quiet

# ── Playwright browsers ─────────────────────────────────────────────────────────

info "Installing Playwright system dependencies..."
.venv/bin/playwright install-deps chromium
info "Installing Playwright browsers..."
mkdir -p "$APP_DIR/.playwright-browsers"
chown "$APP_USER:$APP_USER" "$APP_DIR/.playwright-browsers"
PLAYWRIGHT_BROWSERS_PATH="$APP_DIR/.playwright-browsers" \
    sudo -u "$APP_USER" \
    PLAYWRIGHT_BROWSERS_PATH="$APP_DIR/.playwright-browsers" \
    HOME="$APP_DIR" \
    .venv/bin/playwright install chromium

# ── Environment file ────────────────────────────────────────────────────────────

if [[ ! -f "$APP_DIR/.env" ]]; then
    info "Creating .env from .env.example..."
    sudo -u "$APP_USER" cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    warn "============================================================"
    warn " ACTION REQUIRED: Edit $APP_DIR/.env before continuing!"
    warn " At minimum, set:"
    warn "   GROQ_API_KEY=<your Groq API key>"
    warn "   ADMIN_API_KEY=<a strong random string>"
    warn "   VITE_ADMIN_API_KEY=<same or different strong string>"
    warn "============================================================"
    read -rp "Press ENTER after editing .env to continue, or Ctrl+C to abort..."
else
    info ".env already exists, skipping."
fi

# ── Database migration ──────────────────────────────────────────────────────────

info "Running Alembic migrations (alembic upgrade head)..."
cd "$APP_DIR"
sudo -u "$APP_USER" .venv/bin/alembic upgrade head

# ── Seed sources ────────────────────────────────────────────────────────────────

info "Seeding news sources..."
sudo -u "$APP_USER" .venv/bin/python -m backend.seeds.sources

# ── Build Vue frontend ──────────────────────────────────────────────────────────

info "Installing frontend dependencies..."
cd "$APP_DIR/frontend"
sudo -u "$APP_USER" npm install --silent

info "Building Vue frontend for production..."
sudo -u "$APP_USER" npm run build

# ── systemd service ─────────────────────────────────────────────────────────────

info "Installing systemd service..."
cp "$APP_DIR/deploy/mednews.service" /etc/systemd/system/mednews.service
systemctl daemon-reload
systemctl enable mednews
systemctl restart mednews
systemctl --no-pager status mednews || warn "Service may not have started cleanly — check: journalctl -u mednews"

# ── nginx configuration ─────────────────────────────────────────────────────────

info "Configuring nginx..."
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/mednews

# Remove default site if present
if [[ -L /etc/nginx/sites-enabled/default ]]; then
    rm /etc/nginx/sites-enabled/default
fi

ln -sf /etc/nginx/sites-available/mednews /etc/nginx/sites-enabled/mednews

nginx -t || error "nginx configuration test failed. Check $APP_DIR/deploy/nginx.conf."
systemctl enable nginx
systemctl reload nginx

# ── Done ────────────────────────────────────────────────────────────────────────

info "============================================================"
info " MedNews setup complete!"
info ""
info " Application directory : $APP_DIR"
info " API service           : systemctl status mednews"
info " Logs                  : journalctl -u mednews -f"
info " nginx config          : /etc/nginx/sites-available/mednews"
info ""
info " Next steps:"
info "   1. Update server_name in /etc/nginx/sites-available/mednews"
info "   2. Obtain TLS certificate: certbot --nginx -d yourdomain.com"
info "   3. Open firewall ports 80 and 443 if needed"
info "============================================================"
