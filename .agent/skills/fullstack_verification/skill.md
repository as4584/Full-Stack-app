🧠 SKILL: FULL_STACK_STATE_VERIFICATION

Purpose
Detect, isolate, and fix cases where backend changes are not reflected
in the frontend dashboard by systematically validating each layer
of the system from source of truth to UI render.

🔹 WHEN TO INVOKE
Use this skill whenever:
- Backend logic was changed but UI did not update
- A dashboard shows stale or incorrect data
- A toggle/state appears to “work” but reverts or lies
- Frontend and backend disagree about reality

🔹 CORE PRINCIPLE
Never trust the frontend.
Always verify the system from the authoritative source outward.

🔁 EXECUTION STEPS (NON-NEGOTIABLE ORDER)
1️⃣ Verify Database (Source of Truth)
- Query the database directly
- Confirm the value actually changed
- If DB is wrong → STOP and fix backend persistence

2️⃣ Verify Backend API in Isolation
- Call the API using curl or an HTTP client
- Do NOT use the frontend
- Confirm the API returns the updated value


Rule:

If curl is wrong, the UI is irrelevant.

3️⃣ Verify Network Layer
- Inspect frontend network requests
- Confirm:
  - correct API URL
  - correct environment
  - correct request body
  - correct response payload

4️⃣ Eliminate Caching
- Hard refresh browser
- Disable cache in dev tools
- Check framework fetch caching or revalidation
- Temporarily force no-store behavior if needed

5️⃣ Verify Frontend State Updates
- Confirm frontend state is updated from API response
- Never trust optimistic toggles without reconciliation
- Backend response always wins


Anti-pattern to flag:

setState(!state) without reading response

6️⃣ Verify UI Rendering Logic
- Check conditional rendering
- Check memoization dependencies
- Check stale props or derived state
- Ensure re-render occurs on state change

7️⃣ Add Temporary Boundary Logging
- Backend: log received inputs + persisted values
- Frontend: log API response + state before/after
- Compare logs to identify the lying layer

🔒 GUARANTEES
- Exactly one layer is wrong at any time
- The backend is always more trustworthy than the UI
- The bug is never fixed by guessing

🧠 OUTPUT
- Identified faulty layer (DB, API, network, state, render)
- Concrete fix applied at the correct boundary
- No frontend “workarounds” allowed

🧩 MENTAL MODEL (for Antigravity)
Reality flows in one direction:
Database → Backend API → Network → Frontend State → UI

Never debug sideways.
Never debug from the UI inward.

✅ SHORT INVOCATION PHRASES

You can trigger this skill with any of these:

“Invoke FULL_STACK_STATE_VERIFICATION.”

“Run the frontend-backend desync skill.”

“Dashboard is stale — apply state verification skill.”