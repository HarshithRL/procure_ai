# AI Coding Agent Repository Map

## 1. Knowledge

`/knowledge`

The **Knowledge** repository contains the complete and current design context for the application.

### Purpose

This repository is the **source of truth for product, business, UX, architecture, and technical design knowledge**.

It contains:

- Business requirements
- Product scope
- Application flow
- UX/UI design
- System architecture
- Agent architecture
- Data models
- Domain knowledge
- Technical decisions
- Current implementation focus
- Design decisions and constraints
- Future plans / roadmap

### Access Rule

> [!important]
> **Knowledge is strictly READ-ONLY for all coding agents.**

The following coding agents must **never modify files inside `/knowledge`**:

- Claude Code
- OpenCode
- Cursor AI
- Antigravity

Coding agents may:

- Read knowledge
- Search knowledge
- Reference knowledge
- Use knowledge to understand requirements and implementation context

Coding agents must **not**:

- Create files
- Modify files
- Delete files
- Rewrite documentation
- Update architecture/design directly

Any change to Knowledge must be made intentionally by the project owner / authorized documentation workflow.

---

# 2. Assistant

`/assistant`

The **Assistant** repository is the centralized workspace for all AI coding assistants and coding harness configuration.

It acts as the **common control plane for coding agents**.

### Supported Coding Agents

The same centralized Assistant workspace is used by:

- Claude Code
- OpenCode
- Cursor AI
- Antigravity

### Purpose

All coding-agent-specific instructions, rules, skills, configurations, and harness files should be centralized and organized inside `/assistant`.

Examples include:

- `AGENTS.md`
- `CLAUDE.md`
- `.claude/`
- `.agent/`
- `.opencode/`
- Skills
- Agent instructions
- Coding rules
- Development workflows
- Tool usage rules
- Project-specific coding conventions
- Shared prompts / context
- Agent configuration

### Access Rule

> [!important]
> **Assistant is the CORE READ/WRITE workspace for all coding agents.**

Coding agents are allowed to:

- Read files
- Create files
- Modify files
- Update instructions
- Add skills
- Improve agent workflows
- Maintain coding-agent configuration
- Organize harness-specific resources

All coding agents should treat `/assistant` as their **centralized operational workspace**.

---

# 3. Repository Relationship

```text
                    PROJECT
                       │
            ┌──────────┴──────────┐
            │                     │
            ▼                     ▼
       /knowledge              /assistant
            │                     │
            │                     │
       SOURCE OF TRUTH       CODING CONTROL PLANE
            │                     │
            │                     │
         READ ONLY           READ + WRITE
            │                     │
            │                     │
    ┌───────┼────────┐      ┌─────┼──────────────┐
    │       │        │      │     │      │       │
    ▼       ▼        ▼      ▼     ▼      ▼       ▼
 Claude  OpenCode Cursor  Claude OpenCode Cursor Antigravity
 Code                         Code