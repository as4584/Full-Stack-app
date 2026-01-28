#!/bin/bash
# GitHub Actions SSH Key Generator
# Generates a properly formatted SSH key for GitHub Actions secrets

set -e

echo "🔑 GitHub Actions SSH Key Generator"
echo "=================================="

SERVER_IP="104.236.100.245"

# Check if we can connect to server
echo "1. Testing connection to $SERVER_IP..."
if ! ping -c 1 -W 5 $SERVER_IP >/dev/null 2>&1; then
    echo "❌ Cannot reach server $SERVER_IP"
    exit 1
fi

echo "✅ Server is reachable"

# Generate a new SSH key specifically for GitHub Actions
echo "2. Generating new SSH key for GitHub Actions..."
KEY_NAME="github-actions-deploy-key"
rm -f ~/.ssh/$KEY_NAME ~/.ssh/$KEY_NAME.pub

ssh-keygen -t ed25519 -f ~/.ssh/$KEY_NAME -N "" -C "github-actions-deploy-$(date +%Y%m%d)"

echo "✅ SSH key generated"

# Test the key format
echo "3. Validating key format..."
if ssh-keygen -l -f ~/.ssh/$KEY_NAME >/dev/null 2>&1; then
    echo "✅ Key format is valid"
    ssh-keygen -l -f ~/.ssh/$KEY_NAME
else
    echo "❌ Key format validation failed"
    exit 1
fi

# Add key to server
echo "4. Adding public key to server..."
echo "You'll need to authenticate to add the key to the server."
ssh-copy-id -i ~/.ssh/$KEY_NAME.pub root@$SERVER_IP

# Test the new key
echo "5. Testing SSH authentication..."
if ssh -i ~/.ssh/$KEY_NAME -o BatchMode=yes -o ConnectTimeout=10 root@$SERVER_IP "echo 'SSH test successful'"; then
    echo "✅ SSH authentication works!"
else
    echo "❌ SSH authentication failed"
    exit 1
fi

echo ""
echo "🎯 GitHub Actions Configuration"
echo "=============================="
echo ""
echo "1. Go to your GitHub repository:"
echo "   Settings → Secrets and variables → Actions"
echo ""
echo "2. Create/Update the SSH_PRIVATE_KEY secret with this EXACT content:"
echo ""
echo "--- COPY FROM BELOW (including BEGIN/END lines) ---"
cat ~/.ssh/$KEY_NAME
echo "--- COPY TO ABOVE (including BEGIN/END lines) ---"
echo ""

echo "3. Verify other required secrets are set:"
echo "   HOST_IP: $SERVER_IP"
echo "   DOMAIN: lexmakesit.com"
echo "   EMAIL: your-email@domain.com"
echo "   SECRET_KEY: $(openssl rand -base64 32)"
echo ""

echo "4. The private key is saved as ~/.ssh/$KEY_NAME"
echo "   You can delete this file after copying to GitHub for security"
echo ""

echo "✅ Setup complete! Push to GitHub to test deployment."