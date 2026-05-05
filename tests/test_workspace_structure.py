import os


def test_folder_structure():
    assert os.path.isdir("bspg/gui")
    assert os.path.isdir("bspg/backend_adapter")
    assert os.path.isdir("bspg/core")
    assert os.path.isdir("bspg/utils")
