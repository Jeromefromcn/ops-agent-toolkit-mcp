import httpx

from audit import audited
from settings import CONSUL_URL, HTTP_TIMEOUT_SECONDS


@audited
async def get_service_health(service: str) -> dict:
    """Check a service's registration and health-check status in Consul."""
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        resp = await client.get(f"{CONSUL_URL}/v1/health/service/{service}")
        resp.raise_for_status()
        entries = resp.json()

    if not entries:
        return {"service": service, "registered": False, "instance_count": 0}

    instances = []
    for entry in entries:
        checks = entry.get("Checks", [])
        statuses = {check.get("Status") for check in checks}
        overall = (
            "passing"
            if statuses == {"passing"}
            else ("critical" if "critical" in statuses else "warning")
        )
        instances.append(
            {
                "node": entry.get("Node", {}).get("Node"),
                "address": entry.get("Service", {}).get("Address"),
                "port": entry.get("Service", {}).get("Port"),
                "status": overall,
                "checks": [
                    {"name": c.get("Name"), "status": c.get("Status")} for c in checks
                ],
            }
        )

    return {
        "service": service,
        "registered": True,
        "instance_count": len(instances),
        "healthy_instance_count": sum(1 for i in instances if i["status"] == "passing"),
        "instances": instances,
    }
