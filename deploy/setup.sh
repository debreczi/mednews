#!/usr/bin/env bash
# deploy/setup.sh — MedNews installer
# Usage: curl -fsSL https://raw.githubusercontent.com/debreczi/mednews/main/deploy/setup.sh | sudo bash
# Or:    sudo bash deploy/setup.sh
# Creates a MedNews/ directory in the current working directory.
set -euo pipefail

REPO="https://github.com/debreczi/mednews.git"
INSTALL_DIR="$(pwd)/MedNews"
RUN_USER="${SUDO_USER:-$USER}"
PORT="${PORT:-8000}"

RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

[[ $EUID -ne 0 ]] && error "Run with sudo: sudo bash setup.sh"

info "Installing MedNews into $INSTALL_DIR (running as $RUN_USER)..."

# ── System packages ──────────────────────────────────────────────────────────
info "Installing system packages..."
apt-get update -qq
apt-get install -y --no-install-recommends \
    curl git build-essential \
    python3 python3-venv python3-dev \
    sqlite3

# ── Node 20 ─────────────────────────────────────────────────────────────────
if ! command -v node &>/dev/null; then
    info "Installing Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi
info "Node $(node --version) / npm $(npm --version)"

# ── Clone repo ───────────────────────────────────────────────────────────────
if [[ -d "$INSTALL_DIR" ]]; then
    info "Directory exists, pulling latest..."
    git -C "$INSTALL_DIR" pull
else
    info "Cloning repository..."
    git clone "$REPO" "$INSTALL_DIR"
fi
chown -R "$RUN_USER:$RUN_USER" "$INSTALL_DIR"

# ── Python venv ──────────────────────────────────────────────────────────────
info "Setting up Python environment..."
cd "$INSTALL_DIR"
sudo -u "$RUN_USER" python3 -m venv .venv
sudo -u "$RUN_USER" .venv/bin/pip install --upgrade pip -q
sudo -u "$RUN_USER" .venv/bin/pip install -r requirements.txt -q

# ── Playwright ───────────────────────────────────────────────────────────────
info "Installing Playwright..."
.venv/bin/playwright install-deps chromium
sudo -u "$RUN_USER" .venv/bin/playwright install chromium

# ── .env ─────────────────────────────────────────────────────────────────────
if [[ ! -f "$INSTALL_DIR/.env" ]]; then
    sudo -u "$RUN_USER" cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
    warn "────────────────────────────────────────────────────────"
    warn " Edit $INSTALL_DIR/.env"
    warn " Set: GROQ_API_KEY and ADMIN_API_KEY"
    warn "────────────────────────────────────────────────────────"
    read -rp "Press ENTER after editing .env to continue..."
else
    info ".env exists, skipping."
fi

# ── DB + seed ────────────────────────────────────────────────────────────────
info "Running database migrations..."
sudo -u "$RUN_USER" .venv/bin/alembic upgrade head

info "Seeding news sources..."
sudo -u "$RUN_USER" .venv/bin/python -m backend.seeds.sources

# ── Frontend build ───────────────────────────────────────────────────────────
info "Building frontend..."
cd "$INSTALL_DIR/frontend"
sudo -u "$RUN_USER" npm install --no-fund --no-audit
sudo -u "$RUN_USER" npm run build

# ── systemd service ──────────────────────────────────────────────────────────
info "Installing systemd service..."
cat > /etc/systemd/system/mednews.service <<EOF
[Unit]
Description=MedNews
After=network.target

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
Environment=PORT=$PORT
ExecStart=$INSTALL_DIR/.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port $PORT
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable mednews
systemctl restart mednews
sleep 2
systemctl --no-pager status mednews

# ── Done ─────────────────────────────────────────────────────────────────────
SERVER_IP=$(hostname -I | awk '{print $1}')
info "────────────────────────────────────────────────────────"
info " MedNews is running at http://$SERVER_IP:$PORT"
info " Logs:   journalctl -u mednews -f"
info " Stop:   sudo systemctl stop mednews"
info " Update: cd $INSTALL_DIR && git pull && sudo systemctl restart mednews"
info "────────────────────────────────────────────────────────"
