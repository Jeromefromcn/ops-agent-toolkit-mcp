import os

from mcp.server.fastmcp import FastMCP

from tools.chaos import get_active_chaos_scenario, toggle_chaos_scenario
from tools.config import get_service_config
from tools.discovery import get_service_health
from tools.logs import search_logs
from tools.metrics import query_metric
from tools.tracing import get_trace, search_traces

# stdio for `python server.py` locally; the container CMD sets
# MCP_TRANSPORT=streamable-http so Claude Code can connect over the
# lab-environment docker network (see ROADMAP.md / Dockerfile).
mcp = FastMCP(
    "ops-agent-toolkit",
    host=os.environ.get("MCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("MCP_PORT", "8765")),
)

for tool in (
    search_logs,
    query_metric,
    get_trace,
    search_traces,
    get_service_health,
    get_service_config,
    toggle_chaos_scenario,
    get_active_chaos_scenario,
):
    mcp.add_tool(tool)

if __name__ == "__main__":
    mcp.run(transport=os.environ.get("MCP_TRANSPORT", "stdio"))
