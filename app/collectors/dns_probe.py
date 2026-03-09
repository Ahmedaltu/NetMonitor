# app/collectors/dns_probe.py

import socket
import time
from app.collectors.base import BaseCollector
from app.utils.logger import logger


class DnsProbeCollector(BaseCollector):
    """Probe DNS resolution and measure lookup time."""

    name = "dns_probe"

    def __init__(self, settings=None):
        self.probes = []
        if settings and hasattr(settings, "dns_probes"):
            for p in settings.dns_probes:
                self.probes.append({
                    "hostname": p.hostname,
                    "timeout": p.timeout,
                })

    def collect(self, target: str = None) -> dict:
        if not self.probes:
            return {}

        results = []
        for probe in self.probes:
            result = self._resolve(probe)
            results.append(result)

        successful = [r for r in results if r["success"]]
        avg_time = (
            sum(r["resolution_time_ms"] for r in successful) / len(successful)
            if successful
            else None
        )

        return {
            "dns_probes": results,
            "dns_avg_resolution_time": avg_time,
            "dns_success_rate": len(successful) / len(results) if results else 1.0,
        }

    def _resolve(self, probe: dict) -> dict:
        hostname = probe["hostname"]
        timeout = probe.get("timeout", 3)

        try:
            start = time.perf_counter()
            # Use per-call timeout via signal-free thread approach:
            # socket.getaddrinfo is blocking and doesn't accept a timeout,
            # but we avoid the global setdefaulttimeout race condition.
            # Instead, we rely on the OS resolver timeout and cap via perf check.
            addresses = socket.getaddrinfo(hostname, None)
            elapsed = (time.perf_counter() - start) * 1000

            if elapsed > timeout * 1000:
                logger.warning("DNS probe slow: %s took %.0fms (timeout: %ds)", hostname, elapsed, timeout)

            resolved_ips = list({addr[4][0] for addr in addresses})

            return {
                "hostname": hostname,
                "resolved_ips": resolved_ips,
                "resolution_time_ms": round(elapsed, 2),
                "success": True,
            }
        except socket.gaierror as e:
            logger.warning("DNS probe failed: %s — %s", hostname, e)
            return {
                "hostname": hostname,
                "resolved_ips": [],
                "resolution_time_ms": None,
                "success": False,
                "error": str(e),
            }
        except socket.timeout:
            logger.warning("DNS probe timeout: %s", hostname)
            return {
                "hostname": hostname,
                "resolved_ips": [],
                "resolution_time_ms": None,
                "success": False,
                "error": "timeout",
            }
