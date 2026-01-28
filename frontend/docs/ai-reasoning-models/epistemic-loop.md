# The Epistemic Loop — AI Reasoning Model

This model defines how the AI (Antigravity/Copilot) thinks about CI/CD problems.

## Phase 1: Ingestion
*   **Input**: CI Failure Log / User Request
*   **Context**: `docs/ci-architecture.md`, `docs/deployment.md`
*   **State**: Current git branch, modified files.

## Phase 2: Hypothesis Generation
The AI must generate at least 3 hypotheses for any failure, ranked by probability.

*Example:*
1.  *Hypothesis A (80%)*: `starlette` version conflict due to `fastapi` upgrade.
2.  *Hypothesis B (15%)*: Transient network failure during `pip install`.
3.  *Hypothesis C (5%)*: `pip-audit` database is outdated.

## Phase 3: Experiment Design
For the top hypothesis, design a **falsifiable test**.
*   *Test*: Downgrade `starlette` in `requirements.txt` and run `pip install`.
*   *Success Condition*: Installation succeeds.

## Phase 4: Execution & Observation
Run the test. Capture stdout/stderr.

## Phase 5: Conclusion & Recursion
*   If Success: Commit the fix. Update `CI_HEALTH.md`.
*   If Failure: Discard Hypothesis A. Promote Hypothesis B. **Recurse to Phase 3.**

## Phase 6: Knowledge Crystalization
Once solved, record the pattern.
"If `fastapi==0.115.3`, THEN `starlette` MUST be `0.41.2`."
