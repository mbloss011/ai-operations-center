import WorkflowCanvas from "../components/WorkflowCanvas";
export default function Home() {
  return (<main style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
    <header style={{ padding: "12px 16px", borderBottom: "1px solid #1c3442" }}>
      <h1 style={{ margin: 0, fontSize: 20 }}>AI Operations Center</h1>
      <p style={{ margin: "4px 0 0", color: "#8fb3c2" }}>Input → nodes → output pages + artifacts, in realtime. Opal-style, self-hosted, local models.</p>
    </header>
    <WorkflowCanvas />
  </main>);
}
