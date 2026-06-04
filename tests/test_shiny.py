from unittest.mock import MagicMock, patch
from codetyper.config import Config, CodeBlock
from codetyper.app import CodeTyperApp


def test_shiny_detection_python():
    block = CodeBlock(name="Import", code="from shiny import App, render, ui")
    config = Config(language="python", output_file="demo.py", blocks=[block])
    assert config.is_shiny is True

    block2 = CodeBlock(name="Import", code="import shiny")
    config2 = Config(language="python", output_file="demo.py", blocks=[block2])
    assert config2.is_shiny is True


def test_shiny_detection_r():
    block = CodeBlock(name="Import", code="library(shiny)")
    config = Config(language="r", output_file="demo.R", blocks=[block])
    assert config.is_shiny is True

    block2 = CodeBlock(name="Import", code="require(shiny)")
    config2 = Config(language="r", output_file="demo.R", blocks=[block2])
    assert config2.is_shiny is True


def test_non_shiny_detection():
    block = CodeBlock(name="Import", code="import pandas as pd")
    config = Config(language="python", output_file="demo.py", blocks=[block])
    assert config.is_shiny is False


@patch("codetyper.app.FileWriter")
@patch("codetyper.app.TypewriterEngine")
def test_shiny_bypasses_individual_execution(mock_engine, mock_writer):
    block = CodeBlock(name="App", code="from shiny import App\napp = App(None, None)", execute=True)
    config = Config(
        language="python",
        output_file="demo.py",
        execute_blocks=True,
        blocks=[block]
    )
    app = CodeTyperApp(config)
    app.engine.quit = False
    app.executor = MagicMock()
    app._display_welcome = MagicMock()
    app._display_controls = MagicMock()
    app._display_block_header = MagicMock()
    app._display_completion = MagicMock()
    app._type_block = MagicMock(return_value="from shiny import App\napp = App(None, None)")
    app._start_recording = MagicMock()
    app._stop_recording = MagicMock()

    app.run()

    app.executor.execute_block.assert_not_called()
    app.executor.execute_shiny.assert_called_once_with("demo.py", None)


@patch("codetyper.app.FileWriter")
@patch("codetyper.app.TypewriterEngine")
def test_shiny_passes_browser_command(mock_engine, mock_writer):
    block = CodeBlock(name="App", code="from shiny import App\napp = App(None, None)", execute=True)
    config = Config(
        language="python",
        output_file="demo.py",
        execute_blocks=True,
        blocks=[block],
        browser_command="python3 -m unittest test_script.py"
    )
    app = CodeTyperApp(config)
    app.engine.quit = False
    app.executor = MagicMock()
    app._display_welcome = MagicMock()
    app._display_controls = MagicMock()
    app._display_block_header = MagicMock()
    app._display_completion = MagicMock()
    app._type_block = MagicMock(return_value="from shiny import App\napp = App(None, None)")
    app._start_recording = MagicMock()
    app._stop_recording = MagicMock()

    app.run()

    app.executor.execute_shiny.assert_called_once_with("demo.py", "python3 -m unittest test_script.py")


@patch("codetyper.executor.subprocess")
@patch("codetyper.executor.time.sleep")
def test_execute_shiny_with_browser_command(mock_sleep, mock_subprocess):
    mock_proc = MagicMock()
    mock_subprocess.Popen.return_value = mock_proc
    from codetyper.executor import CodeExecutor
    executor = CodeExecutor("python")
    executor.execute_shiny("demo.py", "python3 test_script.py")

    mock_subprocess.Popen.assert_called_once_with(["python3", "-m", "shiny", "run", "--reload", "demo.py"])
    mock_subprocess.run.assert_called_once_with("python3 test_script.py", shell=True)
    mock_proc.terminate.assert_called_once()
    mock_proc.wait.assert_called_once_with(timeout=5)


def test_shiny_output_file_enforcement(tmp_path):
    py_content = """---
language: python
output_file: custom_name.py
---
## App
from shiny import App
"""
    py_file = tmp_path / "test_shiny.py"
    py_file.write_text(py_content)

    from codetyper.parser import parse_script_file
    config = parse_script_file(py_file)
    assert config.output_file == "app.py" or config.output_file == "./app.py"

    r_content = """---
language: r
output_file: custom_name.R
---
## App
library(shiny)
"""
    r_file = tmp_path / "test_shiny.R"
    r_file.write_text(r_content)

    config_r = parse_script_file(r_file)
    assert config_r.output_file == "app.R" or config_r.output_file == "./app.R"


