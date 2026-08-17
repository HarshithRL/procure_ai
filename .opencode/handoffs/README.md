# Handoff Notes — Inter-Agent Status

This directory holds handoff notes between agent sessions. Use this to track:
- Current task status and blockers
- What the next agent should focus on
- Known issues or gotchas discovered
- Git branch status and uncommitted work
- Link to the task plan in `.design_docs/assistent/tasks/`

## Format

Create a file named after the task or agent:
```
handoff_sprint1_flask_app.md
handoff_frontend_dashboard.md
handoff_BLOCKER_databricks_auth.md  (if blocked, prefix with "BLOCKER_")
```

Include:
1. **Status**: What was accomplished
2. **Next Steps**: What the next agent should do
3. **Blockers**: Any issues preventing progress (if any)
4. **Git State**: Current branch, uncommitted changes
5. **Task Plan**: Link to `.design_docs/assistent/tasks/<task>.md`

## Example

```markdown
# Handoff: Flask App Setup

**Status**: Core Flask app scaffolded, blueprint structure created, no routes yet

**Next Steps**:
1. Implement `/api/profile` endpoint with X-Forwarded header extraction
2. Add telemetry logging (Sections 5 in Sprint 1 checklist)
3. Test with Databricks SSO headers locally

**Blockers**: None

**Git State**: Branch `feature/sprint1-flask-app`, 3 commits, ready to push

**Task Plan**: `.design_docs/assistent/tasks/task_sprint1_flask_app.md`
```

## Tips
- Keep handoffs short and actionable
- Reference task plans, not just JIRA/GitHub issues
- If blocked, use BLOCKER_ prefix and include repro steps
- Commit handoff notes as part of the task completion
