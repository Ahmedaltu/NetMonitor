# README Quality Checklist

Use this checklist to audit any README. Score each item as:
- **OK** — Present and accurate
- **OUTDATED** — Present but doesn't match codebase
- **MISSING** — Should exist but doesn't
- **N/A** — Not applicable

---

## Identity

- [ ] Project name is clear and prominent (H1)
- [ ] One-line description explains what the project does
- [ ] Badges present (build status, version, license) if applicable

## Visual

- [ ] Screenshot or demo GIF showing the product (if it has a UI)
- [ ] Architecture diagram (if the system has multiple components)
- [ ] Diagrams use Mermaid (renders natively on GitHub) when possible

## Features

- [ ] Feature list exists
- [ ] Every listed feature is actually implemented
- [ ] No major implemented features are missing from the list
- [ ] Features match what the codebase actually provides

## Prerequisites

- [ ] Runtime requirements listed (Python version, Node version, etc.)
- [ ] External service dependencies noted (databases, APIs, Docker)
- [ ] OS-specific requirements mentioned if applicable

## Installation

- [ ] Clone command is correct
- [ ] Dependency install commands are complete and correct
- [ ] Virtual environment / package manager setup is covered
- [ ] Environment variable setup is documented
- [ ] All commands are copy-paste ready

## Configuration

- [ ] Config file format and location documented
- [ ] All config options explained (or link to config docs)
- [ ] Example config provided or referenced
- [ ] Secrets / tokens handling explained

## Usage

- [ ] How to start / run the application
- [ ] All entry points documented (backend, frontend, CLI)
- [ ] Common use cases shown with examples
- [ ] Expected output described where helpful

## API / Endpoints

- [ ] All API endpoints listed (or linked to API docs)
- [ ] Request/response examples provided
- [ ] Authentication requirements noted
- [ ] Every listed endpoint actually exists in the codebase

## Docker / Deployment

- [ ] Docker commands include all necessary flags (ports, volumes, env vars)
- [ ] docker-compose setup documented if it exists
- [ ] Production deployment guidance provided
- [ ] Environment-specific notes (dev vs prod) included

## External Services

- [ ] Each external service (DB, monitoring, LLM, etc.) has setup instructions
- [ ] Default credentials / URLs documented
- [ ] Data source configuration steps included (e.g., Grafana → InfluxDB)
- [ ] Service dependencies are clear (what needs what)

## Testing

- [ ] How to run tests
- [ ] Test dependencies noted if different from main deps
- [ ] Test coverage info if available

## Project Structure

- [ ] File tree matches actual project structure
- [ ] Key directories have descriptions
- [ ] No phantom directories/files listed that don't exist

## Contributing

- [ ] Contribution guidelines exist (or link to CONTRIBUTING.md)
- [ ] Code style / linting requirements noted
- [ ] PR process described

## License

- [ ] License type stated
- [ ] Matches actual LICENSE file in repo

## Cross-Cutting Quality

- [ ] All code blocks have language tags (```bash, ```python, etc.)
- [ ] No broken internal links
- [ ] Consistent heading hierarchy (no skipped levels)
- [ ] Table of contents for long READMEs (>300 lines)
- [ ] No outdated version numbers or URLs
- [ ] Commands work on the project's target platform(s)
- [ ] Emojis used consistently (all sections or none)
