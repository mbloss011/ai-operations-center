"use client";
import { useCallback, useState } from "react";
import { ReactFlow, Background, Controls, MiniMap, addEdge, type Node, type Edge, type Connection } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

// Node colours mirror Opal: input yellow, generate blue, output green.
const PALETTE = [
  { type: "input", label: "Input", color: "#e8c547" },
  { type: "agent", label: "Agent (local LLM)", color: "#5b9bd5" },
  { type: "vision", label: "Vision", color: "#5b9bd5" },
  { type: "tool", label: "Tool (TinyWow)", color: "#5b9bd5" },
  { type: "browser", label: "Browser / Scraper", color: "#5b9bd5" },
  { type: "skill", label: "Skill (agentskills.io)", color: "#7aa5ff" },
  { type: "mcp_tool", label: "MCP Tool", color: "#7aa5ff" },
  { type: "image", label: "Image (ComfyUI)", color: "#5b9bd5" },
  { type: "comfy_prompt", label: "ComfyUI prompt graph", color: "#5b9bd5" },
  { type: "studio_character", label: "Studio: Character", color: "#b48ae0" },
  { type: "studio_motion", label: "Studio: Motion", color: "#b48ae0" },
  { type: "studio_brand", label: "Studio: Brand", color: "#b48ae0" },
  { type: "studio_voice", label: "Studio: Voice / TTS", color: "#b48ae0" },
  { type: "studio_music", label: "Studio: Music (ACE-Step)", color: "#b48ae0" },
  { type: "video", label: "Video (ComfyUI)", color: "#5b9bd5" },
  { type: "output", label: "Output / Artifact", color: "#6fbf73" },
];
const initialNodes: Node[] = [
  { id: "url_input", type: "input", position: { x: 0, y: 100 }, data: { label: "Video / page URL" } },
  { id: "summarize", type: "agent", position: { x: 300, y: 100 }, data: { label: "Summarize — {{url_input.output}}" } },
  { id: "page", type: "output", position: { x: 600, y: 100 }, data: { label: "Summary page" } },
];
const initialEdges: Edge[] = [
  // type "default" in @xyflow/react renders a Bezier edge.
  { id: "e1", source: "url_input", target: "summarize", type: "default" },
  { id: "e2", source: "summarize", target: "page", type: "default" },
];
export default function WorkflowCanvas() {
  const [nodes, setNodes] = useState<Node[]>(initialNodes);
  const [edges, setEdges] = useState<Edge[]>(initialEdges);
  const [log, setLog] = useState<string>("Drag nodes from the palette. Edges are Bezier curves. Hit Run to stream node outputs + artifacts here.");
  const onConnect = useCallback((c: Connection) => setEdges((e) => addEdge({ ...c, type: "default" }, e)), []);
  const addNode = (type: string) => {
    const id = `${type}_${nodes.length + 1}`;
    setNodes((n) => [...n, { id, type, position: { x: 100 + n.length * 40, y: 250 }, data: { label: type } }]);
  };
  return (<div style={{ display: "flex", flex: 1, minHeight: 0 }}>
    <aside style={{ width: 220, padding: 12, borderRight: "1px solid #1c3442" }}>
      <h3>Palette</h3>
      {PALETTE.map((p) => (<button key={p.type} onClick={() => addNode(p.type)} style={{ display: "block", width: "100%", marginBottom: 6, padding: 8, background: "#0c1b26", color: "#e6f0f5", border: `1px solid ${p.color}`, borderRadius: 6, cursor: "pointer", textAlign: "left" }}>{p.label}</button>))}
      <p style={{ color: "#8fb3c2", fontSize: 13 }}>Reference upstream outputs as {"{{node_id.output}}"} — Opal&apos;s @step.output.</p>
    </aside>
    <div style={{ flex: 1, background: "#08131a" }}>
      <ReactFlow nodes={nodes} edges={edges} onNodesChange={() => {}} onEdgesChange={() => {}} onConnect={onConnect} fitView>
        <Background /><Controls /><MiniMap />
      </ReactFlow>
    </div>
    <aside style={{ width: 320, padding: 12, borderLeft: "1px solid #1c3442", overflow: "auto" }}>
      <h3>Run / Artifacts (realtime)</h3>
      <button onClick={() => setLog("Run requires a saved workflow id — POST /api/workflows, then /api/workflows/{id}/run, then stream /api/runs/{run_id}/stream (SSE).")} style={{ padding: "8px 14px", cursor: "pointer" }}>Run</button>
      <pre style={{ whiteSpace: "pre-wrap", fontSize: 13 }}>{log}</pre>
    </aside>
  </div>);
}
