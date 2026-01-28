# AUTH STABILITY CHECKLIST
**Purpose:** Verify authentication remains stable across deployments and prevent user lockouts

## ✅ Pre-Deployment Checklist

### 1. Environment Variables (CRITICAL)
- [ ] `ADMIN_PRIVATE_KEY` exists in production `.env` file
- [ ] `ADMIN_PRIVATE_KEY` is at least 32 characters long
- [ ] `DATABASE_URL` or `POSTGRES_USER`/`POSTGRES_PASSWORD` configured
- [ ] `OPENAI_API_KEY` configured
- [ ] No placeholder values like `CHANGEME`, `TODO`, `REPLACE`, etc.

**Verification Command:**
```bash
ssh Innovation "cd /opt/ai-receptionist && cat .env | grep -E 'ADMIN_PRIVATE_KEY|DATABASE_URL|POSTGRES'"
```

### 2. Docker Volume Safety
- [ ] Database volume `ai-receptionist_pgdata` exists
- [ ] Database volume is NOT being deleted in deploy scripts
- [ ] `docker-compose.prod.yml` uses named volumes (not bind mounts)

**Verification Command:**
```bash
ssh Innovation "docker volume ls | grep ai-receptionist"
```

**Expected Output:**
```
ai-receptionist_pgdata
ai-receptionist_redisdata
ai-receptionist_qdrantdata
```

### 3. Code Validation (Local)
- [ ] `settings.py` includes `validate_production_secrets()` method
- [ ] `auth.py` does NOT use fallback JWT secret (no `"dev-jwt-secret-change-in-production"`)
- [ ] `auth.py` includes detailed logging for auth failures
- [ ] `main.py` calls `validate_production_secrets()` on startup

**Verification Command:**
```bash
cd /home/lex/lexmakesit/backend
grep -n "validate_production_secrets" ai_receptionist/config/settings.py
grep -n "dev-jwt-secret" ai_receptionist/core/auth.py  # Should return NO results
```

## ✅ Deployment Validation

### 4. Safe Deployment Process
- [ ] Using `safe_deploy.sh` script (NOT manual commands)
- [ ] Deploy script validates env vars BEFORE restarting
- [ ] Deploy script NEVER runs `docker volume rm`
- [ ] Deploy script checks application health after restart

**Deploy Command:**
```bash
ssh Innovation "cd /opt/ai-receptionist && bash safe_deploy.sh"
```

### 5. Post-Deploy Health Checks
- [ ] Backend container is running and healthy
- [ ] Database container is running and healthy
- [ ] Health endpoint returns `{"status":"ok","db":"connected"}`
- [ ] No startup errors in application logs

**Verification Commands:**
```bash
# Check container health
ssh Innovation "cd /opt/ai-receptionist && docker compose -f docker-compose.prod.yml ps"

# Check health endpoint
curl https://receptionist.lexmakesit.com/health

# Check startup logs
ssh Innovation "cd /opt/ai-receptionist && docker compose -f docker-compose.prod.yml logs --tail=50 app | grep -E 'CRITICAL|ERROR|startup'"
```

## ✅ Authentication Testing

### 6. JWT Token Stability
- [ ] Existing JWT tokens remain valid after deployment
- [ ] New JWT tokens can be created
- [ ] Token expiration works correctly (7 days)

**Test Steps:**
1. Get a valid JWT token before deploy (from browser DevTools → Application → Cookies)
2. Deploy new version
3. Make authenticated API request with old token
4. Verify token still works

**Manual Test:**
```bash
# Using existing token
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" https://receptionist.lexmakesit.com/api/business/me
# Should return business data, NOT 401 Unauthorized
```

### 7. Password Verification
- [ ] Existing users can log in with correct passwords
- [ ] Wrong passwords are rejected with 401
- [ ] Password hashes are NOT regenerated on deploy

**Test Steps:**
1. Create a test user BEFORE deployment
2. Deploy new version
3. Login with same credentials
4. Verify login succeeds

**Manual Test:**
```bash
# Login request
curl -X POST https://receptionist.lexmakesit.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"correct_password"}'
# Should return {"access_token":"...", "user":{...}}
```

### 8. Database Continuity
- [ ] User table has same user count before and after deploy
- [ ] Password hashes match before and after deploy
- [ ] Business associations remain intact

