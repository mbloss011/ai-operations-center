"""DAG workflow engine — Opal semantics, local execution.

Graph: {"nodes": [{"id", "type", "data": {...}}], "edges": [{"source", "target", "sourceHandle", "targetHandle"}]}
Node types: input, agent, tool, browser, scraper, vision, image, video,
skill, mcp_tool, output.
Rules (from Opal): build left-to-right, no cycles, a node may reference
an upstream node's output as {{node_id.output}} or {{node_id}} in prompts
and tool inputs. Execution is topological; each node emits an output
dict stored on the run, streamed as SSE events by main.py.

Agent nodes call LM Studio's OpenAI-compatible API with the selected
local model (default ornith-1.5-9b). Tool nodes may call TinyWow tools
(non-LLM ones locally, LLM ones via the same agent call) or a skill /
MCP tool when allowlisted. Vision nodes send image_url content parts.
Image/video nodes route to ComfyUI workflows when COMFYUI_URL is set;
without a configured workflow they return a clear 'not configured'
error rather than a fake file.
"""
import os, re, json, httpx
from .tools.registry import run_local_tool, get_tool
from .browser import scrape_url, redirect_chain
from .skills import load_skills
from .model_registry import get_model
from .comfyui import ComfyClient, STUDIO, SAVED_WORKFLOWS

class CycleError(ValueError):
    pass

def topo_sort(nodes, edges):
    ids = [n["id"] for n in nodes]
    indeg = {i: 0 for i in ids}; adj = {i: [] for i in ids}
    for e in edges:
        if e["source"] in adj and e["target"] in indeg:
            adj[e["source"]].append(e["target"]); indeg[e["target"]] += 1
    queue = [i for i in ids if indeg[i] == 0]; out = []
    while queue:
        n = queue.pop(0); out.append(n)
        for m in adj[n]:
            indeg[m] -= 1
            if indeg[m] == 0: queue.append(m)
    if len(out) != len(ids):
        raise CycleError("workflow has a cycle — Opal-style graphs must be acyclic")
    return out

def render_template(text, outputs):
    if not isinstance(text, str):
        return text
    def repl(m):
        key = m.group(1).strip()
        node_id = key.split(".")[0]
        val = outputs.get(node_id, {})
        if isinstance(val, dict):
            return str(val.get("output", val.get("text", json.dumps(val))))
        return str(val)
    return re.sub(r"\{\{\s*([^}]+)\s*\}\}", repl, text)

def call_lmstudio(prompt, model="ornith-1.5-9b", system=None, image_url=None):
    base = os.environ.get("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1").rstrip("/")
    content = [{"type": "text", "text": prompt}]
    if image_url:
        content.append({"type": "image_url", "image_url": {"url": image_url}})
    msgs = []
    if system: msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": content})
    with httpx.Client(timeout=300) as c:
        r = c.post(f"{base}/chat/completions", json={"model": model, "messages": msgs})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

