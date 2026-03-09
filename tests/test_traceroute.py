import subprocess
from unittest.mock import patch, MagicMock

import pytest

from app.collectors.traceroute import TracerouteCollector


# ── Sample outputs ────────────────────────────────────────────

LINUX_OUTPUT_COMPLETE = """\
traceroute to 8.8.8.8 (8.8.8.8), 30 hops max, 60 byte packets
 1  192.168.1.1  1.234 ms  1.100 ms  0.980 ms
 2  10.0.0.1  5.678 ms  5.432 ms  5.210 ms
 3  8.8.8.8  12.345 ms  12.100 ms  11.900 ms
"""

LINUX_OUTPUT_INCOMPLETE = """\
traceroute to 8.8.8.8 (8.8.8.8), 30 hops max, 60 byte packets
 1  192.168.1.1  1.234 ms  1.100 ms  0.980 ms
 2  * * *
 3  10.0.0.1  5.678 ms  5.432 ms  5.210 ms
"""

WINDOWS_OUTPUT_COMPLETE = """\
Tracing route to 8.8.8.8 over a maximum of 30 hops

  1    <1 ms    <1 ms    <1 ms  192.168.1.1
  2     5 ms     5 ms     4 ms  10.0.0.1
  3    12 ms    11 ms    12 ms  8.8.8.8

Trace complete.
"""

WINDOWS_OUTPUT_TIMEOUT_HOPS = """\
Tracing route to 8.8.8.8 over a maximum of 30 hops

  1    <1 ms    <1 ms    <1 ms  192.168.1.1
  2     *        *        *     Request timed out.
  3    12 ms    11 ms    12 ms  8.8.8.8

Trace complete.
"""


# ── Fixtures ──────────────────────────────────────────────────

@pytest.fixture
def collector():
    return TracerouteCollector()


def _mock_run(stdout: str):
    """Return a MagicMock that behaves like subprocess.run()."""
    result = MagicMock()
    result.stdout = stdout
    return result


# ── collect() ─────────────────────────────────────────────────

class TestCollect:
    def test_no_target_returns_empty(self, collector):
        # Act
        result = collector.collect(target=None)

        # Assert
        assert result == {}

    @patch("app.collectors.traceroute.subprocess.run")
    def test_delegates_to_run_traceroute(self, mock_run, collector):
        # Arrange
        mock_run.return_value = _mock_run(LINUX_OUTPUT_COMPLETE)

        # Act
        result = collector.collect(target="8.8.8.8")

        # Assert
        assert result["traceroute_target"] == "8.8.8.8"
        mock_run.assert_called_once()


# ── _run_traceroute() — happy path ───────────────────────────

class TestRunTracerouteHappyPath:
    @patch("app.collectors.traceroute.subprocess.run")
    def test_complete_traceroute_linux(self, mock_run, collector):
        # Arrange
        collector._is_windows = False
        mock_run.return_value = _mock_run(LINUX_OUTPUT_COMPLETE)

        # Act
        result = collector._run_traceroute("8.8.8.8")

        # Assert
        assert result["traceroute_target"] == "8.8.8.8"
        assert result["traceroute_hop_count"] == 3
        assert result["traceroute_complete"] is True

    @patch("app.collectors.traceroute.subprocess.run")
    def test_complete_traceroute_windows(self, mock_run, collector):
        # Arrange
        collector._is_windows = True
        mock_run.return_value = _mock_run(WINDOWS_OUTPUT_COMPLETE)

        # Act
        result = collector._run_traceroute("8.8.8.8")

        # Assert
        assert result["traceroute_target"] == "8.8.8.8"
        assert result["traceroute_hop_count"] == 3
        assert result["traceroute_complete"] is True

    @patch("app.collectors.traceroute.subprocess.run")
    def test_incomplete_traceroute(self, mock_run, collector):
        # Arrange
        collector._is_windows = False
        mock_run.return_value = _mock_run(LINUX_OUTPUT_INCOMPLETE)

        # Act
        result = collector._run_traceroute("8.8.8.8")

        # Assert
        assert result["traceroute_complete"] is False
        assert result["traceroute_hop_count"] == 3

    @patch("app.collectors.traceroute.subprocess.run")
    def test_returns_all_required_keys(self, mock_run, collector):
        # Arrange
        mock_run.return_value = _mock_run(LINUX_OUTPUT_COMPLETE)

        # Act
        result = collector._run_traceroute("8.8.8.8")

        # Assert
        assert set(result.keys()) == {
            "traceroute_target",
            "traceroute_hops",
            "traceroute_hop_count",
            "traceroute_complete",
        }


# ── _run_traceroute() — command building ─────────────────────

class TestCommandBuilding:
    @patch("app.collectors.traceroute.subprocess.run")
    def test_linux_command_flags(self, mock_run, collector):
        # Arrange
        collector._is_windows = False
        mock_run.return_value = _mock_run("")

        # Act
        collector._run_traceroute("1.2.3.4")

        # Assert
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "traceroute"
        assert "-n" in cmd
        assert "1.2.3.4" == cmd[-1]

    @patch("app.collectors.traceroute.subprocess.run")
    def test_windows_command_flags(self, mock_run, collector):
        # Arrange
        collector._is_windows = True
        mock_run.return_value = _mock_run("")

        # Act
        collector._run_traceroute("1.2.3.4")

        # Assert
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "tracert"
        assert "-d" in cmd
        assert "1.2.3.4" == cmd[-1]

    @patch("app.collectors.traceroute.subprocess.run")
    def test_subprocess_timeout_derived_from_settings(self, mock_run, collector):
        # Arrange
        collector._is_windows = False
        collector.max_hops = 10
        collector.timeout = 2
        mock_run.return_value = _mock_run("")

        # Act
        collector._run_traceroute("1.2.3.4")

        # Assert — timeout should be max_hops * timeout + 10
        _, kwargs = mock_run.call_args
        assert kwargs["timeout"] == 10 * 2 + 10


