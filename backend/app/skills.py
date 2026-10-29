"""agentskills.io-style skills-as-folders, same pattern as CADENCE.

A skill is a folder under SKILLS_DIR containing SKILL.md with frontmatter:
    ---
    name: web-research
    description: Research a topic on the web and return cited notes.
    ---
    # instructions ...

Skills are loaded at startup and on /api/skills/reload. An agent node can
invoke a skill by name; the skill's instructions are prepended to the
agent prompt and its scripts (if any) become callable tools.
"""
import pathlib, re

def parse_skill_md(text):
    meta = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1); meta[k.strip()] = v.strip()
            body = parts[2].strip()
    return meta, body

def load_skills(skills_dir):
    skills = []
    base = pathlib.Path(skills_dir)
    if not base.exists():
        return skills
    for folder in sorted(base.iterdir()):
        md = folder / "SKILL.md"
        if folder.is_dir() and md.exists():
            meta, body = parse_skill_md(md.read_text())
            skills.append({
                "name": meta.get("name", folder.name),
                "description": meta.get("description", ""),
                "path": str(folder),
                "instructions": body,
                "scripts": sorted(p.name for p in folder.glob("scripts/*")) if (folder / "scripts").exists() else [],
            })
    return skills