def execute_node(node, inputs, outputs, ctx):
    ntype = node["type"]; data = node.get("data", {})
    if ntype == "input":
        return {"output": data.get("value", data.get("default", ""))}
    if ntype == "agent":
        prompt = render_template(data.get("prompt", ""), outputs)
        skill = data.get("skill")
        if skill:
            skills = {s["name"]: s for s in load_skills(ctx.get("skills_dir", "./skills"))}
            if skill not in skills:
                raise ValueError(f"unknown skill: {skill}")
            prompt = skills[skill]["instructions"] + "\n\n" + prompt
        model = data.get("model", "ornith-1.5-9b")
        if get_model(model) is None:
            raise ValueError(f"unknown local model: {model} (see model_registry.py)")
        return {"output": call_lmstudio(prompt, model=model, system=data.get("system"))}
    if ntype == "vision":
        prompt = render_template(data.get("prompt", "Describe this image."), outputs)
        return {"output": call_lmstudio(prompt, model=data.get("model", "ornith-1.5-9b"), image_url=data.get("image_url") or inputs.get("image_url", ""))}
    if ntype == "tool":
        tool_id = data.get("tool")
        tool = get_tool(tool_id) if tool_id else None
        if tool is None:
            raise ValueError(f"unknown tool: {tool_id}")
        payload = {k: render_template(v, outputs) if isinstance(v, str) else v for k, v in data.get("inputs", {}).items()}
        if tool["kind"] == "llm":
            prompt = payload.get("text", payload.get("prompt", "")) or render_template(data.get("prompt", ""), outputs)
            return {"output": call_lmstudio(prompt, model=data.get("model", "ornith-1.5-9b"))}
        return run_local_tool(tool_id, payload)
    if ntype in ("browser", "scraper"):
        url = render_template(data.get("url", ""), outputs) or inputs.get("url", "")
        if data.get("mode") == "redirects":
            return redirect_chain(url)
        return scrape_url(url)
    if ntype in ("image", "video", "comfy_prompt"):
        # data.prompt = full ComfyUI workflow graph; data.comfy_workflow = saved workflow name.
        client = ComfyClient()
        if data.get("prompt"):
            return client.run_prompt(data["prompt"], timeout=int(data.get("timeout", 600)))
        if data.get("comfy_workflow"):
            name = data["comfy_workflow"]
            if name not in SAVED_WORKFLOWS:
                raise ValueError(f"unknown saved ComfyUI workflow: {name} (see comfyui.SAVED_WORKFLOWS)")
            raise RuntimeError(f"Saved workflow {name} ({SAVED_WORKFLOWS[name]}) must be supplied as data.prompt graph JSON — ComfyUI has no by-name queue endpoint; the saved file lives in user/default/workflows on node-001.")
        raise RuntimeError("image/video/comfy_prompt node needs data.prompt (ComfyUI workflow graph) — no file is fabricated without ComfyUI.")
    if ntype.startswith("studio_"):
        suite = ntype[len("studio_"):]
        if suite not in STUDIO:
            raise ValueError(f"unknown studio suite: {suite}")
        payload = data.get("payload", {}) or {}
        for k, v in data.items():
            if k not in ("payload", "label"):
                payload.setdefault(k, v)
        return ComfyClient().studio_build(suite, payload)
    if ntype == "skill":
        skills = {s["name"]: s for s in load_skills(ctx.get("skills_dir", "./skills"))}
        name = data.get("skill")
        if name not in skills:
            raise ValueError(f"unknown skill: {name}")
        prompt = skills[name]["instructions"] + "\n\n" + render_template(data.get("prompt", ""), outputs)
        return {"output": call_lmstudio(prompt, model=data.get("model", "ornith-1.5-9b"))}
    if ntype == "mcp_tool":
        allowed = ctx.get("mcp_allowlist", [])
        tool_id = data.get("tool", "")
        if allowed and tool_id not in allowed:
            raise ValueError(f"MCP tool not allowlisted for this workflow: {tool_id}")
        raise RuntimeError(f"MCP tool {tool_id} requires a live MCP session — configure mcp_servers.json and the mcp SDK; see mcp.py.")
    if ntype == "output":
        rendered = render_template(data.get("template", data.get("value", "")), outputs)
        artifact = {"kind": data.get("kind", "webpage"), "content": rendered, "title": data.get("title", node["id"])}
        ctx.setdefault("artifacts", []).append(artifact)
        return {"output": rendered, "artifact": artifact}
    raise ValueError(f"unknown node type: {ntype}")

def run_workflow(graph, run_inputs=None, ctx=None):
    ctx = ctx or {}
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    order = topo_sort(graph.get("nodes", []), graph.get("edges", []))
    outputs = {}
    # Seed input nodes with run-time values
    for nid, val in (run_inputs or {}).items():
        if nid in nodes and nodes[nid]["type"] == "input":
            nodes[nid] = {**nodes[nid], "data": {**nodes[nid].get("data", {}), "value": val}}
    events = []
    for nid in order:
        node = nodes[nid]
        # upstream outputs are available via `outputs` for templating
        result = execute_node(node, {}, outputs, ctx)
        outputs[nid] = result
        events.append({"node": nid, "type": node["type"], "output": result})
    return {"outputs": outputs, "events": events, "artifacts": ctx.get("artifacts", [])}
