"""ComfyUI client — live-verified endpoint catalog, node-001 @ 127.0.0.1:8188.

Core pattern (standard): GET /object_info -> POST /upload/image (if needed)
-> POST /prompt (queue workflow) -> WS /ws progress -> GET /history/{id}
-> GET /view?filename=...&subfolder=...&type=output.

Studio suites short-circuit that: they queue a composed workflow server-side
via /studio/dispatch, /motion/build, /brand/build, /voice/build, /music/build.

All methods raise httpx errors / RuntimeError with the endpoint that
failed — never a fabricated media file. If ComfyUI is unreachable (e.g.
this sandbox, which has no :8188), the node fails loudly and the run
records the error, which is the honest behaviour for a local-only service.
"""
import os, time, httpx

BASE = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188").rstrip("/")

# Studio suite routes, verified live per the 2026-10-28 audit.
STUDIO = {
    "character": {"ui": "/studio", "defaults": "/studio/defaults", "files": "/studio/files",
                  "build": "/studio/build", "dispatch": "/studio/dispatch", "jobs": "/studio/jobs", "stop": "/studio/stop"},
    "motion": {"ui": "/motion", "options": "/motion/options", "library": "/motion/library",
               "projects": "/motion/projects", "brandkits": "/motion/brandkits",
               "build": "/motion/build", "upload": "/motion/upload"},
    "brand": {"ui": "/brand", "options": "/brand/options", "kits": "/brand/kits",
              "files": "/brand/files", "logos": "/brand/logos",
              "resolve": "/brand/resolve", "extract": "/brand/extract", "build": "/brand/build"},
    "voice": {"ui": "/voice", "options": "/voice/options", "names": "/voice/names",
              "files": "/voice/files", "build": "/voice/build", "transcribe": "/voice/transcribe"},
    "music": {"ui": "/music", "options": "/music/options", "files": "/music/files",
              "build": "/music/build", "meta": "/music/meta"},
}
# Saved ComfyUI workflows on node-001 (user/default/workflows).
SAVED_WORKFLOWS = {
    "character_0_portfolio_flux2": "Flux 2 character/portfolio image generation",
    "character_1_keyframes_flux2": "Flux 2 keyframe generation for animation",
    "character_2_long_video_ltx23": "Long-form video via LTX-2.3",
    "character_3_movie_32s_ltx23": "32-second movie clip via LTX-2.3",
    "character_4_movie_90s_ltx23": "90-second movie clip via LTX-2.3",
    "character_5_fast_sdxl_reactor": "Fast SDXL + reActor face swap throughput",
    "ace_step_1_5_music": "Song / music production with ACE-Step 1.5",
}

class ComfyClient:
    def __init__(self, base_url=None):
        self.base = (base_url or BASE).rstrip("/")
    def _url(self, path):
        return self.base + path
    def get(self, path, **kw):
        with httpx.Client(timeout=60) as c:
            r = c.get(self._url(path), **kw); r.raise_for_status(); return r.json()
    def post(self, path, payload=None, **kw):
        with httpx.Client(timeout=120) as c:
            r = c.post(self._url(path), json=payload or {}, **kw); r.raise_for_status(); return r.json()
    # Core
    def system_stats(self): return self.get("/system_stats")
    def object_info(self, node_class=None):
        return self.get(f"/object_info/{node_class}" if node_class else "/object_info")
    def queue_prompt(self, prompt_graph):
        return self.post("/prompt", {"prompt": prompt_graph})
    def history(self, prompt_id=None):
        return self.get(f"/history/{prompt_id}" if prompt_id else "/history")
    def queue(self): return self.get("/queue")
    def interrupt(self): return self.post("/interrupt")
    def free(self): return self.post("/free")
    def wait_for_prompt(self, prompt_id, timeout=600, poll=2):
        deadline = time.time() + timeout
        while time.time() < deadline:
            hist = self.history(prompt_id)
            entry = hist.get(prompt_id) if isinstance(hist, dict) else None
            if entry and entry.get("outputs"):
                return entry
            time.sleep(poll)
        raise TimeoutError(f"ComfyUI prompt {prompt_id} did not finish within {timeout}s")
    def run_prompt(self, prompt_graph, timeout=600):
        queued = self.queue_prompt(prompt_graph)
        pid = queued.get("prompt_id")
        if not pid:
            raise RuntimeError(f"ComfyUI /prompt returned no prompt_id: {queued}")
        entry = self.wait_for_prompt(pid, timeout=timeout)
        return {"prompt_id": pid, "outputs": entry.get("outputs", {})}
    # Studio suites
    def studio(self, suite, action, payload=None):
        route = STUDIO[suite][action]
        if action in ("build", "dispatch", "jobs", "stop", "resolve", "extract", "transcribe", "meta"):
            return self.post(route, payload)
        return self.get(route)
    def studio_build(self, suite, payload):
        """One entry point for node types studio_character/motion/brand/voice/music."""
        if suite not in STUDIO:
            raise ValueError(f"unknown studio suite: {suite} (character, motion, brand, voice, music)")
        build_action = "dispatch" if suite == "character" else "build"
        return self.studio(suite, build_action, payload)
