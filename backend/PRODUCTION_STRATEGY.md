# Production Strategy for AI Receptionist Dashboard

## 1. Core Principle

**Production means zero framework internals visible to users—if they see Next.js warnings, React error boundaries, or backend stack traces, we have failed.**

---

## 2. Frontend Strategy

### Build & Deployment Rules
- **MUST**: Run `npm run build` + `npm start` in production (never `npm run dev`)
- **MUST**: Set `NODE_ENV=production` in production environments
- **MUST**: Fail CI if `npm run build` fails (type errors, missing imports, etc.)
- **NEVER**: Deploy development mode to production (dev mode is for developers, not users)

### Error Handling Philosophy
```tsx
// ❌ WRONG: Treat empty data as error
if (callsError || !calls) {
  showErrorToast("Failed to load calls");
}

// ✅ RIGHT: Only treat HTTP errors as errors
if (callsError?.status >= 500) {
  showErrorToast("Unable to load calls");
} else if (calls?.length === 0) {
  showEmptyState("No calls yet");
}
```

### Implementation Requirements
1. **Error Boundaries**: Wrap all route-level components in React Error Boundaries that show friendly "Something went wrong" pages
2. **Suspense Boundaries**: Wrap all `useSearchParams()`, `useRouter()`, and async components in `<Suspense>`
3. **Defensive Rendering**: Always check `error.status` before showing error UI—`null`, `[]`, and `undefined` are not errors
4. **Loading States**: Show spinners for loading, not errors
5. **Empty States**: Design explicit empty state UI (illustrations, CTAs) for zero-data scenarios

### What Users See
- Loading spinner → Empty state with "Get started" CTA
- Loading spinner → Data loaded successfully
- Loading spinner → "Unable to connect, please refresh" (for 500/network errors only)

---

## 3. Backend Strategy

### API Contract Guarantees

**HTTP Status Codes**:
- `200`: Success (even if data is empty, null, or disabled)
- `401`: Authentication required
- `403`: Forbidden (has auth, insufficient permissions)
- `404`: Only for truly invalid routes or IDs that do not belong to the authenticated user. **NEVER** for "user has no data yet" scenarios (e.g., business profile, calls, settings)
- `500`: Unexpected server error (should NEVER happen in normal operation)

**404 Usage Rule**:
- ✅ Use 404: `/api/businesses/999999` (ID doesn't exist or belongs to another user)
- ❌ Don't use 404: `/api/business/me` (user exists but hasn't created business yet → return `null`)
- ❌ Don't use 404: `/api/business/calls` (user has no calls yet → return `[]`)

**Expected States Must Return 200**:
```python
# ❌ WRONG: 404 for new user without business
if not business:
    raise HTTPException(status_code=404, detail="Business not found")

# ✅ RIGHT: 200 with null
if not business:
    return None  # Frontend handles null gracefully

# ❌ WRONG: 500 for empty data
calls = get_user_calls(user_id)
if not calls:
    raise Exception("No calls found")

# ✅ RIGHT: 200 with empty array
calls = get_user_calls(user_id)
return calls  # Returns [] if empty—totally valid
```

### Optional Integration Behavior
- If integration is disabled → Return `{"enabled": false, "data": null}`
- If integration fails → Log error, return cached/empty data with flag: `{"available": false, "reason": "temporary_issue"}`
- **NEVER** let optional features break core dashboard

### Error Response Structure
```python
# For expected business logic failures (not server errors)
return {
    "success": False,
    "error_code": "INSUFFICIENT_BALANCE",
    "message": "Your account balance is too low",
    "user_message": "Please add funds to continue"
}
```

### Database Query Safety
- **MUST**: Validate columns exist before querying (or use ORM that catches at startup)
- **MUST**: Return `[]` for empty query results, not `None`
- **MUST**: Catch database errors and return user-friendly messages, not stack traces

### Dashboard Health Contract
- **Dashboard must render successfully if ALL endpoints return 200 + valid JSON**
- **Empty arrays, nulls, and disabled integrations must not trigger error UI**
- **No single widget failure may block the dashboard shell**

---

## 4. CI & Verification Strategy

### Pre-Merge Checks (Block PR)
1. ✅ `npm run build` succeeds (frontend)
2. ✅ `pytest tests/` passes (backend unit tests)
3. ✅ No TypeScript errors
4. ✅ No ESLint errors blocking production

### Pre-Deploy Checks (Block Deploy)
1. ✅ Production build artifact exists
2. ✅ E2E smoke tests pass against staging:
   ```bash
   test_dashboard_loads()
   test_auth_endpoints_work()
   test_critical_user_flows()
   ```
3. ✅ Health check passes: `/api/health` returns 200

