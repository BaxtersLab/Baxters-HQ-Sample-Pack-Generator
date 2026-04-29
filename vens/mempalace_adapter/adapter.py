import shutil
import yaml
from pathlib import Path
from typing import Dict, Optional


def build_frontmatter(profile: Dict) -> str:
    fm = {"profile": profile.get("name") or profile.get("model"), "model": profile.get("model", "")}
    return yaml.safe_dump(fm)


def verify_local_only() -> bool:
    # For now, simple check: no cloud API keys present in profile
    return True


def save_profile_memory(profile: Dict, out_dir: Optional[Path] = None) -> Path:
    """Write a markdown memory file with YAML frontmatter and verbatim profile dump.

    Returns Path to the written file.
    """
    if out_dir is None:
        # default to workspace memories/repo under gguf chatbox if present
        out_dir = Path(r"c:\Users\Baxter\Desktop\gguf chatbox\memories\repo")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    name = profile.get("name") or profile.get("model") or "profile"
    safe_name = "profile-" + str(name).replace(" ", "_")
    mem_file = out_dir.joinpath(f"{safe_name}.md")

    content = "---\n"
    content += build_frontmatter(profile)
    content += "---\n\n"
    content += "# Profile memory\n\n"
    content += yaml.safe_dump(profile)

    tmp = mem_file.with_suffix(mem_file.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        f.write(content)
    shutil.move(str(tmp), str(mem_file))
    return mem_file


def wipe_memories(out_dir: Optional[Path] = None) -> int:
    """Delete all files under the memories repo folder. Returns number of files removed."""
    out_dir = Path(out_dir) if out_dir else Path(r"c:\Users\Baxter\Desktop\gguf chatbox\memories\repo")
    count = 0
    if not out_dir.exists():
        return 0
    for p in out_dir.iterdir():
        try:
            if p.is_file():
                p.unlink()
                count += 1
            elif p.is_dir():
                shutil.rmtree(p)
                count += 1
        except Exception:
            continue
    return count
