# 🚀 AI Receptionist Platform - Implementation Plan
**Created**: 2026-01-19
**Owner**: thegamermasterninja@gmail.com
**Status**: In Progress ✅

---

## ✅ COMPLETED TODAY (2026-01-19)

### Workstream 1: Mobile UI ✅
- Added responsive CSS for 768px and 480px breakpoints
- Hamburger menu for mobile navigation
- Pricing cards stack vertically on mobile
- Touch-friendly buttons (min 48px tap targets)

### Workstream 2: Real-time Features ✅
- Calendar now shows actual current date (January 19, 2026)
- Real-time clock updates every second
- Calendar properly calculates days in month and first day of week
- Live transcript shows properly formatted conversation

### Workstream 5: Stripe Payments ✅
- Added Stripe credentials to server `.env`
- Created `/api/stripe/create-checkout-session` endpoint
- Created `/api/stripe/webhook` endpoint for payment processing
- Pricing buttons now trigger Stripe checkout
- Welcome email sends after successful purchase

### Workstream 6: Pricing CTAs ✅
- "Get Started" button → Stripe checkout (Starter tier)
- "Start Free Pilot" button → Stripe checkout (Professional tier)
- "Contact Sales" buttons → Home contact form

---
1. **Mobile-friendly UI** - Responsive design improvements
2. **Real-time Dashboard Features** - Live calendar, clock, and transcript
3. **Phone Number Integration** - Twilio dropdown + linked number display
4. **Improved Onboarding Flow** - Better business profile setup
5. **Stripe Payment Integration** - Purchase flow + email access
6. **Pricing Page CTA Links** - Connect to dashboard/signup

---

## 🔧 WORKSTREAM 1: Mobile-Friendly UI (Frontend)

### Goal
Make the AI Receptionist page fully responsive and mobile-optimized following Frutiger Aero design principles.

### Tasks
- [ ] Add proper viewport meta tags
- [ ] Implement CSS media queries for mobile breakpoints (320px, 480px, 768px)
- [ ] Stack pricing cards vertically on mobile
- [ ] Responsive navigation (hamburger menu)
- [ ] Touch-friendly button sizes (min 44px tap targets)
- [ ] Test on actual mobile devices

### Files to Modify
- `frontend/portfolio/templates/ai-receptionist.html`
- `frontend/portfolio/static/css/global.css`
- `frontend/portfolio/static/css/components.css`

---

## 🔧 WORKSTREAM 2: Real-Time Dashboard Features (Frontend + Backend)

### Goal
Make the dashboard calendar, clock, and live transcript accurate and real-time.

### Tasks

#### 2a. Schedule/Booking Calendar
- [ ] Display today's date correctly (JavaScript `new Date()`)
- [ ] Highlight current day
- [ ] Show current month/year dynamically
- [ ] Add real-time clock display

#### 2b. Live Transcript
- [ ] Connect to WebSocket for real call data
- [ ] Display actual transcription from Twilio/OpenAI
- [ ] Color-code caller (blue) vs AI (green) properly

### Files to Modify
- Dashboard frontend (Next.js or equivalent)
- Backend WebSocket handler
- `ai_receptionist/` modules

---

## 🔧 WORKSTREAM 3: Phone Number Integration (Backend + Frontend)

### Goal
Link thegamermasterninja@gmail.com to a Twilio phone number and display it in the dashboard.

### Tasks

#### 3a. Twilio Phone Number Dropdown
- [ ] Create API endpoint to fetch available Twilio numbers
- [ ] Build dropdown component in onboarding UI
- [ ] Allow selection and assignment of number to user

#### 3b. Phone Number Display
- [ ] Show assigned phone number in dashboard header
- [ ] Add "Copy Number" functionality
- [ ] Display phone status (active/inactive)

### Backend Endpoints Needed
```python
GET  /api/twilio/available-numbers  # List purchasable numbers
GET  /api/twilio/my-numbers         # User's assigned numbers
POST /api/twilio/assign-number      # Assign number to user
```

### Twilio API Requirements
- Twilio Account SID
- Twilio Auth Token
- Access to Twilio Phone Numbers API

