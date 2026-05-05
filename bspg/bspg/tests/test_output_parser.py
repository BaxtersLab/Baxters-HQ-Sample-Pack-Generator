from bspg.backend_adapter.output_parser import BackendOutputParser, parse_cli_output
from bspg.backend_adapter.pipeline_state import PipelineStage


def test_detect_stage_and_progress_and_error():
    bp = BackendOutputParser()
    e = bp.parse_line('Starting Stem Separation...')
    assert e.stage == PipelineStage.STEM_SEPARATION
    s = bp.update_state(e)
    assert s.stage == PipelineStage.STEM_SEPARATION

    e2 = bp.parse_line('Progress: 42%')
    bp.update_state(e2)
    assert abs(bp.state.progress - 0.42) < 0.01

    e3 = bp.parse_line('ERROR: Missing file')
    bp.update_state(e3)
    assert bp.state.stage == PipelineStage.ERROR


def test_parse_cli_output_helper():
    out = 'Starting Stem Separation...\nProgress: 50%\nPipeline complete.'
    state = parse_cli_output(out)
    assert state.stage == PipelineStage.COMPLETE or state.progress >= 0.5