### Post-Deploy Verification (Rollback Trigger)
1. ✅ Synthetic user test: Login → View dashboard → No 500 errors
2. ✅ Error rate < 0.1% (monitor for 5 minutes)
3. ✅ P95 response time < 2 seconds
4. ❌ If any check fails → Automatic rollback

### Monitoring & Alerting
- Alert on any 500 error in production
- Alert on error rate > 1%
- Alert on dashboard load time > 5 seconds
- Weekly report: Zero 500 errors expected

---

## 5. User Experience Rules

### What Users Are Allowed To See
✅ **Loading states**: Spinners, skeleton screens  
✅ **Empty states**: "No calls yet—get started by configuring your receptionist"  
✅ **Temporary unavailability**: "Unable to connect right now, please refresh"  
✅ **Business logic feedback**: "Your trial has ended—upgrade to continue"  
✅ **Form validation**: "Email address is required"  

### What Users Must NEVER See
❌ Next.js dev warnings or red error overlay  
❌ React stack traces or component names  
❌ Database errors ("column does not exist")  
❌ HTTP 500 error details  
❌ "undefined", "null", "[object Object]"  
❌ Framework internals (Suspense warnings, hydration errors)  
❌ Dev-only messages ("Failed to load fast refresh")  

### How Errors Are Communicated
**Transient Errors** (network, temporary backend issues):
- Subtle inline message: "Unable to load recent calls"
- Auto-retry in background
- Don't block other dashboard sections

**Permanent Errors** (auth failure, account suspended):
- Clear modal or banner explaining issue
- Actionable next step ("Log in again" or "Contact support")
- Block relevant action, not entire dashboard

**Empty States** (no data):
- Illustration + headline + CTA
- Treat as onboarding opportunity, not failure

---

## 6. Operational Guarantees

### How This Prevents Regressions
1. **Production builds catch type errors** → No runtime surprises from missing types
2. **E2E tests catch API contract breaks** → Backend changes that break frontend are blocked
3. **Health checks catch deploy issues** → Bad deploys never reach users
4. **Error monitoring alerts immediately** → First user error triggers investigation, not hundredth

### How This Reduces Firefighting
- **No more "works on my machine"** → Production builds tested in CI
- **No more "SQL column missing"** → E2E tests catch schema/code mismatches
- **No more "user saw dev warning"** → Production mode enforced
- **No more "empty data broke UI"** → Defensive rendering + empty state tests

### Technical Debt Prevention
- **TypeScript strict mode** → Catch null/undefined issues at build time
- **API response schemas** → Backend changes require frontend approval
- **Component-level error boundaries** → One component failure doesn't crash app
- **Incremental adoption** → Fix highest-traffic pages first, expand coverage

---

## 7. Final Recommendation: Production Checklist

### ✅ DO THIS

**Frontend**:
- [ ] Deploy production builds only (`npm run build` + `npm start`)
- [ ] Add React Error Boundaries to all route components
- [ ] Wrap all `useSearchParams()` in `<Suspense>`
- [ ] Check `error?.status >= 500` before showing error UI
- [ ] Design empty states for zero-data scenarios
- [ ] Test with empty responses: `calls: []`, `business: null`

**Backend**:
- [ ] Return `200` for empty/null/disabled states
- [ ] Return `401` for auth failures (not 500)
- [ ] Return `404` only for invalid routes/IDs, never for "no data yet"
- [ ] Validate DB schema matches code at startup
- [ ] Log errors server-side, return friendly messages to users
- [ ] Never expose stack traces or internal errors in API responses

**CI/CD**:
- [ ] Block merge if `npm run build` fails
- [ ] Run E2E smoke tests before every deploy
- [ ] Auto-rollback if post-deploy health check fails
- [ ] Alert on first 500 error in production

**Monitoring**:
- [ ] Track dashboard load time (target: <2s)
- [ ] Track error rate (target: <0.1%)
- [ ] Weekly zero-500-error report
- [ ] Synthetic user test runs every 5 minutes

### ❌ NEVER DO THIS

- [ ] ❌ Run `npm run dev` in production
- [ ] ❌ Deploy without running `npm run build` first
- [ ] ❌ Return 500 for "user has no data" scenarios
- [ ] ❌ Return 404 for "user has no data yet" scenarios
- [ ] ❌ Treat empty arrays or null values as errors in UI
- [ ] ❌ Show framework warnings or stack traces to users
- [ ] ❌ Let optional integrations break core dashboard
- [ ] ❌ Deploy without post-deploy health check
- [ ] ❌ Ignore 500 errors ("it's just one user")

---

**Final Note**: The current issue—dev warning showing to users—is the symptom. The disease is running development mode in production. Fix the infrastructure first (production builds), then add defensive patterns (error boundaries, empty states, status code checking) so this category of issue can never recur.
