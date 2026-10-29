"""Local model registry — node-001 audit, 2026-10-28 23:20 UTC.
LM Studio: http://127.0.0.1:1234/v1 (OpenAI-compatible). ComfyUI: :8188.
Qdrant: :6333. No cloud model is required; cloud fallbacks are opt-in only.
"""
MODELS = [
    {"id": "ornith-1.5-9b", "family": "Ornith 1.5", "size": "9B dense", "ctx": 113664,
     "modalities": ["text", "vision"], "role": "default agent + vision",
     "endpoint": "lmstudio", "notes": "Primary work LLM, mmproj F16, currently hot-loaded."},
    {"id": "ornith-1.5-35b-a3b", "family": "Ornith 1.5", "size": "35B MoE / 3B active",
     "ctx": 0, "modalities": ["text", "vision"], "role": "heavy reasoning",
     "endpoint": "lmstudio", "notes": "Needs multi-GPU or CPU offload on 3x RTX 3060 (36 GB)."},
    {"id": "lfm2-1.2b", "family": "Liquid LFM2", "size": "1.2B", "ctx": 8192,
     "modalities": ["text"], "role": "routing / tool-use", "endpoint": "lmstudio",
     "notes": "Ultra-light agent/routing LLM."},
    {"id": "qwen3.5-9b", "family": "Qwen", "size": "9B", "ctx": 0,
     "modalities": ["text", "vision"], "role": "alternate LLM", "endpoint": "lmstudio", "notes": ""},
    {"id": "qwen3.8-27b", "family": "Qwen", "size": "27B", "ctx": 0,
     "modalities": ["text", "vision"], "role": "alternate LLM", "endpoint": "lmstudio", "notes": ""},
    {"id": "muse-glimmer-30b", "family": "Muse Glimmer", "size": "30B", "ctx": 0,
     "modalities": ["text", "vision"], "role": "alternate LLM", "endpoint": "lmstudio", "notes": ""},
    {"id": "granite-docling-258m", "family": "IBM Docling", "size": "258M", "ctx": 0,
     "modalities": ["vision", "document"], "role": "document OCR / DOM parsing",
     "endpoint": "lmstudio", "notes": "Document understanding, not chat."},
    {"id": "text-embedding-nomic-embed-text-v1.5", "family": "Nomic", "size": "small",
     "ctx": 0, "modalities": ["embedding"], "role": "RAG embeddings",
     "endpoint": "lmstudio", "notes": "Vector search over Qdrant/Chroma."},
    {"id": "flux2-turbo", "family": "Flux 2", "size": "Turbo", "ctx": 0,
     "modalities": ["image"], "role": "fast text-to-image", "endpoint": "comfyui", "notes": "ComfyUI checkpoint Flux2TurboComfyv2."},
    {"id": "flux2-dev", "family": "Flux 2", "size": "Dev fp8", "ctx": 0,
     "modalities": ["image"], "role": "full-quality text-to-image", "endpoint": "comfyui", "notes": ""},
    {"id": "realvisxl-v5", "family": "SDXL", "size": "RealVisXL V5", "ctx": 0,
     "modalities": ["image"], "role": "photorealistic image", "endpoint": "comfyui", "notes": ""},
    {"id": "qwen-image-3.8b", "family": "Qwen Image", "size": "3.8B fp8", "ctx": 0,
     "modalities": ["image"], "role": "text-to-image", "endpoint": "comfyui", "notes": ""},
    {"id": "wan2.2-i2v-14b", "family": "Wan 2.2", "size": "14B fp8", "ctx": 0,
     "modalities": ["video"], "role": "image-to-video", "endpoint": "comfyui",
     "notes": "Two-stage hi/lo + LightX2V 4-step LoRAs."},
    {"id": "ltx-2.3-22b", "family": "LTX 2.3", "size": "22B fp8", "ctx": 0,
     "modalities": ["video"], "role": "long-form video to ~90s", "endpoint": "comfyui",
     "notes": "Distilled LoRA + talking-video ID LoRA + 2x upscaler."},
    {"id": "ace-step-1.5", "family": "ACE-Step", "size": "1.5 Turbo", "ctx": 0,
     "modalities": ["audio", "music"], "role": "music generation", "endpoint": "comfyui", "notes": ""},
    {"id": "qwen3-vl-4b", "family": "Qwen3-VL", "size": "4B fp8", "ctx": 0,
     "modalities": ["vision"], "role": "vision-language encoder", "endpoint": "comfyui", "notes": ""},
    {"id": "gemma-3-12b-encoder", "family": "Gemma 3", "size": "12B fp4", "ctx": 0,
     "modalities": ["text"], "role": "prompt encoder for Flux 2", "endpoint": "comfyui", "notes": ""},
    {"id": "mistral-3-small-encoder", "family": "Mistral 3", "size": "Small fp8", "ctx": 0,
     "modalities": ["text"], "role": "CLIP-style encoder for Flux 2", "endpoint": "comfyui", "notes": ""},
]
def models_for(modality):
    return [m for m in MODELS if modality in m["modalities"]]
def get_model(model_id):
    for m in MODELS:
        if m["id"] == model_id:
            return m
    return None
