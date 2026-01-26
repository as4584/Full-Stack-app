---
name: browser_verification
description: Forces the agent to use the browser tool to verify UI changes and functionality before considering a task complete.
---

# Browser Verification Skill

This skill ensures that all frontend changes are verified using the `browser_subagent` tool.

## Instructions

1.  **Always Open Browser**: After any frontend modification or if a functionality is reported as broken, you MUST open the browser to the relevant URL (usually `http://localhost:3000`).
2.  **Verify State**: 
    - Check if the page loads without errors.
    - Inspect the DOM or take screenshots to verify visual changes.
    - Use the subagent to click buttons and verify interactive flows (e.g., OAuth, searches).
3.  **Debug Failures**:
    - If a button doesn't work, use the browser subagent to check the console logs.
    - Inspect network requests if an API call fails.
4.  **Repeat Until Success**: Do not stop until the browser confirms the feature is working as intended.

## Workflow

1.  Navigate to the page.
2.  Perform the action (e.g., click "Connect Google Cal").
3.  Wait for the page to update or check for specific elements.
4.  Capture a screenshot if needed for the user.
5.  Check for errors in the terminal or browser console.
