"""Agent Skills Loader and Tools for NetraCare Patient Assistant (Iteration 6 R4 & R5).
Scans skills/ directory, extracts YAML front matter for prompt injection,
and provides load_skill and read_skill_file tools with directory traversal protection.
"""
from pathlib import Path
import re
import yaml
from typing import Dict, Any, Optional
from langchain_core.tools import tool

# Find skills directory in repository root
ROOT_DIR = Path(__file__).resolve().parents[3]
SKILLS_DIR = ROOT_DIR / "skills"
if not SKILLS_DIR.exists():
    # Fallback to local cwd check
    SKILLS_DIR = Path.cwd() / "skills"

def load_skill_frontmatter() -> Dict[str, Dict[str, str]]:
    """Parse front matter (name, description) of all skills at startup."""
    skills = {}
    if not SKILLS_DIR.exists():
        return skills

    for folder in SKILLS_DIR.iterdir():
        if folder.is_dir():
            skill_md = folder / "SKILL.md"
            if skill_md.exists():
                try:
                    content = skill_md.read_text(encoding="utf-8")
                    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
                    if match:
                        fm = yaml.safe_load(match.group(1))
                        name = fm.get("name", folder.name)
                        desc = fm.get("description", "").strip()
                        skills[name] = {
                            "name": name,
                            "description": desc,
                            "folder": folder.name,
                            "path": str(folder),
                        }
                except Exception as e:
                    print(f"Error parsing skill in {folder}: {e}")
    return skills

# Cache loaded skills metadata
AVAILABLE_SKILLS = load_skill_frontmatter()

def format_skills_for_prompt() -> str:
    """Format available skills list for inclusion in system prompt."""
    if not AVAILABLE_SKILLS:
        return ""
    lines = ["AVAILABLE SKILLS (use load_skill only when a task specifically needs one):"]
    for name, data in AVAILABLE_SKILLS.items():
        lines.append(f"- {name}: {data['description']}")
    lines.append(
        "\nSkills hold clinic know-how for specific journeys. If a patient query matches an available skill, "
        "call `load_skill(name)`. To read an extra file referenced by the skill, call `read_skill_file(name, file)`. "
        "Do not load a skill for simple questions answered by search_clinic_docs or basic booking tools."
    )
    return "\n".join(lines)

@tool
def load_skill(name: str) -> str:
    """Load the full instructions and steps of an available clinic skill by name."""
    clean_name = name.strip()
    if clean_name not in AVAILABLE_SKILLS:
        return f"Error: Unknown skill '{clean_name}'. Available skills: {', '.join(AVAILABLE_SKILLS.keys())}"

    skill_folder = SKILLS_DIR / AVAILABLE_SKILLS[clean_name]["folder"]
    skill_file = skill_folder / "SKILL.md"
    if not skill_file.exists():
        return f"Error: SKILL.md not found for skill '{clean_name}'."

    content = skill_file.read_text(encoding="utf-8")
    # Strip front matter and return instruction body
    match = re.match(r"^---\s*\n.*?\n---\s*\n(.*)$", content, re.DOTALL)
    body = match.group(1).strip() if match else content
    return body

@tool
def read_skill_file(name: str, file: str) -> str:
    """Read an extra documentation or guide file belonging to a loaded skill (e.g. 'post-op-guide.md', 'questions.md', 'checklists.md').
    
    Args:
        name: The name of the skill.
        file: The relative filename within that skill's folder.
    """
    clean_name = name.strip()
    if clean_name not in AVAILABLE_SKILLS:
        return f"Error: Unknown skill '{clean_name}'."

    clean_file = file.strip()
    # Directory traversal guard: strictly reject .., absolute paths, drive letters
    if ".." in clean_file or clean_file.startswith("/") or clean_file.startswith("\\") or ":" in clean_file:
        return "Error: Access denied. Cannot read files outside the skill directory."

    skill_folder = (SKILLS_DIR / AVAILABLE_SKILLS[clean_name]["folder"]).resolve()
    target_file = (skill_folder / clean_file).resolve()

    # Verify target stays inside skill directory
    try:
        target_file.relative_to(skill_folder)
    except ValueError:
        return "Error: Access denied. Cannot read files outside the skill directory."

    if not target_file.exists() or not target_file.is_file():
        return f"Error: File '{clean_file}' does not exist in skill '{clean_name}'."

    try:
        return target_file.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file '{clean_file}': {str(e)}"

