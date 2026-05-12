#!/bin/bash
# One-shot setup script for the AVM AI Agent on Ubuntu VPS.
# Run as root. Usage: bash deploy/setup.sh <github-repo-url>
# Example:  bash deploy/setup.sh https://github.com/yourorg/avm-agent.git

set -euo pipefail

REPO_URL="${1:?Usage: $0 <github-repo-url>}"
APP_DIR="/opt/avm-agent"
APP_USER="avm"
DOMAIN="srv1504040.hstgr.cloud"
EMAIL="azeng@mba21.rsm.nl"

echo "=== 1. System packages ==="
apt-get update -qq
apt-get install -y python3.11 python3.11-venv python3-pip nginx certbot python3-certbot-nginx git

echo "=== 2. App user + directory ==="
id "$APP_USER" &>/dev/null || useradd --system --home "$APP_DIR" --shell /bin/bash "$APP_USER"
mkdir -p "$APP_DIR"

echo "=== 3. Clone / update repo ==="
if [ -d "$APP_DIR/.git" ]; then
    git -C "$APP_DIR" pull
else
    git clone "$REPO_URL" "$APP_DIR"
fi

echo "=== 4. Python venv + dependencies ==="
python3.11 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip --quiet
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt" --quiet

echo "=== 5. systemd services ==="
cp "$APP_DIR/deploy/avm-chainlit.service" /etc/systemd/system/
cp "$APP_DIR/deploy/avm-webhook.service"  /etc/systemd/system/
systemctl daemon-reload
systemctl enable avm-chainlit avm-webhook

echo "=== 6. nginx (HTTP only — HTTPS added after certbot) ==="
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/avm-agent
ln -sf /etc/nginx/sites-available/avm-agent /etc/nginx/sites-enabled/avm-agent
rm -f /etc/nginx/sites-enabled/default
# Temporarily serve HTTP so certbot can complete its ACME challenge
cat > /etc/nginx/sites-available/avm-agent-bootstrap <<'EOF'
server {
    listen 80;
    server_name srv1504040.hstgr.cloud;
    location / { return 200 "ok"; }
}
EOF
ln -sf /etc/nginx/sites-available/avm-agent-bootstrap /etc/nginx/sites-enabled/avm-agent
nginx -t
systemctl enable nginx
systemctl restart nginx

echo "=== 7. TLS certificate (Let's Encrypt) ==="
certbot certonly --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "$EMAIL"

echo "=== 8. Switch to full nginx config (HTTPS) ==="
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/avm-agent
ln -sf /etc/nginx/sites-available/avm-agent /etc/nginx/sites-enabled/avm-agent
rm -f /etc/nginx/sites-available/avm-agent-bootstrap
nginx -t
systemctl reload nginx

echo "=== 9. Permissions ==="
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

echo ""
echo "========================================================"
echo " Setup complete. Manual steps still required:"
echo "========================================================"
echo ""
echo "  From your LOCAL machine, copy secrets to the VPS:"
echo "    scp .env                        root@187.124.43.165:$APP_DIR/.env"
echo "    scp -r secrets/                 root@187.124.43.165:$APP_DIR/secrets/"
echo "    scp public/dpd_logo.png         root@187.124.43.165:$APP_DIR/public/dpd_logo.png"
echo ""
echo "  Then back on the VPS (as root):"
echo "    chown -R $APP_USER:$APP_USER $APP_DIR/.env $APP_DIR/secrets/ $APP_DIR/public/"
echo "    chmod 600 $APP_DIR/.env $APP_DIR/secrets/service_account.json"
echo "    systemctl start avm-chainlit avm-webhook"
echo "    sudo -u $APP_USER $APP_DIR/venv/bin/python $APP_DIR/ingest.py"
echo "    sudo -u $APP_USER $APP_DIR/venv/bin/python $APP_DIR/manage_users.py add <user> <pass> <role> <group>"
echo ""
echo "  Visit: https://$DOMAIN"
