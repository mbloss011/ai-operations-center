# Tools
235 TinyWow tools are registered in `backend/app/tools/catalog.json`
(PDF 45, image ~70, video ~45, AI writing ~50, file/utility ~35,
deduplicated). Categories and ids are stable; the frontend tool picker
reads them from GET /api/tools.

Implemented locally in v0.1: word count, epoch conversion, lorem ipsum,
zip, CSV->JSON, JSON->XML, PDF text extraction + merge (PyMuPDF),
image resize/convert/B&W/crop (Pillow), MP4->MP3 (ffmpeg).
LLM-backed writing tools run through the local model, not a stub.
Everything else is registered with a clear "no local implementation yet"
error — add it in `tools/registry.py` following the existing pattern.
