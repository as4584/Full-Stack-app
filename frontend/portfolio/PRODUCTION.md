# Portfolio Production Deployment Guide

## 🚀 Quick Start

Your portfolio is now enterprise-ready with PostgreSQL database, structured logging, Docker secrets, and enhanced security.

### Prerequisites

- Domain name pointing to your server
- Docker and Docker Compose installed
- Ports 80 and 443 open on your server
- At least 2GB RAM (4GB recommended)

### Deployment Steps

1. **Clone and prepare:**
   ```bash
   git clone <your-repo> portfolio
   cd portfolio
   ```

2. **Deploy with SSL:**
   ```bash
   ./deploy.sh yourdomain.com your-email@example.com
   ```

3. **The script will:**
   - Generate secure `.env` file and Docker secrets
   - Create PostgreSQL database with sample data
   - Generate Let's Encrypt SSL certificates
   - Configure nginx with enhanced security
   - Deploy your portfolio with HTTPS and database

### Manual Configuration

If you prefer manual setup:

1. **Create environment and secrets:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   
   mkdir -p secrets
   echo "your-secret-key" > secrets/secret_key.txt
   echo "your-smtp-password" > secrets/smtp_password.txt
   echo "your-postgres-password" > secrets/postgres_password.txt
   chmod 600 secrets/*.txt
   ```

2. **Start services:**
   ```bash
   docker-compose up -d db
   # Wait for database to be ready
   docker-compose up -d
   ```

## 🏗️ Architecture

### Services
- **web**: FastAPI application with structured logging
- **db**: PostgreSQL 15 with persistent storage
- **nginx**: Reverse proxy with SSL and rate limiting
- **certbot**: SSL certificate management

### Data Persistence
- PostgreSQL data: `postgres_data` volume
- SSL certificates: `certbot-etc` volume
- Application logs: `./logs` directory

## 🔒 Security Features

- **Docker secrets** for sensitive data (no environment variables)
- **PostgreSQL database** with connection pooling
- **Structured JSON logging** for monitoring
- **Enhanced rate limiting** (API: 5/s, Contact: 1/m, Static: 50/s)
- **Connection limits** per IP and server
- **Health checks** for all containers
- **Gzip compression** for performance
- **Security headers** (CSP, HSTS, XSS protection)

## 🗄️ Database Schema

Your database includes tables for:
- `contacts`: Contact form submissions
- `projects`: Dynamic project management
- `testimonials`: Client testimonials
- `analytics`: Basic site analytics

Sample data is automatically populated.

## 📊 Logging & Monitoring

### Structured Logs
- **Application logs**: `logs/application.json`
- **Error logs**: `logs/errors.json`
- **Nginx logs**: `logs/` (access and error)

### Log Format
```json
{
  "timestamp": "2025-11-12T00:00:00Z",
  "level": "INFO",
  "logger": "main",
  "message": "Contact form submitted",
  "module": "main",
  "function": "contact_form",
  "line": 487
}
```

### Health Checks
- **Application**: `https://yourdomain.com/api/health`
- **Database**: Built-in PostgreSQL health check
- **Nginx**: HTTP status check

## 🔧 Environment Variables

Key variables in your `.env` file:

```bash
# Application
DOMAIN=yourdomain.com
EMAIL=your-email@example.com
PRODUCTION=true

# Database (auto-configured)
DATABASE_URL=postgresql://portfolio_user:password@db:5432/portfolio
POSTGRES_DB=portfolio
POSTGRES_USER=portfolio_user
POSTGRES_PASSWORD=secure-password

# Security
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
TRUSTED_HOSTS=yourdomain.com,www.yourdomain.com
RATE_LIMIT_PER_MINUTE=60
```

## � Performance Features

### Nginx Optimizations
- **Gzip compression** (level 6) for all text content
- **Static file caching** (30 days) with immutable headers
- **Connection pooling** to backend
- **Request buffering** for better performance

### Database Optimizations
- **Connection pooling** (2-10 connections)
- **Prepared statements** and query optimization
- **Indexed tables** for fast queries
- **JIT disabled** for consistent small query performance

### Rate Limiting
- **API endpoints**: 5 requests/second
- **Contact form**: 1 request/minute
- **Static files**: 50 requests/second
- **General pages**: 20 requests/second

## 🛠️ Troubleshooting

### Database Issues
```bash
# Check database status
docker-compose logs db

# Access database directly
docker-compose exec db psql -U portfolio_user -d portfolio

# Reset database
docker-compose down -v
docker-compose up -d db
```

### Application Issues
```bash
# Check app logs
docker-compose logs web
tail -f logs/application.json

# Check structured error logs
tail -f logs/errors.json | jq .

# Restart with fresh logs
docker-compose restart web
```

### SSL Issues
```bash
# Check certificate status
docker-compose run --rm certbot certificates

# Force renewal
docker-compose run --rm certbot renew --force-renewal

# Check nginx SSL config
docker-compose exec nginx nginx -t
```

## 🔄 Maintenance

### SSL Renewal (Automated)
```bash
# Add to crontab
0 0 * * 0 /path/to/portfolio/renew-ssl.sh
```

### Log Rotation
Logs are automatically rotated when they exceed 10MB (5 backup files kept).

### Database Backup
```bash
# Manual backup
docker-compose exec db pg_dump -U portfolio_user portfolio > backup.sql

# Restore
docker-compose exec -T db psql -U portfolio_user portfolio < backup.sql
```

## � Scaling

### Horizontal Scaling
- Increase web service replicas in docker-compose
- Add load balancer for multiple servers
- Use external PostgreSQL for multi-server setup

### Performance Monitoring
- Monitor `logs/application.json` for performance metrics
- Use `docker stats` for container resource usage
- Monitor database connections via health endpoint

Your portfolio is now **production-ready** with enterprise features! 🎉