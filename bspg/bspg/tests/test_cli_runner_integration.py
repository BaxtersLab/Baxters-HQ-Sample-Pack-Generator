import logging
from pathlib import Path

import pytest

from bspg.backend_adapter.cli_runner import BackendRunner, BackendProcessResult


class DummyConfig:
    class Paths:
        def __init__(self, input_files, output_folder):
            self.input_files = input_files
            self.output_folder = output_folder

    def __init__(self, input_files, output_folder):
        self.paths = DummyConfig.Paths(input_files, output_folder)


def test_run_pipeline_monkeypatched(monkeypatch, tmp_path, caplog):
    caplog.set_level(logging.INFO)
    # create dummy input file
    infile = tmp_path / 'in.wav'
    infile.write_text('dummy')
    cfg = DummyConfig([str(infile)], str(tmp_path / 'out'))

    runner = BackendRunner()

    # monkeypatch stage methods to avoid running external CLIs
    monkeypatch.setattr(runner, 'run_stage1', lambda i, o, model='htdemucs': 0)
    # create a fake file as stage1 output
    (tmp_path / 'out' / 'stage1').mkdir(parents=True)
    fake_stage1_file = tmp_path / 'out' / 'stage1' / 'stem.wav'
    fake_stage1_file.write_text('stem')
    monkeypatch.setattr(runner, 'run_stage2', lambda i, o, options=None: 0)
    monkeypatch.setattr(runner, 'run_stage3', lambda i, o, base_name='slice', count=1: [o + '/slice_1.wav'])

    res = runner.run_pipeline(cfg)
    assert isinstance(res, BackendProcessResult)
    assert res.exit_code == 0
    assert res.raw_output
