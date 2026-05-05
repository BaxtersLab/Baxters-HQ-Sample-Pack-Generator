from bspg.core.config import PathsConfig, SettingsConfig, FlowchartConfig, HRTConfig, AppConfig


def test_config_classes():
    p = PathsConfig()
    s = SettingsConfig()
    f = FlowchartConfig()
    h = HRTConfig()
    app = AppConfig()

    assert isinstance(p.input_files, list)
    assert isinstance(s.backsplash_enabled, bool)
    assert hasattr(f, 'cb8')
    assert hasattr(h, 'connected')
    assert isinstance(app.paths, PathsConfig)
