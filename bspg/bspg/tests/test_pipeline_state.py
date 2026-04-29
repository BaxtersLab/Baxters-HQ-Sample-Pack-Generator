from bspg.backend_adapter.pipeline_state import PipelineStage, PipelineEvent, PipelineState, PipelineStatus


def test_pipeline_state_models():
    e = PipelineEvent(timestamp=0.0, stage=PipelineStage.IDLE, message='ok', raw_line='ok')
    s = PipelineState()
    s.events.append(e)
    assert s.stage == PipelineStage.IDLE
    assert isinstance(s.events, list)
    ps = PipelineStatus()
    assert ps.running in (True, False)
