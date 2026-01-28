#!/bin/bash
# GitHub Secrets Validator
# This script helps diagnose GitHub Actions deployment issues

set -e

echo "🔍 GitHub Actions Deployment Diagnostics"
echo "======================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SERVER_IP="104.236.100.245"
DOMAIN="lexmakesit.com"

echo -e "${BLUE}Checking deployment configuration...${NC}"
echo ""

# Check 1: Server connectivity
echo -e "${YELLOW}1. Testing server connectivity...${NC}"
if ping -c 1 -W 3 $SERVER_IP >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Server $SERVER_IP is reachable${NC}"
else
    echo -e "${RED}❌ Server $SERVER_IP is not reachable${NC}"
fi

# Check 2: SSH connectivity
echo -e "${YELLOW}2. Testing SSH connectivity...${NC}"
if ssh -o BatchMode=yes -o ConnectTimeout=10 root@$SERVER_IP "echo 'SSH OK'" 2>/dev/null; then
    echo -e "${GREEN}✅ SSH connection works${NC}"
    
    # Check server Docker
    echo -e "${YELLOW}3. Checking Docker on server...${NC}"
    if ssh root@$SERVER_IP "docker --version" 2>/dev/null; then
        echo -e "${GREEN}✅ Docker is installed on server${NC}"
    else
        echo -e "${RED}❌ Docker is not available on server${NC}"
    fi
    
    # Check server disk space
    echo -e "${YELLOW}4. Checking server disk space...${NC}"
    ssh root@$SERVER_IP "df -h /" | tail -1
    
else
    echo -e "${RED}❌ SSH connection failed${NC}"
    echo "Common issues:"
    echo "  - SSH_PRIVATE_KEY secret is incorrect"
    echo "  - Public key not added to server's authorized_keys"
    echo "  - SSH key format is wrong (needs to be raw private key)"
fi

# Check 3: Domain configuration
echo -e "${YELLOW}5. Testing domain configuration...${NC}"
if nslookup $DOMAIN >/dev/null 2>&1; then
    DOMAIN_IP=$(nslookup $DOMAIN | grep -A 1 "Name:" | grep "Address:" | awk '{print $2}' | head -1)
    if [ "$DOMAIN_IP" = "$SERVER_IP" ]; then
        echo -e "${GREEN}✅ Domain $DOMAIN points to $SERVER_IP${NC}"
    else
        echo -e "${YELLOW}⚠️  Domain $DOMAIN points to $DOMAIN_IP (expected $SERVER_IP)${NC}"
    fi
else
    echo -e "${RED}❌ Domain $DOMAIN is not resolvable${NC}"
fi

# Check 4: Required files
echo -e "${YELLOW}6. Checking required files...${NC}"
for file in "Dockerfile" "main.py" "requirements.txt" "templates/index.html"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file exists${NC}"
    else
        echo -e "${RED}❌ $file is missing${NC}"
    fi
done

# Check 5: GitHub workflow
echo -e "${YELLOW}7. Checking GitHub workflow...${NC}"
if [ -f ".github/workflows/deploy.yml" ]; then
    echo -e "${GREEN}✅ GitHub workflow exists${NC}"
    
    # Check for required secrets in workflow
    echo "Required secrets in GitHub:"
    echo "  - SSH_PRIVATE_KEY (your server's SSH private key)"
    echo "  - HOST_IP ($SERVER_IP)"
    echo "  - DOMAIN ($DOMAIN)" 
    echo "  - EMAIL (your email)"
    echo "  - SECRET_KEY (random string for FastAPI)"
else
    echo -e "${RED}❌ GitHub workflow is missing${NC}"
fi

echo ""
echo -e "${BLUE}Troubleshooting Tips:${NC}"
echo "====================="
echo ""
echo -e "${YELLOW}If SSH authentication is failing:${NC}"
echo "1. Run: ./scripts/setup-github-ssh.sh"
echo "2. Copy the generated private key to GitHub secrets as 'SSH_PRIVATE_KEY'"
echo "3. Make sure to copy the ENTIRE key including BEGIN/END lines"
echo "4. The key should NOT be base64 encoded - use the raw key"
echo ""
echo -e "${YELLOW}If deployment still fails:${NC}"
echo "1. Check GitHub repo → Settings → Secrets and variables → Actions"
echo "2. Verify all required secrets are set"
echo "3. Check GitHub Actions logs for specific error messages"
echo ""
echo -e "${YELLOW}If you need to regenerate secrets:${NC}"
echo "SECRET_KEY: $(openssl rand -base64 32)"