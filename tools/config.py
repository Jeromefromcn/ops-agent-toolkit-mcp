import base64

import httpx

from audit import audited
from settings import CONSUL_URL, HTTP_TIMEOUT_SECONDS


@audited
async def get_service_config(service: str) -> dict:
    """Read a service's current config from Consul KV
    (config/<service>/data/*, including chaos.* toggles)."""
    prefix = f"config/{service}/data/"
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        resp = await client.get(
            f"{CONSUL_URL}/v1/kv/{prefix}", params={"recurse": "true"}
        )

    if resp.status_code == 404:
        return {"service": service, "found": False, "config": {}}
    resp.raise_for_status()

    config = {}
    for entry in resp.json():
        key = entry["Key"][len(prefix):]
        if not key or entry.get("Value") is None:
            continue
        config[key] = base64.b64decode(entry["Value"]).decode("utf-8")

    return {"service": service, "found": True, "config": config}
