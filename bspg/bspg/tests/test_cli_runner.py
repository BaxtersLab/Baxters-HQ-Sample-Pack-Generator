import sys
from bspg.backend_adapter.cli_runner import BackendRunner, BackendCommand


def test_build_command_and_run(tmp_path):
    runner = BackendRunner(backend_path=sys.executable)
    class C: pass
    c = C()
    c.paths = type('P', (), {'input_files': [str(tmp_path / 'a.wav')], 'output_folder': str(tmp_path)})()
    c.flowchart = None
    args = runner.build_command(c)
    assert isinstance(args, list)

    # run a harmless python command that prints
    res = runner.run_command([sys.executable, '-c', 'print("hello")'])
    assert res.exit_code == 0
    assert 'hello' in ''.join(res.raw_output)
