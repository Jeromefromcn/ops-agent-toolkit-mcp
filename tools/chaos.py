import base64

import httpx

from audit import audited
from settings import CONSUL_URL, HTTP_TIMEOUT_SECONDS


class InvalidChaosScenarioName(ValueError):
    pass


@audited
async def toggle_chaos_scenario(service: str, scenario: str, enabled: bool) -> dict:
    """Enable or disable a fault-injection scenario for testing. The only
    write-capable tool in this server; never writes real app config."""
    # Scoped to the top-level chaos/<service>/<scenario> Consul KV prefix,
    # kept separate from config/ so a toggle write never triggers Spring
    # Cloud Consul Config's watch/refresh (see lab-environment/CLAUDE.md's
    # cross-repo contract).
    if not scenario or "/" in scenario:
        raise InvalidChaosScenarioName(
            f"scenario must be a bare toggle name with no '/', got: {scenario!r}"
        )

    key = f"chaos/{service}/{scenario}"
    value = "true" if enabled else "false"

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        resp = await client.put(f"{CONSUL_URL}/v1/kv/{key}", content=value)
        resp.raise_for_status()

    return {"service": service, "scenario": scenario, "enabled": enabled}


@audited
async def get_active_chaos_scenario() -> dict:
    """List every chaos scenario currently enabled, across all services.
    Reports live Consul state only, not the catalog of available scenario
    types."""
    # chaos/<service>/<name> toggles; the scenario catalog itself lives in
    # lab-environment/scenarios/scenarios.yaml, which this tool never reads.
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        resp = await client.get(f"{CONSUL_URL}/v1/kv/chaos/", params={"recurse": "true"})

    if resp.status_code == 404:
        return {"active_scenarios": []}
    resp.raise_for_status()

    active = []
    for entry in resp.json():
        key = entry["Key"]
        parts = key.split("/")
        # chaos/<service>/<name>
        if len(parts) != 3:
            continue
        if entry.get("Value") is None:
            continue
        value = base64.b64decode(entry["Value"]).decode("utf-8")
        if value.strip().lower() == "true":
            active.append({"service": parts[1], "scenario": parts[2]})

    return {"active_scenarios": active}
