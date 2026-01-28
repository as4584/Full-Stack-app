#!/bin/bash
# GitHub SSH Key Setup Helper
# This script helps you set up SSH authentication for GitHub Actions deployment

set -e

echo "🔐 GitHub Actions SSH Key Setup Helper"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SERVER_IP="104.236.100.245"
SERVER_USER="root"

echo -e "${BLUE}This script will help you set up SSH authentication for GitHub Actions${NC}"
echo "Server: $SERVER_USER@$SERVER_IP"
echo ""

# Check if we can connect to the server
echo -e "${YELLOW}1. Testing current SSH connection to server...${NC}"
if ssh -o BatchMode=yes -o ConnectTimeout=10 $SERVER_USER@$SERVER_IP "echo 'Connection successful'" 2>/dev/null; then
    echo -e "${GREEN}✅ SSH connection to server works${NC}"
else
    echo -e "${RED}❌ Cannot connect to server with current SSH setup${NC}"
    echo "Make sure you can SSH to the server manually first: ssh $SERVER_USER@$SERVER_IP"
    exit 1
fi

# Generate a new SSH key for GitHub Actions
echo -e "${YELLOW}2. Generating new SSH key for GitHub Actions...${NC}"
SSH_KEY_NAME="github-actions-key"
if [ -f ~/.ssh/$SSH_KEY_NAME ]; then
    echo "SSH key already exists. Removing old key..."
    rm -f ~/.ssh/$SSH_KEY_NAME ~/.ssh/$SSH_KEY_NAME.pub
fi

ssh-keygen -t ed25519 -f ~/.ssh/$SSH_KEY_NAME -N "" -C "github-actions@$HOSTNAME"
echo -e "${GREEN}✅ SSH key generated${NC}"

# Add the key to the server
echo -e "${YELLOW}3. Adding public key to server...${NC}"
ssh-copy-id -i ~/.ssh/$SSH_KEY_NAME.pub $SERVER_USER@$SERVER_IP
echo -e "${GREEN}✅ Public key added to server${NC}"

# Test the new key
echo -e "${YELLOW}4. Testing new SSH key...${NC}"
if ssh -i ~/.ssh/$SSH_KEY_NAME -o BatchMode=yes -o ConnectTimeout=10 $SERVER_USER@$SERVER_IP "echo 'New key works!'" 2>/dev/null; then
    echo -e "${GREEN}✅ New SSH key works!${NC}"
else
    echo -e "${RED}❌ New SSH key failed${NC}"
    exit 1
fi

# Show the private key for GitHub secrets
echo ""
echo -e "${YELLOW}5. GitHub Secrets Configuration${NC}"
echo "================================"
echo ""
echo -e "${BLUE}Copy the following private key and add it to your GitHub repository secrets as 'SSH_PRIVATE_KEY':${NC}"
echo ""
echo -e "${YELLOW}Go to: GitHub repo → Settings → Secrets and variables → Actions → New repository secret${NC}"
echo -e "${YELLOW}Name: SSH_PRIVATE_KEY${NC}"
echo -e "${YELLOW}Value: (copy the entire key below, including BEGIN and END lines)${NC}"
echo ""
echo "--- COPY FROM HERE ---"
cat ~/.ssh/$SSH_KEY_NAME
echo "--- COPY TO HERE ---"
echo ""

# Verify the key format
echo -e "${YELLOW}6. Key verification${NC}"
echo "Key fingerprint:"
ssh-keygen -l -f ~/.ssh/$SSH_KEY_NAME
echo ""

# Show additional secrets needed
echo -e "${YELLOW}7. Additional GitHub Secrets Required${NC}"
echo "===================================="
echo "Make sure these secrets are also set in GitHub:"
echo ""
echo "HOST_IP: $SERVER_IP"
echo "DOMAIN: lexmakesit.com"
echo "EMAIL: your-email@domain.com"
echo "SECRET_KEY: $(openssl rand -base64 32)"
echo ""

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Add the SSH_PRIVATE_KEY secret to GitHub (shown above)"
echo "2. Verify other secrets are set correctly"
echo "3. Push your code to trigger GitHub Actions"
echo ""
echo -e "${YELLOW}Note: The private key file is saved as ~/.ssh/$SSH_KEY_NAME${NC}"
echo -e "${YELLOW}You can delete it after adding to GitHub secrets for security${NC}"