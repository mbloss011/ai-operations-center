"""Tool registry: TinyWow catalog + real implementations for the subset
that can run locally without inventing results.

Every catalog entry is addressable by id from an agent/tool node.
Kinds: pdf / image / video / file / llm.
- pdf/image: PyMuPDF / Pillow when installed, else a clear missing-dependency error.
- video: ffmpeg subprocess when installed, else a clear error.
- file: stdlib (csv/json/xml/zip/qr needs qrcode, epoch, word count, lorem).
- llm: delegated to the configured local LLM via the engine (see engine.py).
  The registry itself never fabricates LLM output.
"""
import json, pathlib, shutil, subprocess, zipfile
_CATALOG = json.loads((pathlib.Path(__file__).parent / "catalog.json").read_text())
TOOLS = {t["id"]: t for t in _CATALOG["tools"]}

def list_tools(category=None):
    return [t for t in _CATALOG["tools"] if category is None or t["category"] == category]

def get_tool(tool_id):
    return TOOLS.get(tool_id)

def run_local_tool(tool_id, payload):
    """Run a non-LLM tool. Returns dict. Raises RuntimeError on missing deps."""
    tool = get_tool(tool_id)
    if tool is None:
        raise ValueError(f"unknown tool: {tool_id}")
    if tool["kind"] == "llm":
        raise RuntimeError("llm tool must run through the agent engine, not run_local_tool")
    if tool_id == "count_words_in_your_text":
        text = payload.get("text", "")
        return {"words": len(text.split()), "characters": len(text)}
    if tool_id == "convert_epoch_to_human_readable_date":
        import datetime
        v = payload.get("epoch")
        return {"human": datetime.datetime.fromtimestamp(float(v), datetime.timezone.utc).isoformat()} if v is not None else {"error": "epoch required"}
    if tool_id == "generate_lorem_ipsum_placeholder_text":
        n = int(payload.get("paragraphs", 1))
        para = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
        return {"text": "\n\n".join([para] * max(1, n))}
    if tool_id == "create_zip_file_online":
        # Local equivalent: zip files already in the run workdir.
        files = payload.get("files", [])
        out = payload.get("output", "archive.zip")
        with zipfile.ZipFile(out, "w") as z:
            for f in files:
                z.write(f)
        return {"output": out, "files": files}
    if tool["kind"] == "pdf":
        try:
            import fitz  # PyMuPDF
        except ImportError as e:
            raise RuntimeError("PyMuPDF is required for PDF tools: pip install PyMuPDF") from e
        if tool_id in ("extract_text_from_pdf", "convert_pdf_to_text"):
            doc = fitz.open(payload["input"])
            return {"text": "\n".join(p.get_text() for p in doc)}
        if tool_id == "merge_pdf":
            out = fitz.open()
            for f in payload["inputs"]:
                out.insert_pdf(fitz.open(f))
            out.save(payload.get("output", "merged.pdf"))
            return {"output": payload.get("output", "merged.pdf")}
        raise RuntimeError(f"PDF tool {tool_id} is registered but has no local implementation yet — wire it in tools/registry.py rather than stubbing output.")
    if tool["kind"] == "image":
        try:
            from PIL import Image
        except ImportError as e:
            raise RuntimeError("Pillow is required for image tools: pip install Pillow") from e
        if tool_id in ("resize_image",):
            im = Image.open(payload["input"])
            im = im.resize((int(payload.get("width", im.width)), int(payload.get("height", im.height))))
            out = payload.get("output", "resized.png"); im.save(out); return {"output": out}
        if tool_id in ("convert_png_to_jpg", "convert_jpg_to_png", "convert_webp_to_png", "convert_png_to_webp"):
            im = Image.open(payload["input"]).convert("RGB")
            out = payload.get("output", "converted.png"); im.save(out); return {"output": out}
        if tool_id in ("make_photo_black_and_white",):
            im = Image.open(payload["input"]).convert("L")
            out = payload.get("output", "bw.png"); im.save(out); return {"output": out}
        if tool_id in ("crop_image",):
            im = Image.open(payload["input"])
            box = payload.get("box", [0, 0, im.width, im.height])
            out = payload.get("output", "cropped.png"); im.crop(box).save(out); return {"output": out}
        raise RuntimeError(f"Image tool {tool_id} is registered but has no local implementation yet.")
    if tool["kind"] == "video":
        if shutil.which("ffmpeg") is None:
            raise RuntimeError("ffmpeg is required for video tools and was not found on PATH.")
        if tool_id == "convert_mp4_to_mp3":
            subprocess.run(["ffmpeg", "-y", "-i", payload["input"], payload.get("output", "audio.mp3")], check=True, capture_output=True)
            return {"output": payload.get("output", "audio.mp3")}
        raise RuntimeError(f"Video tool {tool_id} is registered but has no local implementation yet.")
    if tool["kind"] == "file":
        if tool_id == "convert_csv_to_json":
            import csv
            with open(payload["input"], newline="") as f:
                rows = list(csv.DictReader(f))
            return {"rows": rows}
        if tool_id == "convert_json_to_xml":
            import json as _j, xml.etree.ElementTree as ET
            data = _j.loads(payload.get("text", "{}"))
            root = ET.Element("root")
            for k, v in data.items():
                c = ET.SubElement(root, str(k)); c.text = str(v)
            return {"xml": ET.tostring(root, encoding="unicode")}
        raise RuntimeError(f"File tool {tool_id} is registered but has no local implementation yet.")
    raise RuntimeError(f"Tool {tool_id} has no local implementation yet.")
