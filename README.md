# AI Operations Center — an Opal-style visual workflow builder, self-hosted

Build a custom workflow once: **Input page → nodes → Output pages + artifacts, in realtime.**

Inspired by Google Opal (see `docs/opal-model.md`): describe an app in plain
language, or drag nodes on a canvas. Opal's three node families map directly:

| Opal | AI Operations Center |
|---|---|
| User Input (yellow) | `input` node — text, file, image, video, URL, drawing |
| Generate (blue) | `agent`, `tool`, `browser`, `scraper`, `vision`, `image`, `video`, `skill`, `mcp_tool` nodes |
| Output (green) | `output` node — webpage, markdown, PDF, image, video, file, JSON artifact |
| `@step.output` references | `{{node_id.output}}` templating in prompts and tool inputs |
| Preview / Run / Publish | Run panel with live SSE events + a public `/run/[id]` page per workflow |

## Stack (as requested)

- **Frontend:** Next.js (React) + ReactFlow. Edges are Bezier curves
  (`type: "default"` in @xyflow/react renders a Bezier edge; see
  `apps/web/components/WorkflowCanvas.tsx`).
- **Backend:** Python + FastAPI. Workflows execute as a DAG, topologically,
  left-to-right, no cycles — same rule Opal enforces.
- **Storage:** PostgreSQL for workflows / runs / artifacts metadata.
  Vector store: **Qdrant first** (already live on node-001 at :6333), Chroma
  as the `VECTOR_BACKEND=chroma` alternative. Embeddings via the local
  `text-embedding-nomic-embed-text-v1.5` model through LM Studio.
- **Local models (node-001, see `backend/app/model_registry.py`):**
  Ornith-1.5-9B is the default agent/vision model (113k context, mmproj),
  Ornith-1.5-35B-A3B MoE for heavy work, LFM2-1.2B for routing/tool-use,
  Qwen3.5/3.8 + Muse-Glimmer-30B as alternates, granite-docling-258M for
  document OCR/DOM parsing, ComfyUI (:8188) for image/video/music:
  Flux 2 Turbo/Dev, RealVisXL, Qwen Image 3.8B, Wan 2.2 I2V 14B,
  LTX-2.3 22B, ACE-Step 1.5. LM Studio serves all LLM/vision work at
  `http://127.0.0.1:1234/v1` (OpenAI-compatible) — no cloud model is required.
- **Tools:** every TinyWow tool in the supplied catalog is registered in
  `backend/app/tools/catalog.json` and callable from any agent/tool node
  (`backend/app/tools/registry.py`). PDF, image, video, AI-writing,
  file-conversion and utility families. Real implementations use
  PyMuPDF/Pillow/ffmpeg where installed; LLM-backed writing tools call the
  configured local model; anything needing a missing binary fails loudly
  with the exact dependency instead of silently stubbing output.
- **Skills:** agentskills.io-style skills-as-folders under `skills/*/SKILL.md`
  (same pattern as CADENCE). An agent node can invoke a skill by name;
  skills appear in the tool picker alongside TinyWow tools.
- **MCP:** `backend/app/mcp.py` — configure MCP servers in
  `mcp_servers.json` (stdio / SSE / streamable-HTTP). Discovered MCP tools
  are bridged into workflows as `mcp:<server>:<tool>` nodes, allowlisted
  per workflow. This repo also ships an MCP server entrypoint
  (`backend/app/mcp_server.py`) exposing `list_tools` / `run_workflow`.

## ComfyUI custom endpoints (node-001 :8188)
`backend/app/comfyui.py` is the only client for ComfyUI. Core: POST /prompt,
GET /history, /queue, /interrupt, /free, /object_info (1,229 nodes),
/system_stats, /view, /upload/image, WS /ws. Studio suites, verified live:
character (/studio/dispatch), motion (/motion/build), brand (/brand/build),
voice (/voice/build), music (/music/build) — full route list in
`docs/comfyui-endpoints.md`, plus the 7 saved workflows
(character_0..5, ACE-Step). Workflow nodes: `comfy_prompt` (full graph in
`data.prompt`), `studio_character|motion|brand|voice|music` (payload in
`data.payload`). No media is fabricated when ComfyUI is unreachable.

## Quick start

```bash
cp .env.example .env   # set DATABASE_URL, LMSTUDIO_BASE_URL, COMFYUI_URL
docker compose up -d postgres qdrant   # or use the ones already on node-001
cd backend && pip install -r requirements.txt && uvicorn app.main:app --port 8000
cd apps/web && npm install && npm run dev   # http://localhost:3000
```

Then open the canvas, load `examples/youtube-summarizer.json`, hit Run,
and watch node outputs + artifacts stream into the right-hand panel.

## Layout

```
apps/web/        Next.js + ReactFlow editor, run page, artifact viewer
backend/app/     FastAPI: engine.py (DAG runner), tools/, model_registry.py,
                 vectorstore.py, skills.py, mcp.py, browser.py, db.py
skills/          skills-as-folders (SKILL.md + scripts/)
examples/        Importable workflows (Opal-style: input -> generate -> output)
docs/            opal-model.md, tools.md, models.md, mcp-and-skills.md
```

## Safety notes

- Browser/scraper nodes fetch only URLs the workflow author or end-user
  supplies. No unauthenticated scanning, no credential harvesting.
- Tool nodes that shell out (ffmpeg, etc.) run with an explicit allowlist
  of binaries and a timeout; file paths are confined to the run's workdir.
- This is v0.1 scaffolding: the DAG engine, registries, skill/MCP bridging
  and the editor are real and tested (see `backend/tests/`); individual
  TinyWow conversions that need a missing system binary report that
  dependency instead of inventing a result.
