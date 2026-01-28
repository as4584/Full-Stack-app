# 🔒 SECURITY HARDENING DOCUMENTATION

## Overview
This portfolio application implements **OWASP ASVS Level 1** security controls and follows industry best practices for production deployment on DigitalOcean.

---

## 🛡️ Security Controls Implemented

### 1. Application-Level Hardening

#### Input Validation & Sanitization
- ✅ **Pydantic schema validation** for all user inputs
- ✅ **Length limits** on all text fields (2-100 chars for name/subject, 10-1000 for message)
- ✅ **Character whitelisting** to block HTML/script injection (`<`, `>`, `{`, `}`, `` ` ``, `$`)
- ✅ **Email validation** via `EmailStr` type
- ✅ **Script tag detection** in message fields (`<script`, `javascript:`)

#### Rate Limiting
- ✅ **Global limit**: 100 requests/hour per IP
- ✅ **Contact form**: 5 submissions/hour per IP
- ✅ **API endpoints**: 10-20 requests/minute
- ✅ **Health check**: 30 requests/minute
- ✅ Uses `slowapi` with in-memory storage

#### Request Size Limits
- ✅ **Max request body**: 1 MB (prevents DoS via large payloads)
- ✅ Middleware enforces `413 Payload Too Large` for oversized requests

---

### 2. Security Headers (OWASP Compliant)

All responses include comprehensive security headers:

```http
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; ...
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=(), usb=()
```

**Protection against:**
- ✅ XSS (Cross-Site Scripting)
- ✅ Clickjacking
- ✅ MIME sniffing attacks
- ✅ Code injection
- ✅ Information leakage via referrer

---

### 3. CORS & Host Configuration

#### Production Mode
- ✅ CORS restricted to allowed origins (via `ALLOWED_ORIGINS` env var)
- ✅ Only `GET` and `POST` methods enabled
- ✅ Credentials allowed only for trusted origins
- ✅ Headers restricted to `Content-Type` and `Authorization`

#### Public Access
- ✅ `TrustedHostMiddleware` allows all hosts (portfolio is publicly accessible)
- ✅ `--forwarded-allow-ips '*'` in Uvicorn for reverse proxy support

---

### 4. Container Security (Dockerfile)

#### Base Image
- ✅ Pinned version: `python:3.11.6-slim-bookworm`
- ✅ Minimal attack surface (slim variant)
- ✅ Security updates applied: `apt-get upgrade -y`

#### Non-Root User
- ✅ Custom user `appuser` (UID 1000, GID 1000)
- ✅ No shell access (`/sbin/nologin`)
- ✅ Application runs as non-root
- ✅ File permissions: `550` (read-only) for app, `750` for static/templates

#### Dependency Management
- ✅ Pip upgraded to specific version: `23.3.1`
- ✅ `pip check` validates dependency integrity
- ✅ No cache files written (`--no-cache-dir`)

#### Health Checks
- ✅ Interval: 30s, Timeout: 5s, Retries: 3
- ✅ Uses `curl` for reliable HTTP checks

#### Runtime Security
- ✅ `PYTHONUNBUFFERED=1` (immediate log output)
- ✅ `PYTHONDONTWRITEBYTECODE=1` (no .pyc files)
- ✅ Uvicorn flags: `--proxy-headers`, `--no-access-log`, `--log-level warning`

---

### 5. Error Handling & Logging

#### Production Mode
- ✅ API docs hidden (`/api/docs`, `/api/redoc` disabled)
- ✅ Generic error messages (no stack traces exposed)
- ✅ Server header removed from responses
- ✅ Errors logged privately with sanitization

#### Development Mode
- ✅ Detailed error messages for debugging
- ✅ API docs available at `/api/docs`

#### Logging
- ✅ Log level: `WARNING` in production, `INFO` in development
- ✅ Structured logging format with timestamps
- ✅ Sensitive data (tokens, IPs) sanitized

---

### 6. Authentication & Secrets Management

#### JWT Tokens
- ✅ Algorithm: HS256
- ✅ Expiration: 30 minutes
- ✅ Secret key from environment variable

#### Password Hashing
- ✅ bcrypt with auto-rotation (via `passlib`)
- ✅ Deprecated schemes handled automatically

#### Environment Variables
- ✅ Secrets loaded via `python-dotenv`
- ✅ `.env` file excluded from Git (`.gitignore`)
- ✅ Default secrets generated with `secrets.token_urlsafe(32)`

**Required env vars:**
```bash
SECRET_KEY=<your-secret-key>
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
PRODUCTION=true
```

---

## 🔍 Vulnerability Scanning

### Recommended Tools
- **Container scanning**: Trivy, Grype
- **Dependency audit**: `pip-audit`, GitHub Dependabot
- **Static analysis**: Bandit, Ruff, Semgrep
- **SAST**: CodeQL, Snyk

### Pre-Deployment Checklist
```bash
# Scan Docker image
trivy image portfolio:latest

# Audit Python dependencies
pip-audit -r requirements.txt

# Static code analysis
bandit -r . -ll

# Check for secrets in code
gitleaks detect --source .
```

---

## 🌐 Server Configuration

### Firewall (UFW)
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### Fail2Ban (SSH Protection)
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Reverse Proxy (Caddy/Nginx)
Use a reverse proxy to:
- ✅ Terminate SSL/TLS
- ✅ Enforce HTTPS redirection
- ✅ Add additional rate limiting
- ✅ Serve static files directly
- ✅ Hide application server details

---

## 🚀 Deployment Instructions

### 1. Build Production Image
```bash
docker build -t portfolio:latest .
```

### 2. Run with Security Options
```bash
docker run -d \
  --name portfolio \
  -p 8000:8000 \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --security-opt no-new-privileges:true \
  --cap-drop ALL \
  -e SECRET_KEY="$(openssl rand -hex 32)" \
  -e ALLOWED_ORIGINS="https://yourdomain.com" \
  -e PRODUCTION=true \
  portfolio:latest
```

### 3. Verify Health
```bash
curl http://localhost:8000/api/health
```

---

## 📋 Compliance Checklist

### OWASP Top 10 (2021)
- [x] A01: Broken Access Control → Rate limiting, input validation
- [x] A02: Cryptographic Failures → Bcrypt, JWT, HTTPS enforcement
- [x] A03: Injection → Pydantic validation, character whitelisting
- [x] A04: Insecure Design → Security headers, CSP, minimal attack surface
- [x] A05: Security Misconfiguration → Non-root user, hidden docs in prod
- [x] A06: Vulnerable Components → Pinned versions, `pip check`
- [x] A07: Auth Failures → JWT expiration, secure cookies
- [x] A08: Data Integrity Failures → Input sanitization, output escaping
- [x] A09: Logging Failures → Structured logging, error tracking
- [x] A10: SSRF → No external requests in user-controlled flows

### OWASP ASVS Level 1
- [x] V1: Architecture → Secure middleware, separation of concerns
- [x] V2: Authentication → JWT, bcrypt, token expiration
- [x] V3: Session Management → Secure cookies (HttpOnly, SameSite, Secure)
- [x] V4: Access Control → Rate limiting, CORS policy
- [x] V5: Input Validation → Pydantic models, length limits, whitelisting
- [x] V7: Error Handling → Generic messages, private logging
- [x] V8: Data Protection → HTTPS enforcement, HSTS
- [x] V9: Communications → TLS/SSL via reverse proxy
- [x] V12: Files → Read-only filesystem in container
- [x] V13: API → Rate limiting, input validation, secure headers
- [x] V14: Configuration → Environment variables, no hardcoded secrets

---

## 🔄 Maintenance

### Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python dependencies
pip install --upgrade -r requirements.txt

# Rebuild Docker image monthly
docker build --no-cache -t portfolio:latest .
```

### Security Monitoring
- Monitor logs for suspicious activity
- Set up alerts for rate limit violations
- Review Dependabot alerts weekly
- Rotate secrets quarterly

---

## 📞 Security Contact

For security issues, contact: **as4584@users.noreply.github.com**

**Do not** file public issues for security vulnerabilities.

---

## 📄 License

Security configurations are part of the main project. See LICENSE file.

---

**Last Updated**: November 6, 2025  
**Security Level**: OWASP ASVS Level 1 Compliant  
**Status**: Production-Ready ✅
