---
name: database_management
description: Directly query and manage the application's SQLite database using natural language and MCP tools.
---

# Database Management Skill

This skill allows you to inspect the application state, verify user transactions, and manage tenant data without manual SQL writing.

## Instructions

1.  **Inspect State**: Use the `sqlite-mcp-server` tools to check the current state of the `sql_app.db`.
2.  **Verify Flow**: After a user signs up or performs an action, verify that the data was correctly written to the database.
3.  **Audit Logs**: Use the database tools to pull call transcripts or logs to help with debugging backend issues.
4.  **Safe Modification**: When requested to update a plan or a flag, use the database tools to perform the update and verify the change immediately.

## Tools to Use
- `sqlite-mcp-server` (e.g., `query`, `list_tables`)
