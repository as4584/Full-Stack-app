# 🤖 AI Receptionist - Full Stack Application

A production-ready AI-powered phone receptionist system that handles incoming calls, books appointments, and provides intelligent responses using voice AI.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Next.js](https://img.shields.io/badge/next.js-14-black.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.100+-green.svg)

## 🌟 Features

- **📞 Voice AI**: Real-time phone call handling with natural conversation
- **📅 Calendar Integration**: Google Calendar OAuth for appointment booking
- **📊 Live Dashboard**: Real-time call logs, analytics, and business insights
- **🔐 Secure Auth**: JWT-based authentication with HttpOnly cookies
- **💳 Payments**: Stripe integration for subscription management
- **🎯 Smart Routing**: Intent detection and call routing logic

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│                     Client Layer                        │
│  ┌─────────────────┐    ┌─────────────────┐           │
│  │   Dashboard     │    │   Auth Portal   │           │
│  │   (Next.js)     │    │   (Next.js)     │           │
│  └────────┬────────┘    └────────┬────────┘           │
└───────────┼──────────────────────┼─────────────────────┘
            │                      │
            ▼                      ▼
┌────────────────────────────────────────────────────────┐
│                   API Gateway (Caddy)                   │
│           TLS Termination • Reverse Proxy              │
└────────────────────────┬───────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │   Auth   │ │  Voice   │ │ Business │ │ Payments │ │
│  │  Routes  │ │ Webhooks │ │   API    │ │   API    │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │
└───────┼────────────┼────────────┼────────────┼────────┘
        │            │            │            │
        ▼            ▼            ▼            ▼
┌────────────────────────────────────────────────────────┐
│                   Data Layer                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │PostgreSQL│ │  Redis   │ │  Qdrant  │              │
│  │  (Data)  │ │ (Cache)  │ │ (Vector) │              │
│  └──────────┘ └──────────┘ └──────────┘              │
└────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- Twilio Account
- OpenAI API Key

### Backend Setup

```bash
cd backend

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env

# Start services
docker-compose up -d

# Run migrations
docker-compose exec app alembic upgrade head
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env.local

# Edit .env.local with your API URL
nano .env.local

# Start development server
npm run dev
```

### Configure Twilio Webhook

Point your Twilio phone number's webhook to:
```
https://your-api-domain.com/twilio/voice
```

## 📁 Project Structure

```
.
├── backend/                 # FastAPI Backend
│   ├── ai_receptionist/    # Main application
│   │   ├── app/           # FastAPI app & routes
│   │   ├── core/          # Auth, config, utilities
│   │   ├── models/        # SQLAlchemy models
│   │   └── services/      # Business logic
│   ├── alembic/           # Database migrations
│   └── docker-compose.yml # Container orchestration
│
├── frontend/               # Next.js Dashboard
│   ├── app/               # App router pages
│   ├── components/        # React components
│   └── lib/               # API client & utilities
│
├── auth-frontend/         # Authentication Portal
│   └── app/               # Login/signup pages
│
└── infra/                 # Infrastructure configs
    └── caddy/             # Reverse proxy config
```

## 🔧 Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | FastAPI, Python 3.11, SQLAlchemy |
| **Frontend** | Next.js 14, TypeScript, React |
| **Database** | PostgreSQL 15 |
| **Cache** | Redis 7 |
| **Vector DB** | Qdrant (for semantic search) |
| **AI** | OpenAI GPT-4o, Google Gemini |
| **Voice** | Twilio Voice API |
| **Payments** | Stripe |
| **Auth** | JWT, bcrypt |
| **Proxy** | Caddy 2 |
| **Containers** | Docker, Docker Compose |

## 📊 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup` | Register new user |
| POST | `/api/auth/login` | Login user |
| GET | `/api/auth/me` | Get current user |
| POST | `/api/auth/logout` | Logout user |

### Business
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/business/me` | Get business details |
| PUT | `/api/business/settings` | Update settings |
| GET | `/api/business/calls` | Get call history |

### Voice (Twilio Webhooks)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/twilio/voice` | Handle incoming calls |
| POST | `/twilio/status` | Call status updates |

## 🔐 Security

- **JWT Authentication**: Secure token-based auth
- **HttpOnly Cookies**: XSS protection
- **CORS**: Configured allowed origins
- **Rate Limiting**: Slowapi middleware
- **Password Hashing**: bcrypt
- **Environment Variables**: Secrets never in code

## 📈 Monitoring

- Health check endpoint: `/health`
- Request ID tracking in logs
- Structured JSON logging
- Docker healthchecks

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 👨‍💻 Author

**Alexander Santiago** - [@as4584](https://github.com/as4584)

---

*Built with ❤️ and lots of debugging sessions*
