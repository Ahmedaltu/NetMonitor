# app/collectors/traceroute.py

import subprocess
import re
import platform
from app.collectors.base import BaseCollector
from app.utils.logger import logger


class TracerouteCollector(BaseCollector):
    """Run traceroute to a target and record hop-by-hop latency."""

    name = "traceroute"

    def __init__(self, settings=None):
        self.max_hops = 30
        self.timeout = 5
        self._is_windows = platform.system().lower() == "windows"

    def collect(self, target: str = None) -> dict:
        if not target:
            return {}
        return self._run_traceroute(target)

    def _run_traceroute(self, target: str) -> dict:
        if self._is_windows:
            cmd = ["tracert", "-d", "-w", str(self.timeout * 1000), "-h", str(self.max_hops), target]
        else:
            cmd = ["traceroute", "-n", "-w", str(self.timeout), "-m", str(self.max_hops), target]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.max_hops * self.timeout + 10,
            )
            hops = self._parse_output(result.stdout)

            return {
                "traceroute_target": target,
                "traceroute_hops": hops,
                "traceroute_hop_count": len(hops),
                "traceroute_complete": any(
                    h.get("ip") == target for h in hops
                ) if hops else False,
            }
        except subprocess.TimeoutExpired:
            logger.warning("Traceroute timed out for %s", target)
            return {
                "traceroute_target": target,
                "traceroute_hops": [],
                "traceroute_hop_count": 0,
                "traceroute_complete": False,
                "traceroute_error": "timeout",
            }
        except FileNotFoundError:
            logger.error("traceroute/tracert command not found")
            return {
                "traceroute_target": target,
                "traceroute_hops": [],
                "traceroute_hop_count": 0,
                "traceroute_complete": False,
                "traceroute_error": "command_not_found",
            }

    def _parse_output(self, output: str) -> list:
        hops = []
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue

            # Match hop number at the start
            hop_match = re.match(r"^\s*(\d+)\s+", line)
            if not hop_match:
                continue

            hop_num = int(hop_match.group(1))

            # Check for timeout (* * *)
            if line.count("*") >= 3 and not re.search(r"\d+\.\d+\.\d+\.\d+", line):
                hops.append({
                    "hop": hop_num,
                    "ip": None,
                    "rtts": [],
                    "avg_rtt": None,
                })
                continue

            # Extract IP address
            ip_match = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
            ip = ip_match.group(1) if ip_match else None

            # Extract RTT values (e.g., "12 ms", "12.3 ms", "<1 ms")
            rtts = []
            for m in re.finditer(r"[<]?(\d+(?:\.\d+)?)\s*ms", line):
                rtts.append(float(m.group(1)))

            avg_rtt = round(sum(rtts) / len(rtts), 2) if rtts else None

            hops.append({
                "hop": hop_num,
                "ip": ip,
                "rtts": rtts,
                "avg_rtt": avg_rtt,
            })

        return hops
