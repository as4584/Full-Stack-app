# Project Architecture Summary for Copilot

## Overview
This repository uses a production-grade FastAPI deployment pipeline.  
Everything in this file defines the standard architecture that all future projects should follow.  

## Tech Stack
- FastAPI + Uvicorn
- Dockerfile for production builds
- docker-compose for container orchestration
- GitHub Actions for CI/CD
- systemd service for uptime and auto-restart
- Nginx reverse proxy on the server
- Deployed to DigitalOcean Ubuntu server under /srv/<project-name>

## Server Structure
The DigitalOcean droplet hosts code at:

```
/srv/portfolio
/srv/<other-projects>
```

Each project:
- runs inside Docker
- exposes one internal port (portfolio uses 8000)
- has its own systemd service
- has its own Nginx route block
- is updated by GitHub Actions

## GitHub Actions Pipeline
Pipeline performs:
1. Code formatting, linting, and tests  
2. Docker image build  
3. SSH into the droplet using secrets:
   - HOST_IP
   - SSH_USERNAME
   - SSH_KEY
4. Pull latest code into /srv/PROJECT_NAME
5. docker compose rebuild and restart
6. Restart the systemd service
7. Reload Nginx if needed

## Deployment Pattern
Every project MUST follow this layout:

- Dockerfile (FastAPI + uvicorn)
- docker-compose.yml (restart always, build in place)
- .github/workflows/deploy.yml
- systemd service file PROJECT_NAME.service
- Nginx location block mounted under domain

## Example Ports
- Portfolio: 8000
- Inventory Manager: 8010
- Future projects: 8020, 8030, etc.

## Required Secrets
Every repo needs GitHub Secrets:
- HOST_IP
- SSH_USERNAME
- SSH_KEY

## Required Systemd File
Each service uses:

```ini
ExecStart=/usr/bin/docker compose -f /srv/PROJECT_NAME/docker-compose.yml up -d --build  
ExecStop=/usr/bin/docker compose -f /srv/PROJECT_NAME/docker-compose.yml down  

User=lex  
Restart=always  
```

## Required Nginx Block Example

```nginx
location /PROJECT_NAME/ {
    proxy_pass http://127.0.0.1:PORT/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

## Goal
Copilot should use this file to:
- replicate this deployment architecture for all new services
- generate boilerplate configs automatically
- ensure all paths, ports, and conventions match this setup

## Current Portfolio Implementation

### File Structure
```
portfolio/
├── Dockerfile
├── docker-compose.yml
├── .github/workflows/deploy.yml
├── main.py (FastAPI application)
├── requirements.txt
├── static/ (CSS, JS, images)
├── templates/ (Jinja2 HTML templates)
└── PROJECT_ARCHITECTURE.md (this file)
```

### Port Allocation
- **Portfolio**: 8000 (current project)
- **Available**: 8010, 8020, 8030, etc.

### Production URLs
- **Primary**: https://as4584.github.io/portfolio/
- **Server**: Accessible via DigitalOcean droplet at /srv/portfolio

### Deployment Workflow
1. **Local Development**: `uvicorn main:app --reload`
2. **Docker Local**: `docker compose up --build`
3. **Production**: Automated via GitHub Actions on push to main

### Security Standards
- OWASP ASVS Level 1 compliance
- Input validation and output escaping
- CSP headers and HSTS
- Rate limiting with slowapi
- Structured logging for monitoring

### Testing Pipeline
- **Syntax Check**: Python syntax validation
- **Security Scan**: Automated vulnerability detection
- **Code Quality**: PEP8 compliance with line length limits
- **Unit Tests**: 12 test cases covering all endpoints
- **Docker Build**: Production container validation

This architecture ensures scalable, maintainable, and secure deployment patterns across all lexmakesit projects.