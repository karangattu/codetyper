from pathlib import Path
from codetyper.parser import parse_script_file

def test_example_script_paths():
    # Verify examples/example_script.py resolves output_file to a relative path
    config_py = parse_script_file(Path("examples/example_script.py"))
    assert config_py.output_file == "demo_from_script.py"

    # Verify examples/example_script.R resolves output_file to a relative path
    config_r = parse_script_file(Path("examples/example_script.R"))
    assert config_r.output_file == "demo_from_script.R"

def test_config_recording_defaults():
    config_py = parse_script_file(Path("examples/example_script.py"))
    assert config_py.record is False
    assert config_py.record_device is None
    assert config_py.record_output == "recording.mp4"
