# Composite network quality score (0-100)


def compute_quality_score(
    latency: float | None,
    packet_loss: float | None,
    jitter: float | None,
) -> float:
    """
    Compute a 0-100 network quality score.

    Weights:
      - Latency  : 40%  (0ms = 100, >=300ms = 0)
      - Packet loss: 40%  (0% = 100, >=10% = 0)
      - Jitter   : 20%  (0ms = 100, >=100ms = 0)

    Returns 0.0 when no data is available.
    """
    if latency is None and packet_loss is None and jitter is None:
        return 0.0

    def _clamp_score(value: float, best: float, worst: float) -> float:
        if value <= best:
            return 100.0
        if value >= worst:
            return 0.0
        return 100.0 * (1.0 - (value - best) / (worst - best))

    lat_score = _clamp_score(latency or 0, 0, 300)
    # packet_loss comes as 0-1 ratio; convert to percent
    loss_score = _clamp_score((packet_loss or 0) * 100, 0, 10)
    jit_score = _clamp_score(jitter or 0, 0, 100)

    score = 0.4 * lat_score + 0.4 * loss_score + 0.2 * jit_score
    return round(score, 1)
