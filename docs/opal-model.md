# Opal model, as implemented here
Source: DataCamp, "Google Opal Tutorial" (https://www.datacamp.com/tutorial/google-opal-tutorial),
plus opal.google's public model: describe -> visual workflow -> preview/run -> publish/share.

- Inputs: text, file, image, video, URL, drawing. In AIOC these are `input` nodes with a `kind`.
- Generate: AI model calls. In AIOC: `agent` (text/vision via LM Studio),
  `tool` (TinyWow tools), `browser`/`scraper`, `vision`, `image`/`video`
  (ComfyUI), `skill`, `mcp_tool`.
- Outputs: webpage, markdown, PDF, image, video, file, JSON. In AIOC these
  are `output` nodes that also emit an artifact record for the Run panel.
- Referencing: Opal `@step.output` == AIOC `{{node_id.output}}`.
- Rules carried over: left-to-right DAG, no cycles, named steps, preview
  before publish. AIOC adds what Opal does not expose: a real tool
  registry, local models, skills-as-folders, and MCP bridging.
