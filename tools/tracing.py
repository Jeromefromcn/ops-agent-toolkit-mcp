import time

import httpx

from audit import audited
from settings import HTTP_TIMEOUT_SECONDS, JAEGER_URL


@audited
async def get_trace(trace_id: str) -> dict:
    """Fetch one trace by ID, formatted as a span tree with per-hop duration."""
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        resp = await client.get(f"{JAEGER_URL}/api/traces/{trace_id}")
        resp.raise_for_status()
        payload = resp.json()

    traces = payload.get("data", [])
    if not traces:
        return {"trace_id": trace_id, "found": False}
    return {"trace_id": trace_id, "found": True, "root_spans": _span_tree(traces[0])}


@audited
async def search_traces(
    service: str, error_only: bool = False, minutes_ago: int = 15, limit: int = 20
) -> dict:
    """Search recent traces for a service, formatted as span trees."""
    now_us = int(time.time() * 1_000_000)
    start_us = now_us - minutes_ago * 60 * 1_000_000

    params = {"service": service, "start": start_us, "end": now_us, "limit": limit}
    if error_only:
        params["tags"] = '{"error":"true"}'

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        resp = await client.get(f"{JAEGER_URL}/api/traces", params=params)
        resp.raise_for_status()
        payload = resp.json()

    traces = payload.get("data", [])
    return {
        "service": service,
        "window_minutes": minutes_ago,
        "error_only": error_only,
        "trace_count": len(traces),
        "traces": [
            {"trace_id": t["traceID"], "root_spans": _span_tree(t)} for t in traces
        ],
    }


def _span_tree(trace: dict) -> list[dict]:
    processes = trace.get("processes", {})
    spans_by_id = {s["spanID"]: s for s in trace.get("spans", [])}
    children: dict[str | None, list[str]] = {}

    for span in trace.get("spans", []):
        parent_id = None
        for ref in span.get("references", []):
            if ref.get("refType") == "CHILD_OF":
                parent_id = ref.get("spanID")
                break
        children.setdefault(parent_id, []).append(span["spanID"])

    def build(span_id: str) -> dict:
        span = spans_by_id[span_id]
        process_id = span.get("processID")
        service_name = processes.get(process_id, {}).get("serviceName", "unknown")
        has_error = any(
            tag.get("key") == "error" and tag.get("value") is True
            for tag in span.get("tags", [])
        )
        return {
            "operation": span.get("operationName"),
            "service": service_name,
            "duration_ms": round(span.get("duration", 0) / 1000, 2),
            "error": has_error,
            "children": [build(child_id) for child_id in children.get(span_id, [])],
        }

    return [build(span_id) for span_id in children.get(None, [])]
