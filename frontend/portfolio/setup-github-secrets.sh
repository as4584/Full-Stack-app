#!/bin/bash

# =============================================================================
# GitHub Secrets Setup Helper Script
# =============================================================================
# This script helps generate the values needed for GitHub repository secrets
# Run this script and copy the output values to your GitHub repository secrets
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_secret() {
    echo -e "${GREEN}Secret Name:${NC} $1"
    echo -e "${GREEN}Value:${NC} $2"
    echo ""
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_header "GitHub Secrets Generator for lexmakesit.com"

echo "This script will generate secure values for your GitHub repository secrets."
echo "Copy these values to: GitHub Repository → Settings → Secrets and variables → Actions"
echo ""

# Check dependencies
if ! command -v openssl &> /dev/null; then
    echo -e "${RED}Error: openssl is required but not installed.${NC}"
    exit 1
fi

if ! command -v ssh-keygen &> /dev/null; then
    echo -e "${RED}Error: ssh-keygen is required but not installed.${NC}"
    exit 1
fi

echo ""
print_header "REQUIRED SECRETS"

# Generate FastAPI secret key
SECRET_KEY=$(openssl rand -hex 32)
print_secret "SECRET_KEY" "$SECRET_KEY"

# Generate PostgreSQL password
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
print_secret "POSTGRES_PASSWORD" "$POSTGRES_PASSWORD"

# Fixed values for your setup
print_secret "HOST_IP" "104.236.100.245"
print_secret "DOMAIN" "lexmakesit.com"

# Values you need to provide
print_header "SECRETS YOU NEED TO PROVIDE"

print_secret "EMAIL" "your-email@example.com (replace with your actual email)"
print_secret "SMTP_USER" "your-email@gmail.com (replace with your Gmail)"
print_secret "SMTP_PASSWORD" "your-gmail-app-password (see instructions below)"

print_header "SSH KEY GENERATION"

# Generate SSH key
SSH_KEY_PATH="$HOME/.ssh/github_actions_lexmakesit"
if [ ! -f "$SSH_KEY_PATH" ]; then
    print_info "Generating SSH key pair..."
    ssh-keygen -t rsa -b 4096 -C "github-actions@lexmakesit.com" -f "$SSH_KEY_PATH" -N ""
    print_info "SSH key pair generated successfully!"
else
    print_warning "SSH key already exists at $SSH_KEY_PATH"
fi

echo ""
print_secret "SSH_PRIVATE_KEY" "$(cat $SSH_KEY_PATH)"

print_header "NEXT STEPS"

echo "1. Copy the SSH public key to your droplet:"
echo "   ssh-copy-id -i ${SSH_KEY_PATH}.pub root@104.236.100.245"
echo ""

echo "2. Test SSH connection:"
echo "   ssh -i $SSH_KEY_PATH root@104.236.100.245 'echo \"Connection successful\"'"
echo ""

echo "3. Get Gmail App Password:"
echo "   - Go to your Google Account settings"
echo "   - Enable 2-factor authentication"
echo "   - Go to Security → App passwords"
echo "   - Generate a new app password for 'Mail'"
echo "   - Use that password for SMTP_PASSWORD secret"
echo ""

echo "4. Add all secrets to GitHub:"
echo "   Repository → Settings → Secrets and variables → Actions → New repository secret"
echo ""

echo "5. Create production environment:"
echo "   Repository → Settings → Environments → New environment → 'production'"
echo ""

echo "6. Test deployment:"
echo "   git add . && git commit -m 'Add CI/CD' && git push origin main"
echo ""

print_header "SECURITY NOTES"
echo "- Keep the private key secure and never share it"
echo "- The secrets are only visible to GitHub Actions"
echo "- You can regenerate any of these values if needed"
echo "- Monitor your repository's Actions tab for deployment status"

echo ""
print_info "Setup complete! Your secrets are ready for GitHub Actions."

# Save values to a temporary file for easy copying
OUTPUT_FILE="/tmp/github_secrets_$(date +%s).txt"
cat > "$OUTPUT_FILE" << EOF
# GitHub Repository Secrets for lexmakesit.com Portfolio
# Copy these values to: Repository → Settings → Secrets and variables → Actions

SECRET_KEY=$SECRET_KEY
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
HOST_IP=104.236.100.245
DOMAIN=lexmakesit.com
EMAIL=your-email@example.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SSH_PRIVATE_KEY=$(cat $SSH_KEY_PATH)
EOF

echo ""
print_info "All values saved to: $OUTPUT_FILE"
print_warning "Remember to delete this file after copying the secrets!"
echo "rm $OUTPUT_FILE"