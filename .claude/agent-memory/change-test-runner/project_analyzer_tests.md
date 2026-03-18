---
name: Analyzer test coverage
description: Coverage status for app/ai/analyzer.py — no prior tests existed; test_analyzer.py was created in this session
type: project
---

`app/ai/analyzer.py` had zero test coverage before this session.

`tests/test_analyzer.py` was created (25 tests) covering:
- `_get_influx_client`: cache creation, cache hit, keyed by (url, org) not token
- `fetch_recent_summary`: token env/settings fallback, client reuse, stat computation, error paths
- `generate_explanation`: empty summary, successful POST, absence of GET health-check, payload shape,
  ConnectionError / ReadTimeout / RequestException / generic exception handling, malformed response
  detection, settings override, prompt key-metric filtering

**Why:** The two changes in the commit (client cache + removal of health-check GET) had no regression
guard. These tests lock in both behaviours.
**How to apply:** Always run `tests/test_analyzer.py` when touching `app/ai/analyzer.py`.
