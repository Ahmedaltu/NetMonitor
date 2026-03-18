---
name: NetMonitor test setup
description: Test framework, runner command, file conventions, and known pre-existing failures for the NetMonitor project
type: project
---

Test framework: pytest 9.0.2 (Python 3.14.3)
Runner command: `python -m pytest tests/ --ignore=tests/test_dashboard_selenium.py`
Config in: `pyproject.toml` (rootdir), asyncio mode = STRICT

Test file conventions:
- All tests live in `tests/` at repo root
- Files named `test_<module>.py` (e.g., `test_analyzer.py` for `app/ai/analyzer.py`)
- No co-located test files — all tests are in the top-level `tests/` directory

Installed dependencies note:
- `httpx` is NOT bundled in the venv; must be installed via pip before `test_api.py` can be collected
  (`pip install httpx`)

Known pre-existing failures (unrelated to the AI analyzer change):
- `tests/test_analytics.py::TestLatencyStats::test_two_values` — `LatencyStats` has no `.percentile()` method
- `tests/test_analytics.py::TestLatencyStats::test_percentile_boundaries` — same cause

test_dashboard_selenium.py requires a browser driver; always skip with --ignore.

**Why:** Captures baseline state so future runs can distinguish new regressions from pre-existing issues.
**How to apply:** When running the full suite, expect exactly 2 failures in test_analytics.py; anything beyond those is a new regression to investigate.
