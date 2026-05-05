from bspg.core.errors import (
    BSPGError,
    ConfigError,
    PathError,
    BackendError,
    FlowchartError,
    HRTError,
    GUIError,
    ValidationError,
)


def test_error_hierarchy():
    assert issubclass(ConfigError, BSPGError)
    assert issubclass(PathError, BSPGError)
    assert issubclass(BackendError, BSPGError)
    assert issubclass(FlowchartError, BSPGError)
    assert issubclass(HRTError, BSPGError)
    assert issubclass(GUIError, BSPGError)
    assert issubclass(ValidationError, BSPGError)

    # instantiation
    ConfigError('bad config')
    PathError('/tmp/foo', 'not found')
    BackendError(1, 'stderr', 'backend failed')
    FlowchartError({'cb1': True}, 'invalid')
    HRTError('down', 'cannot connect')
    GUIError('MainWindow', 'failed')
    ValidationError('input', 'missing')
