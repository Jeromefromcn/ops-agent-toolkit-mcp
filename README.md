# ops-agent-toolkit-mcp

MCP server exposing read-only ops tools to an agent troubleshooting the [`lab-environment`](https://github.com/Jeromefromcn/lab-environment) sandbox.

## Tools

| Tool | Backend | Purpose |
|---|---|---|
| `search_logs(service, keyword, minutes_ago)` | Loki | Search service logs by keyword and time window |
| `query_metric(service, metric_name, minutes_ago)` | Prometheus | Get a metric's summary (mean/peak/threshold), not raw series |
| `get_trace(trace_id)` / `search_traces(service, error_only)` | Jaeger | Fetch or search distributed traces, formatted as a span tree |
| `get_service_health(service)` | Consul | Check service registration/health status |
| `get_service_config(service)` | Consul KV | Read a service's current config |
| `toggle_chaos_scenario(service, scenario, enabled)` | Consul KV | Enable/disable a fault scenario |

See [`ROADMAP.md`](./ROADMAP.md) for planned additions (Kafka tools, multi-agent permission scoping, K8s tools).

## Run locally (stdio mode)

```bash
pip install -r requirements.txt
python server.py
```

## Run as a container (HTTP/SSE mode)

```bash
docker build -t ops-lab/mcp-toolkit:dev .
```

Intended to run inside the `lab-environment` docker-compose network, so it can reach Loki/Prometheus/Jaeger/Consul by service name.

## Design principles

- **Read-only by default.** The one exception is `toggle_chaos_scenario`, scoped to chaos toggle keys only. No tool restarts services, rolls back deployments, or writes real app config. Further write-capable tools require explicit discussion.
- **Parameterized, not raw passthrough.** Never expose PromQL/LogQL directly to the model.
- **Every call is audited** — tool name, args, duration, and a result preview are logged.
- **One tool, one job.** Keep tool boundaries narrow so the agent composes them itself.

## Roadmap

See [`ROADMAP.md`](./ROADMAP.md).
