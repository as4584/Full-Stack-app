# Portfolio Project - Production Ready FastAPI Application

🚀 **Live Site**: [lexmakesit.com](https://lexmakesit.com)

## Quick Start

This is a production-ready portfolio website with enterprise-grade security, automated CI/CD, and modern DevOps practices.

### Features
- ✅ **Automated Deployment**: Push to main → Deploy to production
- ✅ **SSL/HTTPS**: Let's Encrypt with auto-renewal
- ✅ **Database**: PostgreSQL with connection pooling
- ✅ **Security**: Docker secrets, rate limiting, security headers
- ✅ **Monitoring**: Structured logging and health checks
- ✅ **Performance**: Nginx reverse proxy with compression

### Architecture
```
GitHub → CI/CD → Docker → Nginx → FastAPI → PostgreSQL
```

## Development

### Local Setup
```bash
# Clone and setup
git clone <repo> && cd portfolio
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run locally
cp .env.example .env
python main.py  # http://localhost:8001
```

### Production Deployment
```bash
# Automatic deployment (recommended)
git add . && git commit -m "Your changes"
git push origin main  # Automatically deploys to lexmakesit.com

# Manual deployment
./deploy.sh lexmakesit.com your-email@example.com
```

## Documentation

- 📚 **[Complete Project Documentation](PROJECT_DOCUMENTATION.md)** - Architecture, security, and technical details
- 🚀 **[CI/CD Setup Guide](CICD_SETUP.md)** - GitHub Actions configuration
- 🏭 **[Production Deployment](PRODUCTION.md)** - Production setup and monitoring

## Quick Scripts

```bash
# Generate GitHub secrets for CI/CD
./setup-github-secrets.sh

# Check deployment health
./health-check.sh lexmakesit.com

# Manual production deployment
./deploy.sh lexmakesit.com your-email@example.com
```

## Technology Stack

- **Backend**: FastAPI (Python) with async/await
- **Database**: PostgreSQL with asyncpg
- **Proxy**: Nginx with SSL termination
- **Container**: Docker Compose with health checks
- **CI/CD**: GitHub Actions
- **Hosting**: DigitalOcean Droplet (104.236.100.245)

## Security Features

- 🔒 Docker secrets (no environment variable exposure)
- 🛡️ OWASP ASVS Level 1 compliance
- 🚦 Advanced rate limiting per endpoint
- 📊 Structured security logging
- 🔐 Let's Encrypt SSL with HSTS
- 🧪 Automated security scanning in CI/CD

---

**Live Portfolio**: [https://lexmakesit.com](https://lexmakesit.com)