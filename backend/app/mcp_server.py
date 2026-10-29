"""Expose AI Operations Center itself as an MCP server (optional).

Requires `mcp` SDK (FastMCP). Tools exposed:
  - list_tools / list_models / list_skills (registries)
  - run_workflow(graph_json) — runs a DAG via engine.run_workflow
Run: python -m app.mcp_server   (stdio transport)
"""
def main():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as e:
        raise SystemExit("pip install mcp to run the MCP server") from e
    import json
    from .tools.registry import list_tools
    from .model_registry import MODELS
    from .skills import load_skills
    from .engine import run_workflow
    import os
    mcp = FastMCP("ai-operations-center")
    @mcp.tool()
    def list_aioc_tools(category: str = ""):
        return list_tools(category or None)
    @mcp.tool()
    def list_aioc_models():
        return MODELS
    @mcp.tool()
    def list_aioc_skills():
        return load_skills(os.environ.get("SKILLS_DIR", "./skills"))
    @mcp.tool()
    def run_aioc_workflow(graph_json: str):
        return run_workflow(json.loads(graph_json))
    mcp.run()
if __name__ == "__main__":
    main()