---

## 🔧 WORKSTREAM 4: Improved Onboarding Flow (Frontend + Backend)

### Goal
Create a comprehensive onboarding wizard that helps the AI receptionist better represent the business owner.

### Onboarding Steps
1. **Business Profile**
   - Business name
   - Industry/vertical
   - Business hours
   - Location/timezone

2. **Phone Number Selection**
   - Dropdown of available Twilio numbers
   - Area code preference
   - Number porting option

3. **AI Persona Setup**
   - Greeting style (formal/casual/friendly)
   - Key FAQs to answer
   - Services offered
   - Custom responses

4. **Calendar Integration**
   - Connect Google Calendar
   - Set booking rules
   - Define appointment types

5. **Test Call**
   - Make a test call to verify setup
   - Review transcript
   - Approve or adjust

### Files to Create
- `frontend/dashboard/components/OnboardingWizard.tsx`
- `backend/ai_receptionist/onboarding/` module

---

## 🔧 WORKSTREAM 5: Stripe Payment Integration

### Goal
Allow customers to purchase an AI receptionist subscription and receive dashboard access.

### Purchase Flow
1. User clicks pricing tier button ("Get Started")
2. Redirect to Stripe Checkout
3. On success, create user account
4. Send email with login link
5. User accesses dashboard

### Stripe Information Needed from You
To implement Stripe, I need:
- [ ] **Stripe Publishable Key** (pk_live_xxx or pk_test_xxx)
- [ ] **Stripe Secret Key** (sk_live_xxx or sk_test_xxx)
- [ ] **Stripe Webhook Signing Secret** (whsec_xxx)
- [ ] **Product IDs** for each pricing tier (or I can create them)
- [ ] **Price IDs** for each tier's monthly/annual pricing

### Backend Endpoints Needed
```python
POST /api/stripe/create-checkout-session
POST /api/stripe/webhook  # Handle payment success
GET  /api/stripe/subscription-status
```

### Files to Create/Modify
- `backend/ai_receptionist/payments/` module
- `frontend/portfolio/templates/checkout.html`
- `frontend/dashboard/pages/login.tsx` (add signup)

---

## 🔧 WORKSTREAM 6: Pricing Page CTAs (Frontend)

### Goal
Connect the pricing tier buttons to the dashboard/signup flow.

### Tasks
- [ ] "Get Started" → Stripe Checkout (Starter tier)
- [ ] "Start Free Pilot" → Signup/Login + Pilot flag
- [ ] "Contact Sales" → Contact form or email link
- [ ] Add proper tracking (UTM params)

---

## 📊 Priority Matrix

| Workstream | Priority | Effort | Dependencies |
|------------|----------|--------|--------------|
| WS1: Mobile UI | High | Medium | None |
| WS2: Real-time Features | High | High | Backend APIs |
| WS3: Phone Integration | High | Medium | Twilio credentials |
| WS4: Onboarding | Medium | High | WS3 complete |
| WS5: Stripe Integration | High | Medium | Stripe credentials |
| WS6: Pricing CTAs | Medium | Low | WS5 complete |

---

## 📝 Immediate Next Steps

1. **You Provide**: Stripe API keys (test mode is fine to start)
2. **You Provide**: Confirm Twilio credentials are already configured
3. **I Start**: Mobile UI improvements (WS1)
4. **I Start**: Real-time calendar/clock fix (WS2a)

---

## 🔐 Credentials Checklist

### Already Have
- [x] SSH access to droplet
- [x] GitHub repository access
- [ ] Twilio Account SID & Auth Token (confirm)
- [ ] Stripe API keys (needed from you)

### For Stripe - What I Need
Please provide (in a secure way):
1. `STRIPE_PUBLISHABLE_KEY` - Public key for frontend
2. `STRIPE_SECRET_KEY` - Secret key for backend
3. `STRIPE_WEBHOOK_SECRET` - For verifying webhook signatures

You can create these at: https://dashboard.stripe.com/apikeys

---

## 🏗️ TDD Workflow Upgrade

I'm upgrading the workflow file to include all testing commands.
