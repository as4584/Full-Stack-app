#!/bin/bash
# Setup passwordless sudo for Caddy restart
# Run this ONCE on the production server: sudo bash setup_caddy_sudoers.sh

set -e

echo "🔐 Setting up passwordless sudo for Caddy reload..."

# Get the current user
DEPLOY_USER="${SUDO_USER:-$USER}"

# Create sudoers file for Caddy management
cat > /etc/sudoers.d/caddy-reload << EOF
# Allow $DEPLOY_USER to reload/restart Caddy without password
$DEPLOY_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart caddy
$DEPLOY_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl reload caddy
$DEPLOY_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl status caddy
$DEPLOY_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop caddy
$DEPLOY_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl start caddy
EOF

# Set correct permissions (sudoers files must be 0440)
chmod 0440 /etc/sudoers.d/caddy-reload

# Validate sudoers syntax
if visudo -c -f /etc/sudoers.d/caddy-reload; then
    echo "✅ Sudoers file created successfully!"
    echo "✅ User '$DEPLOY_USER' can now run Caddy commands without password"
    echo ""
    echo "Test with: sudo systemctl restart caddy"
else
    echo "❌ ERROR: Invalid sudoers syntax!"
    rm /etc/sudoers.d/caddy-reload
    exit 1
fi
