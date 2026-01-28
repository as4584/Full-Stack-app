# AI Receptionist Documentation Index

Welcome to the AI Receptionist documentation. This index will help you find the right document for your needs.

---

## 📚 Documentation Overview

### For Gemini AI / Brainstorming
- **[GEMINI_SYSTEM_KNOWLEDGE.md](GEMINI_SYSTEM_KNOWLEDGE.md)** ⭐ **START HERE**
  - Complete system overview for AI assistants
  - Architecture, costs, capabilities, limitations
  - Google AI integration opportunities
  - Questions for brainstorming improvements

---

## 🔧 System Documentation

### Critical References
- **[AI_RECEPTIONIST_SOURCE_OF_TRUTH.md](AI_RECEPTIONIST_SOURCE_OF_TRUTH.md)** ⚠️ **MUST READ BEFORE CHANGES**
  - Authoritative system configuration
  - Port configuration, endpoint routing
  - Twilio and OpenAI settings
  - Common failure modes and fixes

### Architecture & Code
- **[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)**
  - Code refactoring history
  - Architecture decisions
  - Module organization

- **[TECHNICAL_DEBT_AUDIT.md](TECHNICAL_DEBT_AUDIT.md)**
  - Known technical debt
  - Areas needing improvement
  - Prioritized action items

---

## 💰 Cost & Performance

- **[COST_DIAGNOSIS.md](COST_DIAGNOSIS.md)**
  - Detailed cost breakdown ($0.95 per 3-min call)
  - Cost comparison with alternatives
  - Optimization recommendations (85-90% savings possible)
  - Modular architecture options

- **[SPEED_OPTIMIZATION.md](SPEED_OPTIMIZATION.md)**
  - Recent speed improvements (10s → 2-3s)
  - System instruction optimization
  - Turn detection tuning
  - Performance metrics

---

## 🐛 Bug Fixes & Issues

- **[SILENCE_BUG_FIX.md](SILENCE_BUG_FIX.md)**
  - Race condition fix (calls were silent)
  - Root cause analysis
  - Solution implementation
  - Includes speed optimization follow-up

---

## 🚀 Deployment & Operations

- **[OPERATIONS.md](OPERATIONS.md)**
  - Service overview and URLs
  - Common operational tasks
  - Database access
  - Log viewing

- **[RELEASE_PLAN.md](RELEASE_PLAN.md)**
  - Deployment procedures
  - Rollback steps
  - Blue/Green deployment strategy

---

## 📋 Business & Onboarding

- **[README.md](README.md)**
  - Quick start guide
  - Local development setup
  - Deployment overview

- **[onboarding_checklist.md](onboarding_checklist.md)**
  - New user onboarding steps
  - Setup requirements
  - Testing procedures

- **[pilot_agreement.md](pilot_agreement.md)**
  - Pilot program terms
  - Service level expectations
  - Pricing and billing

---

## 🧪 Testing & Evaluation

- **[EVAL_SYSTEM_README.md](EVAL_SYSTEM_README.md)**
  - Evaluation pipeline overview
  - Scenario generation
  - Metrics and reporting
  - Auto-improvement system

---

## Quick Navigation by Use Case

### "I want to understand the entire system"
→ Start with [GEMINI_SYSTEM_KNOWLEDGE.md](GEMINI_SYSTEM_KNOWLEDGE.md)

### "I need to make code changes"
→ Read [AI_RECEPTIONIST_SOURCE_OF_TRUTH.md](AI_RECEPTIONIST_SOURCE_OF_TRUTH.md) first

### "I want to reduce costs"
→ See [COST_DIAGNOSIS.md](COST_DIAGNOSIS.md)

### "The system is broken"
→ Check [AI_RECEPTIONIST_SOURCE_OF_TRUTH.md](AI_RECEPTIONIST_SOURCE_OF_TRUTH.md) Common Failure Modes

### "I want to deploy changes"
→ Follow [RELEASE_PLAN.md](RELEASE_PLAN.md)

### "I want to integrate Google AI"
→ Review [GEMINI_SYSTEM_KNOWLEDGE.md](GEMINI_SYSTEM_KNOWLEDGE.md) Integration Opportunities

### "I want to improve performance"
→ See [SPEED_OPTIMIZATION.md](SPEED_OPTIMIZATION.md)

### "I want to test the system"
→ Use [EVAL_SYSTEM_README.md](EVAL_SYSTEM_README.md)

---

## Document Status

| Document | Last Updated | Status |
|----------|--------------|--------|
| GEMINI_SYSTEM_KNOWLEDGE.md | 2025-12-22 | ✅ Current |
| AI_RECEPTIONIST_SOURCE_OF_TRUTH.md | 2025-12-14 | ✅ Current |
| COST_DIAGNOSIS.md | 2025-12-22 | ✅ Current |
| SPEED_OPTIMIZATION.md | 2025-12-22 | ✅ Current |
| SILENCE_BUG_FIX.md | 2025-12-22 | ✅ Current |
| OPERATIONS.md | 2025-12-14 | ✅ Current |
| RELEASE_PLAN.md | 2025-12-14 | ✅ Current |

---

## Contributing to Documentation

When adding new documentation:
1. Place it in the `docs/` folder
2. Update this index with a link and description
3. Add it to the appropriate category
4. Update the "Document Status" table
5. Cross-reference related documents

---

**System Version**: 1.0 (OpenAI Realtime API)  
**Documentation Maintained By**: AI Assistant  
**Last Index Update**: December 22, 2025
