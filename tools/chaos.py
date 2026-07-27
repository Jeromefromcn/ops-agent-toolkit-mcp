import base64

import httpx

from audit import audited
from settings import CONSUL_URL, HTTP_TIMEOUT_SECONDS


class InvalidChaosScenarioName(ValueError):
    pass


@audited
async def toggle_chaos_scenario(service: str, scenario: str, enabled: bool) -> dict:
    """Enable/disable a fault scenario. The ONLY write-capable tool in this
    server — strictly scoped to chaos/<service>/<scenario>, a top-level
    Consul KV prefix kept separate from config/ so a toggle write never
    triggers Spring Cloud Consul Config's watch/refresh (see
    lab-environment/CLAUDE.md's cross-repo contract). Never writes real app
    config. See CLAUDE.md design principles.
    """
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
    """List every chaos/<service>/<name> toggle currently set to true, across
    all services.

    Ground-truth lookup for a given scenario name lives in
    lab-environment/scenarios/scenarios.yaml — this tool only reports what's
    live in Consul KV, it does not know about that file.
    """
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