# ── _run_traceroute() — error paths ──────────────────────────

class TestRunTracerouteErrors:
    @patch("app.collectors.traceroute.subprocess.run")
    def test_subprocess_timeout_returns_error(self, mock_run, collector):
        # Arrange
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="tracert", timeout=30)

        # Act
        result = collector._run_traceroute("8.8.8.8")

        # Assert
        assert result["traceroute_target"] == "8.8.8.8"
        assert result["traceroute_hops"] == []
        assert result["traceroute_hop_count"] == 0
        assert result["traceroute_complete"] is False
        assert result["traceroute_error"] == "timeout"

    @patch("app.collectors.traceroute.subprocess.run")
    def test_command_not_found_returns_error(self, mock_run, collector):
        # Arrange
        mock_run.side_effect = FileNotFoundError()

        # Act
        result = collector._run_traceroute("8.8.8.8")

        # Assert
        assert result["traceroute_error"] == "command_not_found"
        assert result["traceroute_hops"] == []
        assert result["traceroute_complete"] is False


# ── _parse_output() ──────────────────────────────────────────

class TestParseOutput:
    def test_empty_output(self, collector):
        # Act
        hops = collector._parse_output("")

        # Assert
        assert hops == []

    def test_parses_linux_hop_with_three_rtts(self, collector):
        # Arrange
        line = " 1  192.168.1.1  1.234 ms  1.100 ms  0.980 ms\n"

        # Act
        hops = collector._parse_output(line)

        # Assert
        assert len(hops) == 1
        hop = hops[0]
        assert hop["hop"] == 1
        assert hop["ip"] == "192.168.1.1"
        assert len(hop["rtts"]) == 3
        assert hop["avg_rtt"] == pytest.approx(1.105, abs=0.01)

    def test_parses_timeout_hop_as_none(self, collector):
        # Arrange
        line = " 2     *        *        *     Request timed out.\n"

        # Act
        hops = collector._parse_output(line)

        # Assert
        assert len(hops) == 1
        hop = hops[0]
        assert hop["hop"] == 2
        assert hop["ip"] is None
        assert hop["rtts"] == []
        assert hop["avg_rtt"] is None

    def test_parses_windows_sub_millisecond_rtt(self, collector):
        # Arrange — Windows shows "<1 ms" for very fast hops
        line = "  1    <1 ms    <1 ms    <1 ms  192.168.1.1\n"

        # Act
        hops = collector._parse_output(line)

        # Assert
        assert len(hops) == 1
        hop = hops[0]
        assert hop["ip"] == "192.168.1.1"
        assert all(rtt == 1.0 for rtt in hop["rtts"])

    def test_skips_header_lines(self, collector):
        # Arrange — typical traceroute header
        output = (
            "traceroute to 8.8.8.8 (8.8.8.8), 30 hops max, 60 byte packets\n"
            " 1  192.168.1.1  1.0 ms  1.0 ms  1.0 ms\n"
        )

        # Act
        hops = collector._parse_output(output)

        # Assert
        assert len(hops) == 1
        assert hops[0]["hop"] == 1

    def test_parses_multiple_hops_in_order(self, collector):
        # Act
        hops = collector._parse_output(LINUX_OUTPUT_COMPLETE)

        # Assert
        assert len(hops) == 3
        assert [h["hop"] for h in hops] == [1, 2, 3]
        assert [h["ip"] for h in hops] == ["192.168.1.1", "10.0.0.1", "8.8.8.8"]

    def test_mixed_timeout_and_resolved_hops(self, collector):
        # Act
        hops = collector._parse_output(LINUX_OUTPUT_INCOMPLETE)

        # Assert
        assert len(hops) == 3
        assert hops[0]["ip"] == "192.168.1.1"
        assert hops[1]["ip"] is None  # timeout hop
        assert hops[1]["avg_rtt"] is None
        assert hops[2]["ip"] == "10.0.0.1"

    def test_windows_full_output_parsed(self, collector):
        # Act
        hops = collector._parse_output(WINDOWS_OUTPUT_COMPLETE)

        # Assert
        assert len(hops) == 3
        assert hops[2]["ip"] == "8.8.8.8"
        assert hops[2]["avg_rtt"] is not None

    def test_avg_rtt_is_rounded(self, collector):
        # Arrange — 3 RTTs that produce a long decimal
        line = " 1  10.0.0.1  1.111 ms  2.222 ms  3.333 ms\n"

        # Act
        hops = collector._parse_output(line)

        # Assert — rounded to 2 decimal places
        assert hops[0]["avg_rtt"] == pytest.approx(2.22, abs=0.01)


# ── Constructor ───────────────────────────────────────────────

class TestConstructor:
    def test_defaults(self, collector):
        assert collector.max_hops == 30
        assert collector.timeout == 5
        assert collector.name == "traceroute"

    def test_is_base_collector(self, collector):
        from app.collectors.base import BaseCollector
        assert isinstance(collector, BaseCollector)
