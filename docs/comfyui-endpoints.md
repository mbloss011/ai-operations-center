# ComfyUI custom endpoints (live-verified, node-001 :8188)

Client: `backend/app/comfyui.py` (`ComfyClient`). Do not re-implement
these routes ad hoc — import the client.

## Core
- POST /prompt — queue a workflow (main entry point)
- GET /history, /history/{prompt_id} — job results + outputs
- DEL /history, GET/POST /queue, POST /interrupt, POST /free
- GET /api/jobs, /api/jobs/{job_id}, POST /api/jobs/{job_id}/cancel
- GET /object_info, /object_info/{node_class} — 1,229 node schemas
- GET /system_stats, /features, /models, /models/{folder}, /embeddings, /extensions
- GET /view, /view_metadata/{folder_name}, POST /upload/image, /upload/mask
- WS /ws — progress streaming, queue events, binary previews
- GET /, /users, /settings, /userdata, /workflow_templates, /i18n
- GET /internal/logs, /internal/folder_paths, /internal/files/{type}

## Studio suites (in-house custom nodes)
- character_studio: GET /studio, /studio/defaults, /studio/files;
  POST /studio/build, /studio/dispatch, /studio/jobs, /studio/stop;
  DEL /studio/files. Note: no /studio/options exists.
- motion_studio: GET /motion, /motion/options, /motion/library, /motion/projects, /motion/brandkits,
  /motion/templates.js, /motion/gsap.js, /motion/static/{name}, /motion/file/{ref},
  /motion/analyze, /motion/probe; POST/DEL /motion/upload, /motion/projects, /motion/build, /motion/file/{ref}
- brand_studio: GET /brand, /brand/options, /brand/kits, /brand/files, /brand/logos,
  /brand/scenes.js, /brand/book/{path}; POST /brand/resolve, /brand/extract, /brand/kits,
  /brand/build, /brand/book; DEL /brand/kits/{slug}
- voice_studio: GET /voice, /voice/options, /voice/names, /voice/voices/{vid}/ref.wav, /voice/files;
  POST /voice/voices, /voice/transcribe, /voice/build; DEL /voice/voices, /voice/files
- music_studio: GET /music, /music/options, /music/files;
  POST /music/build, /music/meta; DEL /music/files

## Saved workflows mapped to node types
character_0_portfolio_flux2, character_1_keyframes_flux2,
character_2_long_video_ltx23, character_3_movie_32s_ltx23,
character_4_movie_90s_ltx23, character_5_fast_sdxl_reactor,
ace_step_1_5_music. A `comfy_prompt` node takes a full workflow graph
in `data.prompt`; a `studio_*` node takes the suite payload in `data.payload`.
