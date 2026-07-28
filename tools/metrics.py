import time

import httpx

from audit import audited
from settings import HTTP_TIMEOUT_SECONDS, PROMETHEUS_URL


@audited
async def query_metric(
    service: str,
    metric_name: str,
    minutes_ago: int = 15,
    threshold: float | None = None,
) -> dict:
    """Summarize a metric for a service over the last N minutes: mean, peak,
    and (if a threshold is given) whether it was exceeded. Never returns
    the raw time series."""
    now = time.time()
    start = now - minutes_ago * 60
    # Prometheus scrapes instances as "<service>:<port>" (see
    # lab-environment/observability/prometheus/prometheus.yml).
    query = f'{metric_name}{{instance=~"^{service}:.*"}}'
    params = {"query": query, "start": start, "end": now, "step": "15s"}

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        resp = await client.get(f"{PROMETHEUS_URL}/api/v1/query_range", params=params)
        resp.raise_for_status()
        payload = resp.json()

    values: list[float] = []
    for series in payload.get("data", {}).get("result", []):
        for _, value in series.get("values", []):
            values.append(float(value))

    if not values:
        return {
            "service": service,
            "metric": metric_name,
            "window_minutes": minutes_ago,
            "sample_count": 0,
            "note": "no data points in this window",
        }

    mean = sum(values) / len(values)
    peak = max(values)
    result = {
        "service": service,
        "metric": metric_name,
        "window_minutes": minutes_ago,
        "sample_count": len(values),
        "mean": round(mean, 4),
        "peak": round(peak, 4),
    }
    if threshold is not None:
        result["threshold"] = threshold
        result["threshold_exceeded"] = peak > threshold
    return result
