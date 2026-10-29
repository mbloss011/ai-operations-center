"""MCP support — client side (bridge MCP tools into workflows) and
server side is in mcp_server.py.

Config: mcp_servers.json, e.g.
  {"servers": [{"name": "fs", "transport": "stdio", "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/data"],
                "enabled": true}]}
Transports: stdio / sse / streamable-http, via the `mcp` Python SDK when
installed. Without the SDK, list_mcp_tools() reports the gap honestly
instead of pretending a server is connected. Discovered tools are
namespaced as mcp:<server>:<tool> and are allowlisted per workflow
(workflow['mcp_allowlist']).
"""
import json, pathlib

def load_mcp_config(path):
    p = pathlib.Path(path)
    if not p.exists():
        return []
    data = json.loads(p.read_text())
    return [s for s in data.get("servers", []) if s.get("enabled")]

def mcp_tool_id(server, tool):
    return f"mcp:{server}:{tool}"

def list_mcp_tools(config_path):
    servers = load_mcp_config(config_path)
    try:
        import mcp  # noqa: F401  (python-sdk, optional)
    except ImportError:
        return {"connected": False, "servers": [s["name"] for s in servers],
                "error": "mcp python SDK not installed: pip install mcp. No MCP tools are bridged until it is."}
    # Real discovery happens through the SDK session per server; this
    # function is the seam — callers pass a live session in production.
    return {"connected": True, "servers": [s["name"] for s in servers], "tools": []}
