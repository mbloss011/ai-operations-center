const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export async function api(path: string, opts: RequestInit = {}) {
  const r = await fetch(`${API}${path}`, { headers: { "Content-Type": "application/json" }, ...opts });
  return r.json();
}
export const getTools = () => api("/api/tools");
export const getModels = () => api("/api/models");
export const getSkills = () => api("/api/skills");
export const getMcp = () => api("/api/mcp");
export const runWorkflow = (id: string, inputs: Record<string, string>) =>
  api(`/api/workflows/${id}/run`, { method: "POST", body: JSON.stringify({ inputs }) });
