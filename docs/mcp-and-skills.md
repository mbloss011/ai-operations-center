# Skills + MCP

## Skills (agentskills.io pattern)
- Folder per skill: `skills/<name>/SKILL.md` with YAML frontmatter
  (`name`, `description`) + markdown instructions, optional `scripts/`.
- Same shape as CADENCE skills-as-folders. Agent and skill nodes load
  them via `backend/app/skills.py`. Add a skill by adding a folder —
  no code change, no restart needed for the API's /api/skills reload
  path (restart the backend in v0.1 to pick up new folders).
- Included: `web-research`, `document-summarizer`.

## MCP
- Client: `mcp_servers.json` lists servers (stdio / SSE / streamable-HTTP).
  Enabled servers' tools appear as `mcp:<server>:<tool>` in the picker,
  subject to the workflow's `mcp_allowlist`.
- Server: `backend/app/mcp_server.py` exposes AIOC itself over MCP
  (list_tools / list_models / list_skills / run_aioc_workflow) so other
  agents (Claude, CADENCE, LM Studio Bionic-style hosts) can call it.
- Requires the `mcp` Python SDK for live sessions; without it the API
  reports the gap instead of faking a connection.
