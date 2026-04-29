import io
import logging
import os
from pathlib import Path

import pytest

from bspg.backend_adapter.stage1_demucs import Stage1Demucs
from bspg.backend_adapter.stage2_repair import Stage2Repair
from bspg.backend_adapter.stage3_slicer import Stage3Slicer


class FakePopen:
    def __init__(self, cmd, stdout, stderr, text):
        self.cmd = cmd
        self.stdout = io.StringIO("line1\nline2\n")

    def wait(self, timeout=None):
        return 0


def test_stage1_build_command_and_run(monkeypatch, tmp_path, caplog):
    caplog.set_level(logging.INFO)
    demucs = Stage1Demucs(demucs_exe="demucs")
    in_f = tmp_path / "in.wav"
    in_f.write_text("dummy")
    out_d = tmp_path / "out"
    out_d.mkdir()

    cmd = demucs.build_command(in_f, out_d, model="htdemucs")
    assert isinstance(cmd, list)

    monkeypatch.setattr("subprocess.Popen", lambda *a, **k: FakePopen(*a, **k))
    rc = demucs.run(in_f, out_d, model="htdemucs")
    assert rc == 0
    assert any("Starting Demucs" in r.message for r in caplog.records)


def test_stage2_repair_run(monkeypatch, tmp_path, caplog):
    caplog.set_level(logging.INFO)
    repair = Stage2Repair(repair_exe="repair_tool")
    in_f = tmp_path / "in.wav"
    out_f = tmp_path / "out.wav"
    in_f.write_text("dummy")

    monkeypatch.setattr("subprocess.Popen", lambda *a, **k: FakePopen(*a, **k))
    rc = repair.run(in_f, out_f)
    assert rc == 0


def test_stage3_slicer_creates_files(tmp_path):
    slicer = Stage3Slicer()
    in_f = tmp_path / "in.wav"
    in_f.write_text("dummy")
    out_d = tmp_path / "slices"
    outs = slicer.run(in_f, out_d, base_name="s", count=3)
    assert len(outs) == 3
    for p in outs:
        assert p.exists()
