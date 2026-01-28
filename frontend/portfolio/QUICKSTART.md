# Quick Start Guide - API Consulting Portfolio

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies
```bash
# Make setup script executable
chmod +x setup.sh

# Run setup (creates venv, installs packages, generates secret key)
./setup.sh
```

**OR manually:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure Environment
Edit `.env` file and update:
- `SECRET_KEY` - Auto-generated or use your own
- `ALLOWED_ORIGINS` - Add your domain when deploying
- Email settings (optional, for contact form)

### Step 3: Run the Application
```bash
python main.py
```

**OR with uvicorn:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Visit: **http://localhost:8000**

---

## 📝 Customization Checklist

### 1. Update Personal Information (main.py)
- [ ] Change projects in `PROJECTS` list
- [ ] Update testimonials in `TESTIMONIALS` list  
- [ ] Modify tools/certifications in `TOOLS_EXPERTISE` and `CERTIFICATIONS`
- [ ] Update availability message

### 2. Add Your Images (static/images/)
- [ ] Replace `profile.jpg` with your professional photo
- [ ] Add project screenshots: `project1.jpg`, `project2.jpg`, `project3.jpg`
- [ ] Add client avatar images (optional)

### 3. Customize Design (static/css/style.css)
- [ ] Update CSS color variables (lines 7-17)
- [ ] Adjust fonts if needed
- [ ] Modify hero section if desired

### 4. Security Settings (.env)
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure `ALLOWED_ORIGINS` for production
- [ ] Set up email for contact form

---

## 🎯 Features Implemented

### ✅ Security (Production-Ready)
- CORS with whitelist
- Rate limiting (SlowAPI)
- Password hashing (Bcrypt)
- JWT encryption
- CSP headers
- XSS protection
- Input validation (Pydantic)
- HTTPS-ready

### ✅ Cialdini Persuasion Principles
1. **Liking** - Professional intro, relatable personality
2. **Authority** - Certifications, expertise showcase
3. **Social Proof** - Client testimonials, project results
4. **Reciprocity** - Free resources section
5. **Scarcity** - Limited availability notice
6. **Consistency** - Form engagement tracking

### ✅ Modern Design
- Split-face hero (creative + technical)
- Responsive mobile-first layout
- Smooth scroll animations
- Project cards with hover effects
- Professional typography
- Clean minimalist aesthetic

---

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest test_main.py -v

# With coverage
pytest --cov=main test_main.py
```

---

## 🚢 Deployment Options

### Option 1: Docker
```bash
docker build -t api-portfolio .
docker run -p 8000:8000 --env-file .env api-portfolio
```

### Option 2: Docker Compose
```bash
docker-compose up -d
```

### Option 3: Platform Services
- **Railway**: Connect GitHub repo, auto-deploy
- **Render**: Add web service, point to `main.py`
- **Vercel**: Use serverless functions
- **DigitalOcean App Platform**: Deploy from GitHub

### Production Checklist
- [ ] Set `DEBUG=False` in `.env`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure real `ALLOWED_ORIGINS`
- [ ] Set up SSL/TLS certificates
- [ ] Configure email (SMTP)
- [ ] Set up database (if needed)
- [ ] Configure CDN for static files
- [ ] Set up monitoring/logging

---

## 📚 API Documentation

Once running, access interactive API docs:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### Available Endpoints

```
GET  /                      - Main landing page
GET  /api/health           - Health check
GET  /api/projects         - List all projects (rate limited: 10/min)
GET  /api/projects/{id}    - Get specific project (rate limited: 20/min)
GET  /api/testimonials     - List testimonials (rate limited: 10/min)
POST /api/contact          - Submit contact form (rate limited: 5/hour)
```

---

## 🎨 Color Scheme

The design uses a dual theme:

**Creative Side (Colorful)**
- Primary: `#6366f1` (Indigo)
- Secondary: `#8b5cf6` (Purple)
- Accent: `#ec4899` (Pink)

**Technical Side (Grayscale)**
- Primary: `#1f2937` (Gray 800)
- Secondary: `#4b5563` (Gray 600)
- Accent: `#9ca3af` (Gray 400)

Update in `static/css/style.css` (lines 7-17)

---

## 🆘 Troubleshooting

### Port 8000 already in use
```bash
# Find process
lsof -i :8000
# Kill it
kill -9 <PID>
# Or use different port
uvicorn main:app --port 8001
```

### Module not found errors
```bash
# Ensure venv is activated
source venv/bin/activate
# Reinstall dependencies
pip install -r requirements.txt
```

### Static files not loading
- Check `static/` directory exists
- Verify file paths in HTML
- Clear browser cache

---

## 📞 Support

- Check README.md for detailed documentation
- Review code comments in main.py
- Test with included test suite
- Check API docs at /api/docs

---

**Built with FastAPI + Modern Security 🔒**
