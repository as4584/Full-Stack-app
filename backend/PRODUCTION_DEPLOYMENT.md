# 🤖 AI Receptionist Production Deployment Guide

## ⚡ **QUICK START** (5 Minutes)

```bash
# 1. Navigate to backend directory
cd /home/lex/lexmakesit/backend

# 2. Start the complete system
./start_production.sh

# 3. That's it! 🎉
```

## 🎯 **What This Does**

✅ **Replaces SQLite with PostgreSQL** (persistent, production-ready)  
✅ **Seeds your original business data** (name, phone, settings)  
✅ **Sets up automated backups** (daily at 2 AM)  
✅ **Prevents future data loss** (blocks SQLite in production)  
✅ **One-command deployment** (repeatable and safe)  

## 📊 **System Components**

| Service | Port | Purpose |
|---------|------|---------|
| **FastAPI Backend** | 8002 | Main API server |
| **PostgreSQL** | 5432 | Primary database (persistent) |
| **Redis** | 6379 | Cache and sessions |
| **Qdrant** | 6333 | Vector database for AI |

## 🔧 **Business Configuration**

The system will restore these settings automatically:

```yaml
Business Name: "AI Assistant Service"  # ← Update in seed_business_data.py
Owner Email: "thegamermasterninja@gmail.com"
Phone Number: "+1234567890"          # ← Set your Twilio number
Industry: "Technology Consulting"
Hours: "24/7"
Services: "AI receptionist, appointment scheduling, customer support"
```

## ⚙️ **Customization**

### Update Business Details
Edit `/home/lex/lexmakesit/backend/seed_business_data.py`:

```python
BUSINESS_CONFIG = {
    "business_name": "Your Actual Business Name",
    "phone_number": "+1YOUR_TWILIO_NUMBER",
    "industry": "Your Industry",
    "description": "Your business description...",
    # ... more settings
}
```

### Re-seed After Changes
```bash
cd /home/lex/lexmakesit/backend
python3 seed_business_data.py
```

## 🛠️ **Management Commands**

```bash
# View live logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart system
./start_production.sh

# Manual backup
./backup_database.sh manual

# Stop system
docker-compose -f docker-compose.prod.yml down

# Reset everything (DESTRUCTIVE)
./start_production.sh --reset-data
```

## 🔒 **Security Features**

- **Production Guards**: Blocks SQLite if `ENVIRONMENT=production`
- **Database Validation**: Fails startup if database misconfigured  
- **Persistent Storage**: PostgreSQL data survives container restarts
- **Automated Backups**: Daily backups with 30-day retention

## 📞 **Twilio Integration**

After startup, configure Twilio webhooks to point to:
```
https://receptionist.lexmakesit.com/api/webhook/twilio/voice
```

## 📱 **Frontend Connection**

Frontend at `dashboard.lexmakesit.com` should automatically connect to the backend API. No changes needed if backend runs on port 8002.

## 🆘 **Troubleshooting**

### Backend Won't Start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs app

# Check database connection
docker-compose -f docker-compose.prod.yml exec postgres psql -U ai_receptionist_user -d ai_receptionist -c "SELECT 1;"
```

### Database Issues
```bash
# Reset database (DESTRUCTIVE)
./start_production.sh --reset-data

# Manual backup first
./backup_database.sh manual
```

### Environment Problems
```bash
# Verify settings
grep -E "ENVIRONMENT|DATABASE_URL" .env

# Should show:
# ENVIRONMENT=production
# DATABASE_URL=postgresql://...
```

## 📋 **Post-Deployment Checklist**

- [ ] System starts without errors
- [ ] API responds at `http://localhost:8002/health`
- [ ] Database contains business data
- [ ] Frontend can authenticate users
- [ ] Twilio webhooks configured
- [ ] Phone number integration tested
- [ ] Daily backups running (check `/home/lex/lexmakesit/backups/database/`)

## 🚨 **Emergency Recovery**

If something goes wrong:

```bash
# 1. Stop everything
docker-compose -f docker-compose.prod.yml down

# 2. Restore from backup
cd backups/database
gunzip -c ai_receptionist_backup_YYYYMMDD_HHMMSS.sql.gz | \
docker-compose -f ../../docker-compose.prod.yml exec -T postgres psql -U ai_receptionist_user -d ai_receptionist

# 3. Restart
./start_production.sh
```

---

## 🎊 **Success!**

Your AI Receptionist is now running on a production-grade PostgreSQL database with:

- ✅ **Zero data loss risk**
- ✅ **Automated backups** 
- ✅ **One-command deployment**
- ✅ **Business data restored**
- ✅ **Frontend compatibility maintained**

**Next:** Configure your domain and SSL, then test phone integration!