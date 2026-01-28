# GitHub Actions CI/CD Setup Guide

## 🚀 Automated Deployment for lexmakesit.com

This guide will set up automatic deployment to your DigitalOcean droplet at `104.236.100.245` whenever you push to the main branch.

---

## 📋 Prerequisites

1. **GitHub Repository**: Your portfolio code in a GitHub repository
2. **DigitalOcean Droplet**: Server at `104.236.100.245` with Docker installed
3. **Domain**: `lexmakesit.com` pointing to your droplet
4. **SSH Access**: Root access to your droplet

---

## 🔐 Step 1: Generate SSH Key for GitHub Actions

On your local machine or the droplet, generate a new SSH key pair:

```bash
# Generate SSH key for CI/CD
ssh-keygen -t rsa -b 4096 -C "github-actions@lexmakesit.com" -f ~/.ssh/github_actions_key

# Copy the public key to your droplet
ssh-copy-id -i ~/.ssh/github_actions_key.pub root@104.236.100.245

# Test the connection
ssh -i ~/.ssh/github_actions_key root@104.236.100.245 "echo 'SSH connection successful'"
```

**Copy the private key content:**
```bash
cat ~/.ssh/github_actions_key
```
Save this for the GitHub secrets setup.

---

## 🔧 Step 2: Prepare Your Droplet

SSH into your droplet and set up the deployment directory:

```bash
ssh root@104.236.100.245

# Install Docker and Docker Compose if not already installed
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create deployment directory
mkdir -p /opt/portfolio
cd /opt/portfolio

# Set up directory permissions
chown -R root:root /opt/portfolio
chmod 755 /opt/portfolio
```

---

## 🔑 Step 3: Configure GitHub Repository Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these **Repository Secrets**:

### Required Secrets:

| Secret Name | Value | Purpose |
|-------------|-------|---------|
| `SSH_PRIVATE_KEY` | Your private key content | SSH access to droplet |
| `HOST_IP` | `104.236.100.245` | Your droplet IP address |
| `DOMAIN` | `lexmakesit.com` | Your domain name |
| `EMAIL` | `your-email@example.com` | For SSL certificates |
| `SECRET_KEY` | `$(openssl rand -hex 32)` | FastAPI secret key |
| `POSTGRES_PASSWORD` | `$(openssl rand -base64 32)` | Database password |
| `SMTP_USER` | `your-email@gmail.com` | SMTP username |
| `SMTP_PASSWORD` | `your-app-password` | Gmail app password |

### Generate Secure Values:

```bash
# Generate FastAPI secret key
openssl rand -hex 32

# Generate PostgreSQL password  
openssl rand -base64 32

# Get Gmail App Password
# 1. Go to Google Account settings
# 2. Enable 2-factor authentication
# 3. Generate an "App Password" for Mail
```

---

## 🔒 Step 4: Set Up Environment Protection

In your GitHub repository:

1. Go to **Settings** → **Environments**
2. Create a new environment called `production`
3. Add **Protection Rules**:
   - ✅ Required reviewers (optional, for extra safety)
   - ✅ Wait timer: 0 minutes (or add delay if desired)
4. Add **Environment Secrets** (same as above, but environment-specific)

---

## 📦 Step 5: Update Your Repository

Add these files to your repository:

### 1. Create `.github/workflows/deploy.yml`
This workflow file has been created above.

### 2. Update your Dockerfile (if needed)
Ensure your Dockerfile includes the health check:

```dockerfile
# Add health check instruction
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8001/api/health || exit 1
```

### 3. Update requirements.txt
Add testing dependencies:

```txt
# Testing dependencies  
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
```

---

## 🚀 Step 6: Test the Deployment

1. **Push to main branch**:
   ```bash
   git add .
   git commit -m "Add CI/CD workflow"
   git push origin main
   ```

2. **Monitor the deployment**:
   - Go to your repository → Actions tab
   - Watch the workflow run
   - Check each step for any errors

3. **Verify the deployment**:
   ```bash
   # Check if site is live
   curl -I https://lexmakesit.com
   
   # Check health endpoint
   curl https://lexmakesit.com/api/health
   ```

---

## 🔍 Workflow Overview

### **Pipeline Stages:**

1. **🧪 Test Stage**:
   - Runs Python linting (flake8, black, isort)
   - Security scanning (bandit, safety)
   - Unit tests (pytest)
   - Import validation

2. **🏗️ Build Stage**:
   - Builds Docker image
   - Pushes to GitHub Container Registry
   - Tags with commit SHA and 'latest'

3. **🚀 Deploy Stage**:
   - Copies files to droplet via SSH
   - Creates/updates environment files
   - Pulls latest Docker image
   - Graceful service restart
   - Health check verification
   - Cleanup old images

4. **🔐 Security Stage**:
   - Container vulnerability scanning (Trivy)
   - Uploads results to GitHub Security tab

---

## 📊 Monitoring and Troubleshooting

### **Check Deployment Status:**
```bash
# SSH into your droplet
ssh root@104.236.100.245

# Check running containers
cd /opt/portfolio && docker-compose ps

# Check logs
docker-compose logs -f web
docker-compose logs -f nginx
docker-compose logs -f db

# Check health status
curl http://localhost:8001/api/health
curl https://lexmakesit.com/api/health
```

### **Common Issues:**

1. **SSH Key Issues**:
   ```bash
   # Test SSH connection manually
   ssh -i ~/.ssh/github_actions_key root@104.236.100.245
   ```

2. **Docker Registry Authentication**:
   ```bash
   # Login manually on droplet
   echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
   ```

3. **SSL Certificate Issues**:
   ```bash
   # Check certificate status
   docker-compose exec nginx nginx -t
   docker-compose logs certbot
   ```

4. **Database Connection Issues**:
   ```bash
   # Check database status
   docker-compose exec db pg_isready -U portfolio_user
   ```

---

## 🎯 Workflow Features

### **Security Features:**
- ✅ Docker secrets (no env var exposure)
- ✅ Vulnerability scanning with Trivy
- ✅ Code security analysis with Bandit
- ✅ SSH key authentication
- ✅ Environment protection rules

### **Performance Features:**
- ✅ Docker layer caching
- ✅ Graceful container restarts
- ✅ Health check verification
- ✅ Automatic cleanup of old images

### **Reliability Features:**
- ✅ Multi-stage testing before deployment
- ✅ Rollback capability if health checks fail
- ✅ Timeout protection for all operations
- ✅ Detailed logging and monitoring

---

## 🔄 Manual Operations

### **Manual Deployment Trigger:**
You can manually trigger deployment from GitHub Actions tab using the "Run workflow" button.

### **Rollback Procedure:**
```bash
# SSH to droplet
ssh root@104.236.100.245
cd /opt/portfolio

# Check previous images
docker images | grep portfolio

# Rollback to previous image
docker-compose down
# Edit docker-compose.yml to use previous tag
docker-compose up -d
```

### **Environment Updates:**
Update secrets in GitHub repository settings, then trigger a new deployment.

---

## 📈 Next Steps

Once the basic CI/CD is working, consider adding:

1. **Staging Environment**: Deploy to staging first, then production
2. **Database Migrations**: Automated schema updates
3. **Blue-Green Deployment**: Zero-downtime deployments
4. **Monitoring Integration**: Slack/Discord notifications
5. **Performance Testing**: Load testing before production deployment

Your portfolio will now automatically deploy to `https://lexmakesit.com` every time you push to the main branch! 🎉