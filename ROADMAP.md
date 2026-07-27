# ops-agent-toolkit-mcp — Roadmap

MCP server exposing read-only ops tools to an agent troubleshooting the [`lab-environment`](https://github.com/Jeromefromcn/lab-environment) sandbox. This roadmap tracks the tool set's own version history, independent of the sandbox's phase plan (see `lab-environment/ROADMAP.md` for the full project context).

## v0.1 — Core read-only tools

- `search_logs(service, keyword, minutes_ago)` → Loki
- `query_metric(service, metric_name, minutes_ago)` → Prometheus, returns summary stats (mean/peak/threshold), not raw series
- `get_trace(trace_id)` / `search_traces(service, error_only, minutes_ago)` → Jaeger, formatted as a span tree with per-hop duration
- `get_service_health(service)` → Consul
- `get_service_config(service)` → Consul KV

Ships with the `@audited` decorator on every tool call (tool name, args, duration, result preview).

## v0.2 — Chaos control surface

- `toggle_chaos_scenario(service, scenario, enabled)` — writes to Consul KV
- `get_active_chaos_scenario()` — reads current active scenario + its ground truth, for eval scripting

Needed by `lab-environment` Phase 3 (batch evaluation) — scripts must be able to inject and clear faults programmatically.

Note: this is the one write-capable tool in the set. It writes only to chaos toggle keys, never to real app config. Keep it namespaced to `config/<service>/data/chaos.*`.

## v0.3 — Kafka support

- `get_consumer_lag(group)`
- `get_topic_info(topic)`

Depends on `lab-environment` Phase 4 (Kafka + async event chain).

## v0.4 — Multi-agent support

- Split tools into permission groups (e.g. `logs+metrics` vs `config+chaos-control`) so different agent roles in a multi-agent setup (planner / log-agent / metrics-agent / on-call-lead) can be scoped to only what they need
- Depends on `lab-environment` Phase 5 (multi-agent orchestration)

## Backlog / not scheduled

- `kubectl_describe(resource)` / `get_pod_logs(pod)` / `get_pod_events(pod)` — depends on the K8s follow-up in `lab-environment/ROADMAP.md`
- Trino/offline-data tools — depends on the offline-data follow-up in `lab-environment/ROADMAP.md`

## Design principles (do not violate without discussion)

- Read-only, with one deliberate exception: chaos toggles (v0.2). No tool restarts services, rolls back deployments, or writes real app config.
- One tool, one responsibility — don't let a tool quietly do more than its name says.
- Never expose a raw query language (PromQL/LogQL) directly to the model — always wrap in parameterized functions.
- Tool outputs are summarized/formatted for the model, never raw JSON dumps.
- Every call goes through `@audited` — no exceptions.
