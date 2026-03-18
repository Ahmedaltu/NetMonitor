# app/collectors/dns_probe.py

import socket
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from app.collectors.base import BaseCollector
from app.utils.logger import logger

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="dns_probe")


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

        # Submit all probes concurrently, then collect results
        futures = {self._submit(probe): probe for probe in self.probes}
        results = [self._collect_future(future, probe) for future, probe in futures.items()]

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

        start = time.perf_counter()
        future = _executor.submit(socket.getaddrinfo, hostname, None)
        try:
            addresses = future.result(timeout=timeout)
            elapsed = (time.perf_counter() - start) * 1000
            resolved_ips = list({addr[4][0] for addr in addresses})
            return {
                "hostname": hostname,
                "resolved_ips": resolved_ips,
                "resolution_time_ms": round(elapsed, 2),
                "success": True,
            }
        except FuturesTimeoutError:
            elapsed = (time.perf_counter() - start) * 1000
            logger.warning("DNS probe timeout: %s (%.0fms)", hostname, elapsed)
            return {
                "hostname": hostname,
                "resolved_ips": [],
                "resolution_time_ms": None,
                "success": False,
                "error": "timeout",
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
