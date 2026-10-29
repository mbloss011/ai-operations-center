"""FastAPI entrypoint. Run: uvicorn app.main:app --port 8000 (from backend/)."""
import os, json, uuid, pathlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from .db import init_db, Session, Workflow, Run
from .tools.registry import list_tools, get_tool
from .model_registry import MODELS, models_for
from .skills import load_skills
from .mcp import list_mcp_tools
from .engine import run_workflow
from .comfyui import STUDIO, SAVED_WORKFLOWS

app = FastAPI(title="AI Operations Center")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILLS_DIR = os.environ.get("SKILLS_DIR", str(REPO_ROOT / "skills"))
MCP_FILE = os.environ.get("MCP_SERVERS_FILE", str(REPO_ROOT / "mcp_servers.json"))
init_db()

@app.get("/health")
def health():
    return {"ok": True, "tools": len(list_tools()), "models": len(MODELS)}

@app.get("/api/tools")
def tools(category: str = None):
    return list_tools(category)
@app.get("/api/tools/{tool_id}")
def tool(tool_id: str):
    t = get_tool(tool_id)
    return t or {"error": "unknown tool"}
@app.get("/api/models")
def models(modality: str = None):
    return models_for(modality) if modality else MODELS
@app.get("/api/skills")
def skills():
    return load_skills(SKILLS_DIR)
@app.get("/api/comfy")
def comfy():
    return {"studios": STUDIO, "saved_workflows": SAVED_WORKFLOWS}
@app.get("/api/mcp")
def mcp():
    return list_mcp_tools(MCP_FILE)

@app.post("/api/workflows")
def create_workflow(body: dict):
    wid = body.get("id") or str(uuid.uuid4())[:8]
    s = Session(); s.add(Workflow(id=wid, name=body.get("name", wid), graph_json=json.dumps(body.get("graph", {})))); s.commit(); s.close()
    return {"id": wid}
@app.get("/api/workflows/{wid}")
def get_workflow(wid: str):
    s = Session(); w = s.query(Workflow).filter_by(id=wid).first(); s.close()
    return {"id": wid, "graph": json.loads(w.graph_json)} if w else {"error": "not found"}

@app.post("/api/workflows/{wid}/run")
def run(wid: str, body: dict):
    s = Session(); w = s.query(Workflow).filter_by(id=wid).first(); s.close()
    if not w: return {"error": "workflow not found"}
    graph = json.loads(w.graph_json)
    result = run_workflow(graph, run_inputs=body.get("inputs", {}),
                          ctx={"skills_dir": SKILLS_DIR, "mcp_allowlist": body.get("mcp_allowlist", [])})
    rid = str(uuid.uuid4())[:8]
    s = Session(); s.add(Run(id=rid, workflow_id=wid, status="done", outputs_json=json.dumps(result))); s.commit(); s.close()
    return {"run_id": rid, **result}

@app.get("/api/runs/{rid}/stream")
def stream(rid: str):
    # Realtime: the run endpoint already returns events; this SSE route
    # replays a stored run's node events for the live Run panel.
    s = Session(); r = s.query(Run).filter_by(id=rid).first(); s.close()
    data = json.loads(r.outputs_json) if r else {"events": []}
    def gen():
        for ev in data.get("events", []):
            yield f"data: {json.dumps(ev)}\n\n"
        for art in data.get("artifacts", []):
            yield f"data: {json.dumps({'artifact': art})}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")
