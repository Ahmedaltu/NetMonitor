import pytest
from app.analytics.stability import StabilityAnalyzer
from app.analytics.latency_stats import LatencyStats
from app.analytics.scoring import compute_quality_score


class TestStabilityAnalyzer:

    def test_empty_history(self):
        sa = StabilityAnalyzer()
        mean, std = sa.get_metrics()
        assert mean == 0
        assert std == 0

    def test_single_value(self):
        sa = StabilityAnalyzer()
        sa.update(42.0)
        mean, std = sa.get_metrics()
        assert mean == 42.0
        assert std == 0

    def test_multiple_values(self):
        sa = StabilityAnalyzer()
        for v in [10, 20, 30]:
            sa.update(v)
        mean, std = sa.get_metrics()
        assert mean == 20.0
        assert std > 0

    def test_none_ignored(self):
        sa = StabilityAnalyzer()
        sa.update(10)
        sa.update(None)
        sa.update(20)
        mean, _ = sa.get_metrics()
        assert mean == 15.0

    def test_window_overflow(self):
        sa = StabilityAnalyzer(window_size=3)
        for v in [10, 20, 30, 100]:
            sa.update(v)
        # Only last 3 values: 20, 30, 100
        mean, _ = sa.get_metrics()
        assert mean == 50.0

    def test_custom_window(self):
        sa = StabilityAnalyzer(window_size=5)
        assert sa.latency_history.maxlen == 5


# ── LatencyStats ───────────────────────────────────────────────

class TestLatencyStats:

    def test_empty_percentiles(self):
        ls = LatencyStats()
        p = ls.get_percentiles()
        assert p == {"p50": 0.0, "p95": 0.0, "p99": 0.0}

    def test_single_value(self):
        ls = LatencyStats()
        ls.update(42.0)
        p = ls.get_percentiles()
        assert p["p50"] == 42.0
        assert p["p95"] == 42.0
        assert p["p99"] == 42.0

    def test_two_values(self):
        ls = LatencyStats()
        ls.update(10.0)
        ls.update(20.0)
        assert ls.percentile(50) == 15.0  # midpoint

    def test_multiple_values(self):
        ls = LatencyStats()
        for v in range(1, 101):
            ls.update(float(v))
        p = ls.get_percentiles()
        assert abs(p["p50"] - 50.5) < 1.0
        assert p["p95"] > 90
        assert p["p99"] > 95

    def test_none_ignored(self):
        ls = LatencyStats()
        ls.update(10.0)
        ls.update(None)
        ls.update(20.0)
        assert len(ls.history) == 2

    def test_window_overflow(self):
        ls = LatencyStats(window_size=3)
        for v in [10, 20, 30, 40]:
            ls.update(float(v))
        assert len(ls.history) == 3
        # oldest (10) should be evicted
        assert list(ls.history) == [20.0, 30.0, 40.0]

    def test_percentile_boundaries(self):
        ls = LatencyStats()
        for v in [10, 20, 30, 40, 50]:
            ls.update(float(v))
        assert ls.percentile(0) == 10.0
        assert ls.percentile(100) == 50.0


# ── Quality Score ──────────────────────────────────────────────

class TestQualityScore:

    def test_perfect_score(self):
        """Zero latency, zero loss, zero jitter → 100."""
        assert compute_quality_score(0, 0, 0) == 100.0

    def test_no_data(self):
        """All None → 0."""
        assert compute_quality_score(None, None, None) == 0.0

    def test_partial_data(self):
        """Some None values treated as 0 (best)."""
        score = compute_quality_score(0, None, None)
        assert score > 0

    def test_high_latency(self):
        """300ms+ latency → latency component is 0."""
        score = compute_quality_score(300, 0, 0)
        assert score == 60.0  # 40% * 0 + 40% * 100 + 20% * 100

    def test_full_packet_loss(self):
        """10%+ packet loss → loss component is 0."""
        score = compute_quality_score(0, 0.10, 0)
        assert score == 60.0  # 40% * 100 + 40% * 0 + 20% * 100

    def test_high_jitter(self):
        """100ms+ jitter → jitter component is 0."""
        score = compute_quality_score(0, 0, 100)
        assert score == 80.0  # 40% * 100 + 40% * 100 + 20% * 0

    def test_worst_case(self):
        """All at worst → 0."""
        assert compute_quality_score(300, 0.10, 100) == 0.0

    def test_mid_range(self):
        """Mid-range values should produce intermediate score."""
        score = compute_quality_score(150, 0.05, 50)
        assert 0 < score < 100
