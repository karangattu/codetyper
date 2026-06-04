"""Command-line interface for CodeTyper."""

from pathlib import Path
from typing import Optional

import typer

from codetyper.app import CodeTyperApp
from codetyper.parser import load_config, parse_script_file
from codetyper.exceptions import ConfigurationError
from codetyper.templates import TEMPLATES

app = typer.Typer(help="CodeTyper - Terminal typewriter for coding tutorials")


@app.command()
def type_code(
    config_file: Path = typer.Argument(..., help="YAML config file or R/Python script with frontmatter"),
    speed: Optional[float] = typer.Option(None, "--speed", "-s", help="Override typing speed"),
    no_execute: bool = typer.Option(False, "--no-execute", help="Disable code execution"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Override output file"),
    ide: bool = typer.Option(False, "--ide", help="Type into Positron IDE instead of terminal"),
    ide_path: Optional[str] = typer.Option(None, "--ide-path", help="Path to Positron.app (default: /Applications/Positron.app)"),
    format_code: bool = typer.Option(False, "--format", help="Format output with Ruff (Python) or styler (R) after typing"),
    record: bool = typer.Option(False, "--record", help="Enable automatic screen recording with FFmpeg"),
    record_device: str = typer.Option("1", "--record-device", help="FFmpeg avfoundation video input device index"),
    record_output: str = typer.Option("recording.mp4", "--record-output", help="Output file for the screen recording"),
    browser_cmd: Optional[str] = typer.Option(None, "--browser-cmd", help="Browser/test command to run against the running Shiny app"),
):
    """
    Type code character-by-character for tutorial recording.

    Example:
        codetyper type-code examples/example_script.py
        codetyper type-code examples/example_script.R --speed 0.03
        codetyper type-code my_script.py --ide
    """
    try:
        file_ext = config_file.suffix.lower()
        if file_ext in ['.yaml', '.yml']:
            config = load_config(config_file)
        elif file_ext in ['.py', '.r']:
            config = parse_script_file(config_file)
        else:
            raise ConfigurationError(
                f"Unsupported file type: {file_ext}\n"
                "Expected .yaml, .yml, .py, or .r/.R"
            )

        if speed is not None:
            config.typing_speed = speed
        if no_execute:
            config.execute_blocks = False
        if output:
            config.output_file = str(output)
        if ide:
            config.mode = 'ide'
        if ide_path:
            config.ide_path = ide_path
        if format_code:
            config.format_output = True
        if record:
            config.record = True
        if record_device:
            config.record_device = record_device
        if record_output:
            config.record_output = record_output
        if browser_cmd:
            config.browser_command = browser_cmd

        app_instance = CodeTyperApp(config)
        app_instance.run()

    except ConfigurationError as e:
        typer.secho(f"Configuration Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except KeyboardInterrupt:
        typer.secho("\nInterrupted by user", fg=typer.colors.YELLOW)
        raise typer.Exit(0)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)


@app.command()
def init(
    language: str = typer.Argument(..., help="Language: r or python"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output script file (default: demo.py or demo.R)"),
):
    """
    Create a template script file with YAML frontmatter.

    Example:
        codetyper init python
        codetyper init r -o my_tutorial.R
    """
    if language not in TEMPLATES:
        typer.secho(
            f"Unknown language: {language}. Choose from: r, python",
            fg=typer.colors.RED,
            err=True
        )
        raise typer.Exit(1)

    if output is None:
        output = Path(f"demo.{language if language == 'r' else 'py'}")

    output.write_text(TEMPLATES[language])
    typer.secho(f"✓ Created template: {output}", fg=typer.colors.GREEN)
    typer.secho(f"\nTo use this template:", fg=typer.colors.CYAN)
    typer.secho(f"  1. Edit {output} with your code", fg=typer.colors.CYAN)
    typer.secho(f"  2. Run: codetyper type-code {output}", fg=typer.colors.CYAN)
    typer.secho(f"  3. Or with IDE mode: codetyper type-code {output} --ide", fg=typer.colors.CYAN)


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
