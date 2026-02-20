import pytest
import asyncio
from app import main

@pytest.mark.asyncio
async def test_main_loop_runs_one_cycle(monkeypatch):
    # Patch INTERVAL_SECONDS to 0.1 for fast test
    monkeypatch.setattr(main, 'INTERVAL_SECONDS', 0.1)
    # Patch collectors to only run once
    called = {'count': 0}
    orig_sleep = asyncio.sleep
    async def fake_sleep(secs):
        called['count'] += 1
        if called['count'] > 1:
            raise KeyboardInterrupt()
        await orig_sleep(0)
    monkeypatch.setattr(asyncio, 'sleep', fake_sleep)
    try:
        await main.main_loop()
    except KeyboardInterrupt:
        pass
