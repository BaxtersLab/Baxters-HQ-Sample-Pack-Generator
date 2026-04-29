def test_import_cli():
    import importlib
    m = importlib.import_module('hqspg.cli')
    assert hasattr(m, 'main')
