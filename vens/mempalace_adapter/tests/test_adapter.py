import tempfile
from pathlib import Path

from vens.mempalace_adapter import save_profile_memory


def test_save_profile_memory(tmp_path: Path):
    profile = {"name": "TestProfile", "model": "gpt-test", "context": {"temperature": 0.7}}
    out = save_profile_memory(profile, out_dir=tmp_path)
    assert out.exists()
    txt = out.read_text(encoding="utf-8")
    assert "profile" in txt
    assert "gpt-test" in txt
    assert "temperature" in txt