**Verification Command:**
```bash
# Count users before deploy
ssh Innovation "cd /opt/ai-receptionist && docker compose -f docker-compose.prod.yml exec -T postgres psql -U ai_receptionist_user -d ai_receptionist -c 'SELECT COUNT(*) FROM users;'"

# Deploy here

# Count users after deploy (should be SAME)
ssh Innovation "cd /opt/ai-receptionist && docker compose -f docker-compose.prod.yml exec -T postgres psql -U ai_receptionist_user -d ai_receptionist -c 'SELECT COUNT(*) FROM users;'"
```

## ✅ Logging Verification

### 9. Auth Failure Logging
- [ ] Login failures show detailed `[AUTH]` log entries
- [ ] JWT decode failures are logged with error details
- [ ] bcrypt errors (if any) are logged with hash info

**Check Logs:**
```bash
# Watch for auth issues
ssh Innovation "cd /opt/ai-receptionist && docker compose -f docker-compose.prod.yml logs -f app | grep '\\[AUTH\\]'"
```

**Expected Log Patterns:**
- `[AUTH] JWT verified successfully for user_id=X`
- `[AUTH] Login failed: User not found - email@example.com`
- `[AUTH] Login failed: Password mismatch for email@example.com`

### 10. Startup Validation Logging
- [ ] Startup logs show "✅ Production secrets validation passed"
- [ ] No CRITICAL errors during startup
- [ ] All required secrets are confirmed

**Check Startup:**
```bash
ssh Innovation "cd /opt/ai-receptionist && docker compose -f docker-compose.prod.yml logs app | grep -E 'startup|secrets|validation'"
```

## 🚨 Emergency Rollback

### If Auth Lockout Occurs:

1. **Check ADMIN_PRIVATE_KEY exists:**
```bash
ssh Innovation "cd /opt/ai-receptionist && grep ADMIN_PRIVATE_KEY .env"
```

2. **Verify database volume exists:**
```bash
ssh Innovation "docker volume inspect ai-receptionist_pgdata"
```

3. **Check recent logs:**
```bash
ssh Innovation "cd /opt/ai-receptionist && docker compose -f docker-compose.prod.yml logs --tail=100 app"
```

4. **Restore previous git commit (if needed):**
```bash
ssh Innovation "cd /opt/ai-receptionist && git log --oneline -5"  # Find previous commit
ssh Innovation "cd /opt/ai-receptionist && git reset --hard COMMIT_HASH"
ssh Innovation "cd /opt/ai-receptionist && docker compose -f docker-compose.prod.yml restart app"
```

## 📊 Success Metrics

**Deployment is successful when:**
- ✅ All existing users can login with their passwords
- ✅ JWT tokens created before deploy still work
- ✅ New users can signup and login
- ✅ No `[AUTH]` errors in logs
- ✅ Health endpoint returns `db: connected`
- ✅ User count in database unchanged

## 🔐 Security Notes

1. **Never commit secrets to git**
   - All secrets should be in `.env` file (gitignored)
   - Production `.env` should be backed up securely

2. **JWT Secret Rotation (If Needed)**
   - Save old `ADMIN_PRIVATE_KEY` value
   - Generate new secret
   - Add both old and new to code (validate with either)
   - Remove old secret after all tokens expire (7 days)

3. **Password Hash Migration (If Needed)**
   - Never bulk-regenerate password hashes
   - Use database migrations to add columns
   - Hash on user login (lazy migration)
   - Keep old hash for validation

## 📝 Post-Deploy Monitoring

**Monitor these for 24 hours after deploy:**
- Login success rate (should be >95%)
- JWT verification errors (should be near 0)
- Password mismatch rate (baseline comparison)
- Database connection errors (should be 0)

**Dashboard Query:**
```bash
# Check recent auth attempts
ssh Innovation "cd /opt/ai-receptionist && docker compose -f docker-compose.prod.yml logs --since 1h app | grep -c '\\[AUTH\\]'"
```

---

## Quick Reference Commands

```bash
# SSH to production
ssh Innovation

# Navigate to app directory
cd /opt/ai-receptionist

# Check environment
cat .env | grep ADMIN_PRIVATE_KEY

# Safe deploy
bash safe_deploy.sh

# Check health
curl https://receptionist.lexmakesit.com/health

# View logs
docker compose -f docker-compose.prod.yml logs -f app

# Check database
docker compose -f docker-compose.prod.yml exec postgres psql -U ai_receptionist_user -d ai_receptionist

# Restart (if needed)
docker compose -f docker-compose.prod.yml restart app
```

---

**Last Updated:** January 26, 2026  
**Maintainer:** DevOps Team  
**Critical Contact:** Check logs first, then escalate if auth completely broken
