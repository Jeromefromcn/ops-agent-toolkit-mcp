# CLAUDE.md

Keep any additions to this file short and direct.

## Project

MCP server exposing read-only ops tools (logs, metrics, traces, service discovery/config) to an agent troubleshooting the sandbox in `lab-environment`.

## Cross-repo contract

This repo, `lab-environment`, and `spring-petclinic-microservices` don't share Claude Code session context — a session working here has no memory of what the other two assume. Before touching Consul KV paths, DB names, service names, or chaos toggle names, read `lab-environment/CLAUDE.md`'s "Cross-repo contract" table — that file is the single source of truth, not this one.

## Key commands

- `python server.py` — run locally in stdio mode
- `docker build -t ops-lab/mcp-toolkit:dev .` — build the container image (HTTP/SSE mode, joins the `lab-environment` compose network)

## Conventions

- One tool = one responsibility. A tool must not silently do more than its name implies.
- Never expose a raw query language (PromQL, LogQL) directly to the model — wrap it in a parameterized function.
- Every tool call goes through the `@audited` decorator. No exceptions.
- Tool outputs are summarized/formatted for the model, not raw JSON dumps.
- Read-only, except `toggle_chaos_scenario` (scoped to `config/<service>/data/chaos.*` keys only). No tool restarts services, rolls back deployments, or writes real app config. Do not add further write-capable tools without discussing first.

## Roadmap

See `ROADMAP.md` for planned tool additions by phase.
