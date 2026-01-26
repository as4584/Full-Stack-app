# Production Deployment Verification Checklist

## Pre-Deploy Requirements

- [ ] Production build succeeds locally (`npm run build`)
- [ ] No TypeScript errors
- [ ] No ESLint errors
- [ ] NODE_ENV=production set in docker-compose
- [ ] Dockerfile uses multi-stage production build
- [ ] `.env.local` NOT included in rsync

## Infrastructure Requirements

- [ ] Caddy reverse proxy running on port 443
- [ ] Dashboard container on `apps_antigravity_net` network
- [ ] Caddy and dashboard can communicate internally
- [ ] DNS: `dashboard.lexmakesit.com` → server IP
- [ ] SSL certificate auto-provisioned by Caddy

## Security Requirements  

- [ ] Port 3000 NOT exposed publicly (use `expose` not `ports`)
- [ ] Firewall rule blocks direct port 3000 access (`ufw deny 3000`)
- [ ] Only HTTPS accessible (port 443)
- [ ] Security headers configured in Caddyfile
- [ ] No dev mode running (`NODE_ENV=production`)

## Deployment Steps

### 1. Deploy Application
```bash
chmod +x /home/lex/lexmakesit/scripts/deploy-production-secure.sh
/home/lex/lexmakesit/scripts/deploy-production-secure.sh
```

**Expected Output:**
- ✓ Files synced to server
- ✓ Caddy config updated
- ✓ Container built and started
- ✓ NODE_ENV=production confirmed
- ✓ Internal connectivity verified
- ✓ Port 3000 not publicly accessible
- ✓ HTTPS returns 200/307/302

### 2. Run Smoke Test
```bash
chmod +x /home/lex/lexmakesit/scripts/smoke-test-production.sh
/home/lex/lexmakesit/scripts/smoke-test-production.sh
```

**Expected Output:**
- ✓ DNS resolves
- ✓ HTTPS returns 200/307/302
- ✓ Response is HTML
- ✓ No Next.js error overlay
- ✓ Dashboard shell renders
- ✓ Port 3000 locked down

### 3. Manual Browser Verification
```bash
# Open in browser
xdg-open https://dashboard.lexmakesit.com
```

**Visual Checks:**
- [ ] Page loads without 502 error
- [ ] NO red Next.js error overlay
- [ ] NO "Missing required html tags" warning
- [ ] Login page or dashboard renders
- [ ] Browser console has no framework errors
- [ ] Hard refresh (Ctrl+Shift+R) still works

## Post-Deploy Monitoring

### Immediate (First 5 Minutes)
```bash
# Watch container logs
ssh droplet "docker logs -f dashboard_nextjs_prod"

# Watch Caddy logs
ssh droplet "docker logs -f antigravity_caddy"

# Check for errors
ssh droplet "docker logs dashboard_nextjs_prod --since 5m | grep -i error"
```

### Health Check (Automated)
```bash
# Should return "healthy"
ssh droplet "docker inspect dashboard_nextjs_prod --format='{{.State.Health.Status}}'"
```

### Load Testing (Optional)
```bash
# Basic load test
ab -n 100 -c 10 https://dashboard.lexmakesit.com/
```

## Rollback Procedure

If smoke test fails or critical issues detected:

```bash
# Stop broken container
ssh droplet "cd /srv/ai_receptionist/dashboard_src && docker compose -f docker-compose.prod.locked.yml down"

# Restore previous Caddyfile
ssh droplet "sudo cp /etc/caddy/Caddyfile.backup /etc/caddy/Caddyfile"
ssh droplet "docker exec antigravity_caddy caddy reload --config /etc/caddy/Caddyfile"

# Investigate logs
ssh droplet "docker logs dashboard_nextjs_prod --tail 100"
```

## Common Issues & Fixes

### Issue: 502 Bad Gateway
**Cause:** Caddy can't reach container  
**Fix:** Check Docker network: `docker network connect apps_antigravity_net dashboard_nextjs_prod`

### Issue: Port 3000 publicly accessible
**Cause:** `ports` instead of `expose` in docker-compose  
**Fix:** Use docker-compose.prod.locked.yml + `sudo ufw deny 3000`

### Issue: Next.js dev warnings visible
**Cause:** Running `npm run dev` or NODE_ENV not set  
**Fix:** Ensure Dockerfile uses production build + NODE_ENV=production

### Issue: DNS not resolving
**Cause:** DNS propagation delay or wrong A record  
**Fix:** Verify with `dig +short dashboard.lexmakesit.com`

### Issue: SSL certificate error
**Cause:** Caddy hasn't provisioned cert yet  
**Fix:** Check `docker logs antigravity_caddy` for ACME errors

## Success Criteria (Final Sign-Off)

All must be ✓ before considering deployment complete:

- [ ] HTTPS accessible: `curl -I https://dashboard.lexmakesit.com` returns 200/307/302
- [ ] No 502 errors
- [ ] HTML response (not JSON error)
- [ ] No framework errors visible in browser
- [ ] Port 3000 NOT accessible: `nc -zv 104.236.100.245 3000` fails
- [ ] NODE_ENV=production confirmed
- [ ] Container health status: "healthy"
- [ ] No errors in container logs (last 100 lines)
- [ ] Caddy can reach container internally
- [ ] Smoke test passes: `./scripts/smoke-test-production.sh` exits 0

## Maintenance

### Daily Checks
- Monitor error rates in logs
- Check container uptime
- Verify SSL certificate expiry (Caddy auto-renews)

### Weekly Checks  
- Review disk space (`df -h`)
- Check memory usage (`docker stats`)
- Update dependencies if needed

### Emergency Contacts
- DevOps: [Your contact]
- On-call: [Your contact]
- Status Page: https://status.lexmakesit.com (if available)

---

**Last Updated:** January 26, 2026  
**Version:** 1.0  
**Owner:** DevOps Team
