# Claude Code Agent System — NetMonitor

## How to use this system
Paste this prompt into Claude Code to instantly set up a professional agent for the NetMonitor project. This prompt includes project memory, agent skills, and workflow rules for consistent, high-quality development.

---

## Project Memory (CLAUDE.md)
See CLAUDE.md in the project root for:
- Project description
- Live URLs
- Stack and environment variables
- Project structure and file tree
- API endpoints
- Architecture decisions
- Known issues and solutions
- Coding conventions
- Recent changes
- Next steps

---

## Agent Skills (.claude/commands/)
- **debug.md** — Systematic debugging workflow
- **add-feature.md** — Add new features correctly
- **deploy.md** — Deploy the project safely
- **review.md** — Code review checklist
- **update-context.md** — Update project memory after changes
- **refactor.md** — Refactor code safely

---

## Rules to Always Follow
- Update CLAUDE.md after EVERY significant change
- Never remove existing context from CLAUDE.md, only add/update
- Always run /update-context before ending a session
- Keep Recent Changes to last 10 entries
- One focused fix per commit
- Never expose secrets or tokens in code or logs
- Always handle errors — no unhandled promises

---

## Quick Start
1. Read CLAUDE.md for project context
2. Use /debug, /add-feature, /deploy, /review, /update-context, or /refactor as needed
3. Update CLAUDE.md after every change
4. Run /update-context before ending your session
