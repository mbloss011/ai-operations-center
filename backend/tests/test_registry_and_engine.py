import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from app.tools.registry import list_tools, run_local_tool, get_tool
from app.engine import topo_sort, render_template, run_workflow, CycleError
from app.skills import load_skills, parse_skill_md
import pytest

def test_catalog_covers_all_categories():
    cats = {t["category"] for t in list_tools()}
    assert {"pdf", "image", "video", "ai_writing", "file_utility"} <= cats
    assert len(list_tools()) >= 200
    assert len({t["id"] for t in list_tools()}) == len(list_tools())

def test_local_tools_do_not_fabricate():
    assert run_local_tool("count_words_in_your_text", {"text": "hello world"})["words"] == 2
    assert get_tool("merge_pdf") is not None

def test_dag_and_template():
    g = {"nodes": [
        {"id": "a", "type": "input", "data": {"value": "hello"}},
        {"id": "b", "type": "output", "data": {"template": "got {{a.output}}"}}],
        "edges": [{"source": "a", "target": "b"}]}
    r = run_workflow(g)
    assert r["outputs"]["b"]["output"] == "got hello"
    assert r["artifacts"][0]["content"] == "got hello"

def test_cycle_rejected():
    with pytest.raises(CycleError):
        topo_sort([{"id": "a"}, {"id": "b"}], [{"source": "a", "target": "b"}, {"source": "b", "target": "a"}])

def test_skill_frontmatter(tmp_path):
    d = tmp_path / "demo"; d.mkdir()
    (d / "SKILL.md").write_text("---\nname: demo\ndescription: test\n---\nDo X.")
    skills = load_skills(tmp_path)
    assert skills[0]["name"] == "demo" and "Do X" in skills[0]["instructions"]

def test_comfy_client_urls_and_studio_map():
    from app.comfyui import ComfyClient, STUDIO, SAVED_WORKFLOWS
    c = ComfyClient("http://127.0.0.1:8188")
    assert c._url("/prompt") == "http://127.0.0.1:8188/prompt"
    assert set(STUDIO) == {"character", "motion", "brand", "voice", "music"}
    assert "character_2_long_video_ltx23" in SAVED_WORKFLOWS
    assert STUDIO["character"]["dispatch"] == "/studio/dispatch"
    assert STUDIO["voice"]["build"] == "/voice/build"
