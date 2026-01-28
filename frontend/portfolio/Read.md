# DIAGNOSTICS CHECKLIST — RUN THESE COMMANDS NOW

**Priority order**: Run these commands on your droplet and save outputs. This will identify the 500 error cause and memory leak location.

---

## 🔴 PRIORITY 1: Immediate System State (run first)

```bash
# 1) Memory snapshot - shows available memory and if system is near OOM
free -h
# OUTPUT MEANING: Look at "available" column. <100Mi = critical, restart service immediately.

# 2) Top 20 memory-consuming processes
ps aux --sort=-rss | head -n 20
# OUTPUT MEANING: Find your app process (uvicorn/gunicorn/python). RSS column shows memory.
# If uvicorn RSS >500Mi and growing = memory leak confirmed.

# 3) System info
uname -a
lsb_release -a
# OUTPUT MEANING: Confirms Ubuntu version and kernel for compatibility checks.
```

---

## 🟡 PRIORITY 2: Find the App Process and Service

```bash
# 4) Check systemd service status
sudo systemctl status ai_receptionist.service --no-pager -l
sudo systemctl cat ai_receptionist.service
# OUTPUT MEANING: Shows service state (running/failed), startup command, restart count.
# Look for "Restart=" count > 10 = service is crash-looping.

# 5) Find running processes
pgrep -af "uvicorn|gunicorn|python.*main"
# OUTPUT MEANING: Shows PID and exact command. Note the PID for next steps.

# 6) Export PID for next commands
export APP_PID=$(pgrep -f uvicorn | head -n1)
echo "App PID: $APP_PID"
# If empty, app is not running. Check docker instead (see PRIORITY 4).
```

---

## 🟡 PRIORITY 3: Deep Memory Inspection

```bash
# 7) Memory map of the app process (replace with actual PID if $APP_PID empty)
sudo pmap -x $APP_PID | tail -n 40
# OUTPUT MEANING: Shows memory regions. Large "anon" sections = heap growth.
# Look for total RSS matching ps output. Segments >100M indicate leak areas.

# 8) File descriptor count (leak check)
ls -l /proc/$APP_PID/fd | wc -l
# OUTPUT MEANING: >1000 file descriptors = potential file handle leak.
# Normal: 50-200. Critical: >500.

# 9) Connection count
sudo netstat -tnp | grep $APP_PID | wc -l
# OUTPUT MEANING: >100 connections = potential connection pool leak or not closing clients.
```

---

## 🟢 PRIORITY 4: Docker Alternative (if app runs in Docker)

```bash
# 10) List containers
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}"
# OUTPUT MEANING: Find your app container. Note container ID.

# 11) Container resource usage
docker stats --no-stream
# OUTPUT MEANING: MEM USAGE column. If near MEM LIMIT or >700Mi = leak confirmed.

# 12) Container logs (last 200 lines)
docker logs --tail 200 <CONTAINER_ID>
# OUTPUT MEANING: Look for Python tracebacks, "Internal Server Error", or OOM messages.
# Paste full traceback into Copilot for root cause analysis.
```

---

## 🔵 PRIORITY 5: Application Logs (find the 500 error)

```bash
# 13) Tail systemd journal logs
sudo journalctl -u ai_receptionist.service --since "10 minutes ago" --no-pager | tail -n 300
# OUTPUT MEANING: Python tracebacks show which endpoint/function is failing.
# Look for: "Traceback", "Error", "Exception", "500".

# 14) OR tail file logs if logging to file
tail -n 300 /var/log/ai_receptionist.log
# (adjust path: could be /var/log/app.log, ~/portfolio/logs/app.log, etc.)
```

---

## 🟣 PRIORITY 6: Reproduce the HTTP 500 Error

```bash
# 15) Test health endpoint
curl -i http://127.0.0.1:8080/health
# OUTPUT MEANING: HTTP 200 = endpoint works. HTTP 500 = see body for error message.

# 16) Test root endpoint
curl -i http://127.0.0.1:8080/
# OUTPUT MEANING: Same as above. Paste response body for debugging.

# 17) Test any specific endpoint that's broken
curl -i http://127.0.0.1:8080/api/receptionist/call
# (replace with actual failing endpoint from logs)
```

---

## 🟤 PRIORITY 7: Code Repository State

```bash
# 18) Check current branch and uncommitted changes
cd ~/portfolio || cd ~/ai_receptionist
pwd
git status --porcelain -b
git log --oneline -5
# OUTPUT MEANING: Shows current branch, dirty files. Note branch for rollback.

# 19) Check Python version
python3 --version
which python3
# OUTPUT MEANING: Must be 3.10 or 3.11 per your requirements.

# 20) Check installed packages (look for version mismatches)
pip list | grep -E "fastapi|uvicorn|httpx|openai|twilio|pinecone"
# OUTPUT MEANING: Old versions may have known leaks. Note for upgrade recommendations.
```

---

## 📊 WHAT TO DO WITH OUTPUTS

1. **If free -h shows <100Mi available**: Restart service NOW (see emergency mitigation below).
2. **If ps shows uvicorn RSS >500Mi**: Memory leak confirmed. Continue with patches below.
3. **If logs show Python traceback**: Paste full traceback into Copilot for immediate fix.
4. **If curl shows 500**: Logs will have the traceback. Find it in step 13/14.
5. **If docker stats shows high MEM%**: Apply docker memory limits (see docker-compose.memlimit.yml).

---

## 🚨 EMERGENCY MITIGATION (if site is down NOW)

```bash
# Systemd restart
sudo systemctl restart ai_receptionist.service

# Docker restart
docker restart <CONTAINER_ID>

# Or kill and restart manually
sudo kill -9 $APP_PID
cd ~/portfolio
source venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8080 &> /tmp/app.log &
```

**After restart**: Site should return. But leak will recur. Continue with patches and monitoring.

---

## 📋 NEXT STEPS AFTER COLLECTING OUTPUTS

1. Apply `error_and_logging.py` middleware (captures all 500s with full traceback).
2. Enable `memdump.py` debug endpoint (see current memory allocation hotspots).
3. Run `mem_snapshot.py` script after 30 min of runtime to capture heap growth.
4. Switch to Gunicorn with worker recycling (see systemd service template).
5. Add memory limits (systemd MemoryMax or docker mem_limit).
6. Review `likely_causes.txt` and apply targeted fixes based on traceback.

---

**Save all command outputs** and paste into Copilot or review manually using the guides below.
