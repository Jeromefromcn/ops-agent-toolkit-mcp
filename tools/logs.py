import time

import httpx

from audit import audited
from settings import HTTP_TIMEOUT_SECONDS, LOKI_URL


@audited
async def search_logs(service: str, keyword: str, minutes_ago: int = 15) -> dict:
    """Search a service's logs for a keyword within the last N minutes.

    Backed by Loki. Logs are labeled `service="<container name>"` by
    promtail's docker service discovery (see lab-environment/observability).
    """
    now_ns = time.time_ns()
    start_ns = now_ns - minutes_ago * 60 * 1_000_000_000

    query = f'{{service="{service}"}} |= "{keyword}"'
    params = {"query": query, "start": start_ns, "end": now_ns, "limit": 100}

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        resp = await client.get(f"{LOKI_URL}/loki/api/v1/query_range", params=params)
        resp.raise_for_status()
        payload = resp.json()

    lines = []
    for stream in payload.get("data", {}).get("result", []):
        for ts_ns, line in stream.get("values", []):
            lines.append({"timestamp": _ns_to_iso(int(ts_ns)), "line": line})
    lines.sort(key=lambda entry: entry["timestamp"])

    return {
        "service": service,
        "keyword": keyword,
        "window_minutes": minutes_ago,
        "match_count": len(lines),
        "lines": lines,
    }


def _ns_to_iso(ts_ns: int) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts_ns / 1_000_000_000))
