# app/collectors/http_probe.py

import requests
from app.collectors.base import BaseCollector
from app.utils.logger import logger


class HttpProbeCollector(BaseCollector):
    """Probe HTTP/HTTPS endpoints and measure response time and status."""

    name = "http_probe"

    def __init__(self, settings=None):
        self.probes = []
        if settings and hasattr(settings, "http_probes"):
            for p in settings.http_probes:
                self.probes.append({
                    "url": p.url,
                    "expected_status": p.expected_status,
                    "timeout": p.timeout,
                })

    def collect(self, target: str = None) -> dict:
        if not self.probes:
            return {}

        results = []
        for probe in self.probes:
            result = self._check(probe)
            results.append(result)

        # Return aggregate + per-probe detail
        successful = [r for r in results if r["success"]]
        avg_time = (
            sum(r["response_time_ms"] for r in successful) / len(successful)
            if successful
            else None
        )

        return {
            "http_probes": results,
            "http_avg_response_time": avg_time,
            "http_success_rate": len(successful) / len(results) if results else 1.0,
        }

    def _check(self, probe: dict) -> dict:
        url = probe["url"]
        expected = probe.get("expected_status", 200)
        timeout = probe.get("timeout", 5)

        try:
            resp = requests.get(url, timeout=timeout, allow_redirects=True)
            return {
                "url": url,
                "status_code": resp.status_code,
                "response_time_ms": round(resp.elapsed.total_seconds() * 1000, 1),
                "success": resp.status_code == expected,
            }
        except requests.Timeout:
            logger.warning("HTTP probe timeout: %s", url)
            return {
                "url": url,
                "status_code": None,
                "response_time_ms": None,
                "success": False,
                "error": "timeout",
            }
        except requests.RequestException as e:
            logger.warning("HTTP probe failed: %s — %s", url, e)
            return {
                "url": url,
                "status_code": None,
                "response_time_ms": None,
                "success": False,
                "error": str(e),
            }
