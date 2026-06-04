#!/usr/bin/env python3
"""CodeTyper - Terminal typewriter effect tool for coding tutorials."""

import sys
import time
import select
import tty
import termios
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import yaml

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
import typer

from config_schema import Config, CodeBlock


# Custom exceptions
class CodeTyperError(Exception):
    """Base exception for CodeTyper."""
    pass


class ConfigurationError(CodeTyperError):
    """Configuration-related errors."""
    pass


class ExecutionError(CodeTyperError):
    """Code execution errors."""
    pass


class TypewriterEngine:
    """Core typing engine with character-by-character output."""

    def __init__(self, speed: float = 0.05):
        self.speed = speed
        self.paused = False
        self.skip_block = False
        self.speed_multiplier = 1.0
        self.quit = False
        self.console = Console()
        self.old_terminal_settings = None

    def setup_terminal(self):
        """Setup terminal for raw keyboard input."""
        try:
            self.old_terminal_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
        except (OSError, termios.error):
            # Not running in an interactive terminal (e.g., piped, background)
            # Keyboard controls won't work but typing will still function
            self.old_terminal_settings = None

    def restore_terminal(self):
        """Restore terminal to normal mode."""
        if self.old_terminal_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_terminal_settings)

    def _check_keyboard_input(self) -> Optional[str]:
        """Non-blocking keyboard input check."""
        if not self.old_terminal_settings:
            # Not in interactive terminal, skip keyboard input
            return None
        try:
            if select.select([sys.stdin], [], [], 0)[0]:
                return sys.stdin.read(1)
        except (OSError, ValueError):
            # stdin not available for selection
            pass
        return None

    def _handle_key(self, key: str):
        """Handle keyboard input."""
        if key == ' ':
            self.paused = not self.paused
        elif key == '\x1b':  # ESC sequence
            next1 = sys.stdin.read(1)
            if next1 == '[':
                next2 = sys.stdin.read(1)
                if next2 == 'A':  # UP arrow
                    self.speed_multiplier = min(3.0, self.speed_multiplier * 1.5)
                elif next2 == 'B':  # DOWN arrow
                    self.speed_multiplier = max(0.5, self.speed_multiplier * 0.67)
                elif next2 == 'C':  # RIGHT arrow
                    self.skip_block = True
            else:
                # ESC key alone
                self.quit = True
        elif key.lower() == 'q':
            self.quit = True

    def type_text(self, text: str, syntax: str = "python") -> str:
        """Types text character-by-character with syntax highlighting."""
        accumulated = ""

        for i, char in enumerate(text):
            # Check for keyboard input
            key = self._check_keyboard_input()
            if key:
                self._handle_key(key)

            # Handle quit or skip
            if self.quit or self.skip_block:
                break

            # Handle pause
            while self.paused and not self.quit:
                key = self._check_keyboard_input()
                if key:
                    self._handle_key(key)
                time.sleep(0.01)

            # Type character
            accumulated += char
            sys.stdout.write(char)
            sys.stdout.flush()

            # Apply typing delay
            time.sleep(self.speed * self.speed_multiplier)

        # If we skipped, print the rest
        if self.skip_block and not self.quit:
            remaining = text[len(accumulated):]
            sys.stdout.write(remaining)
            sys.stdout.flush()
            accumulated += remaining
            self.skip_block = False

        return accumulated


class IDETyper:
    """Types code character-by-character into Positron IDE by writing to file."""

    def __init__(self, speed: float = 0.05, ide_path: str = "/Applications/Positron.app"):
        self.speed = speed
        self.ide_path = ide_path
        self.positron_cli = f"{ide_path}/Contents/Resources/app/bin/code"
        self.console = Console()
        self.output_file = None

    def open_positron(self, file_path: str):
        """Open file in Positron IDE."""
        # First, create an empty file (or clear it if it exists)
        file_path_obj = Path(file_path)
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)
        file_path_obj.write_text('')  # Ensure file is empty

        self.output_file = file_path_obj
        self.console.print(f"[cyan]Opening {file_path} in Positron...[/cyan]")

        # Open in Positron
        try:
            subprocess.run([self.positron_cli, str(file_path), "-n"], check=True)
        except FileNotFoundError:
            raise ExecutionError(f"Positron not found at {self.ide_path}. Please install Positron or specify the correct path with --ide-path.")

        # Wait for Positron to open and file to load
        time.sleep(2)

        # Activate Positron window
        self.activate_positron()
        time.sleep(0.5)
        self.toggle_zen_mode()
        time.sleep(0.5)

    def activate_positron(self):
        applescript = 'tell application "Positron" to activate'
        subprocess.run(["osascript", "-e", applescript], check=True)

    def toggle_zen_mode(self):
        applescript = (
            'tell application "System Events"\n'
            '    keystroke "k" using command down\n'
            '    delay 0.2\n'
            '    keystroke "z"\n'
            'end tell'
        )
        try:
            subprocess.run(["osascript", "-e", applescript], check=True,
                         capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            self.console.print(f"Warning: Failed to toggle Zen Mode: {e.stderr}")

    def type_keystroke(self, char: str):
        """Type a single character into Positron."""
        # Handle special characters
        if char == '\n':
            applescript = 'tell application "System Events" to keystroke return'
        elif char == '\t':
            applescript = 'tell application "System Events" to keystroke tab'
        elif char == '\\':
            applescript = 'tell application "System Events" to keystroke "\\\\"'
        elif char == '"':
            applescript = 'tell application "System Events" to keystroke "\\"" using shift down'
        else:
            # Escape backslashes and quotes in the AppleScript string
            escaped = char.replace('\\', '\\\\').replace('"', '\\"')
            applescript = f'tell application "System Events" to keystroke "{escaped}"'

        try:
            result = subprocess.run(["osascript", "-e", applescript], check=True,
                         capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            # Check for accessibility permission error
            if "osascript is not allowed to send keystrokes" in e.stderr:
                raise ExecutionError(
                    "\n\n❌ Accessibility Permission Required!\n\n"
                    "macOS requires permission for osascript to send keystrokes.\n\n"
                    "To fix this:\n"
                    "1. Open System Settings → Privacy & Security → Accessibility\n"
                    "2. Click the lock icon to make changes\n"
                    "3. Find 'osascript' or your terminal app in the list\n"
                    "4. Enable the checkbox next to it\n"
                    "5. Restart your terminal and try again\n\n"
                    "Alternatively, you can use terminal mode (without --ide flag)."
                )
            # Other errors - don't fail on individual keystrokes
            self.console.print(f"[yellow]Warning: Failed to type character '{char}': {e.stderr}[/yellow]")

    def type_text(self, text: str, syntax: str = None) -> str:
        """Types text character-by-character by writing to file (avoids auto-indent)."""
        if not self.output_file:
            # Fallback to keystroke method if file not set
            for char in text:
                self.type_keystroke(char)
                time.sleep(self.speed)
            return text

        # Read current file content
        current_content = self.output_file.read_text()

        # Type character-by-character by appending to file
        for char in text:
            current_content += char
            self.output_file.write_text(current_content)
            time.sleep(self.speed)

        return text

    def setup_terminal(self):
        """No-op for IDE mode - no terminal setup needed."""
        pass

    def restore_terminal(self):
        """No-op for IDE mode - no terminal restoration needed."""
        pass


class FileWriter:
    """Manages writing typed code to output file."""

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.file_handle = None

    def open(self):
        """Open file for writing."""
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.file_handle = open(self.filepath, 'w')

    def write_chunk(self, text: str):
        """Append text to output file."""
        if self.file_handle:
            self.file_handle.write(text)
            self.file_handle.flush()

    def close(self):
        """Close file."""
        if self.file_handle:
            self.file_handle.close()

    def finalize(self, console: Console):
        """Close file and display completion message."""
        self.close()
        console.print(f"\n[green]✓[/green] File saved to: {self.filepath}")


class CodeFormatter:
    """Formats code files after typing completes."""

    def __init__(self, language: str):
        self.language = language
        self.console = Console()

    def format_file(self, file_path: str) -> bool:
        """Format the code file. Returns True if successful."""
        try:
            if self.language == 'python':
                return self._format_python(file_path)
            elif self.language == 'r':
                return self._format_r(file_path)
            else:
                return False
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not format file: {e}[/yellow]")
            return False

    def _format_python(self, file_path: str) -> bool:
        """Format Python file with Ruff."""
        try:
            # Check if ruff is available (try both direct command and python -m)
            check_commands = [
                ['ruff', '--version'],
                ['python', '-m', 'ruff', '--version'],
            ]

            ruff_cmd = None
            for cmd in check_commands:
                try:
                    result = subprocess.run(cmd,
                                          capture_output=True,
                                          text=True,
                                          timeout=5)
                    if result.returncode == 0:
                        ruff_cmd = cmd[:-1]  # Remove '--version'
                        break
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue

            if not ruff_cmd:
                self.console.print("[dim]Ruff not found - skipping formatting[/dim]")
                return False

            # Format with ruff
            format_cmd = ruff_cmd + ['format', file_path]
            result = subprocess.run(format_cmd,
                                  capture_output=True,
                                  text=True,
                                  timeout=10)

            if result.returncode == 0:
                self.console.print("[green]✓ Formatted with Ruff[/green]")
                return True
            else:
                self.console.print(f"[yellow]Ruff formatting failed: {result.stderr}[/yellow]")
                return False

        except FileNotFoundError:
            self.console.print("[dim]Ruff not installed - skipping formatting[/dim]")
            return False
        except subprocess.TimeoutExpired:
            self.console.print("[yellow]Ruff formatting timed out[/yellow]")
            return False

    def _format_r(self, file_path: str) -> bool:
        """Format R file with styler."""
        try:
            # Check if styler is available
            check_cmd = 'Rscript -e "if (!require(styler, quietly=TRUE)) quit(status=1)"'
            result = subprocess.run(check_cmd,
                                  shell=True,
                                  capture_output=True,
                                  text=True)

            if result.returncode != 0:
                self.console.print("[dim]styler package not found - skipping formatting[/dim]")
                return False

            # Format with styler
            format_cmd = f'Rscript -e "styler::style_file(\'{file_path}\')"'
            result = subprocess.run(format_cmd,
                                  shell=True,
                                  capture_output=True,
                                  text=True,
                                  timeout=10)

            if result.returncode == 0:
                self.console.print("[green]✓ Formatted with styler[/green]")
                return True
            else:
                self.console.print(f"[yellow]styler formatting failed: {result.stderr}[/yellow]")
                return False

        except FileNotFoundError:
            self.console.print("[dim]Rscript not found - skipping formatting[/dim]")
            return False
        except subprocess.TimeoutExpired:
            self.console.print("[yellow]styler formatting timed out[/yellow]")
            return False


class CodeExecutor:
    """Executes R or Python code blocks."""

    def __init__(self, language: str):
        self.language = language
        self.console = Console()

    def execute_block(self, code: str) -> Tuple[str, str, int]:
        """Execute code and return (stdout, stderr, returncode)."""
        try:
            if self.language == 'r':
                result = subprocess.run(
                    ["Rscript", "--quiet", "-e", code],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            elif self.language == 'python':
                result = subprocess.run(
                    ["python3", "-c", code],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                return "", f"Unknown language: {self.language}", 1

            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Execution timed out (30s limit)", 1
        except FileNotFoundError as e:
            return "", f"Command not found: {e}", 1
        except Exception as e:
            return "", str(e), 1

    def display_output(self, stdout: str, stderr: str, returncode: int):
        """Display execution results with Rich formatting."""
        if returncode == 0:
            if stdout.strip():
                self.console.print(Panel(
                    stdout,
                    title="Output",
                    border_style="green"
                ))
        else:
            if stderr.strip():
                self.console.print(Panel(
                    stderr,
                    title="Error",
                    border_style="red"
                ))

    def execute_shiny(self, file_path: str, browser_command: Optional[str] = None):
        try:
            if self.language == 'python':
                cmd = ["python3", "-m", "shiny", "run", "--reload", "--launch-browser", file_path]
            elif self.language == 'r':
                cmd = ["Rscript", "-e", f"shiny::runApp('{file_path}', launch.browser = TRUE)"]
            else:
                self.console.print(f"Cannot run Shiny app for unsupported language: {self.language}")
                return

            if browser_command:
                if self.language == 'python' and "--launch-browser" in cmd:
                    cmd.remove("--launch-browser")
                elif self.language == 'r':
                    cmd = ["Rscript", "-e", f"shiny::runApp('{file_path}', launch.browser = FALSE)"]

                self.console.print(Panel(
                    "Starting Shiny app server in background...",
                    border_style="green"
                ))
                proc = subprocess.Popen(cmd)
                try:
                    time.sleep(3)
                    self.console.print(Panel(
                        f"Running browser command: {browser_command}",
                        border_style="blue"
                    ))
                    subprocess.run(browser_command, shell=True)
                finally:
                    self.console.print("Terminating Shiny app server...")
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
            else:
                self.console.print(Panel(
                    "Starting Shiny app server...\nPress Ctrl+C to stop the server.",
                    border_style="green"
                ))
                subprocess.run(cmd)
        except KeyboardInterrupt:
            self.console.print("\nShiny app server stopped.")
        except Exception as e:
            self.console.print(f"Error starting Shiny app: {e}")


class CodeTyperApp:
    """Main application orchestrator."""

    def __init__(self, config: Config):
        self.config = config
        self.console = Console()

        self.executor = CodeExecutor(config.language)
        # Choose typer based on mode
        if config.mode == 'ide':
            ide_path = config.ide_path or "/Applications/Positron.app"
            self.engine = IDETyper(config.typing_speed, ide_path)
            self.writer = None  # No separate writer in IDE mode
        else:  # terminal mode
            self.engine = TypewriterEngine(config.typing_speed)
            self.writer = FileWriter(config.output_file)

        self.execute_enabled = config.execute_blocks

        # Formatter (used in both modes if enabled)
        self.formatter = CodeFormatter(config.language) if config.format_output else None

    def run(self):
        """Main execution loop."""
        try:
            if self.config.mode == 'ide':
                self._run_ide_mode()
            else:
                self._run_terminal_mode()
        finally:
            self.engine.restore_terminal()
            if self.writer:
                self.writer.close()

    def _run_ide_mode(self):
        """Run in IDE mode - type into Positron."""
        self._display_welcome()

        # Open a blank file in Positron (will be created empty)
        self.engine.open_positron(self.config.output_file)

        self.console.print("[green]Ready to type into Positron![/green]")
        self.console.print("[yellow]Keep Positron focused - typing will begin in 2 seconds...[/yellow]\n")
        time.sleep(2)

        # Type frontmatter if exists (for Quarto files)
        if self.config.frontmatter:
            self.engine.type_text(self.config.frontmatter)
            if not self.config.frontmatter.endswith('\n'):
                self.engine.type_text('\n')

        # Process each block - type only the code, not the headers
        for i, block in enumerate(self.config.blocks, 1):
            self.console.print(f"\n[dim]Typing block {i}/{len(self.config.blocks)}: {block.name}[/dim]")

            # Type the code (without the markdown header)
            code = block.code
            if not code.endswith('\n'):
                code += '\n'
            self.engine.type_text(code)

            # Pause between blocks
            if i < len(self.config.blocks):
                time.sleep(block.pause_after)

        self.console.print("\n[green]✓ Typing complete![/green]")

        # Format the output file if enabled
        if self.formatter:
            self.console.print("\n[cyan]Formatting code...[/cyan]")
            # Give IDE a moment to save
            time.sleep(1)
            self.formatter.format_file(self.config.output_file)

        self.console.print(f"[green]Code typed into: {self.config.output_file}[/green]")

        if self.config.is_shiny and self.execute_enabled:
            self.executor.execute_shiny(self.config.output_file, self.config.browser_command)

    def _run_terminal_mode(self):
        """Run in terminal mode - type to terminal with optional execution."""
        self._display_welcome()
        self._display_controls()

        self.engine.setup_terminal()
        self.writer.open()

        # Type frontmatter if exists
        if self.config.frontmatter:
            self.writer.write_chunk(self.config.frontmatter)
            if not self.config.frontmatter.endswith('\n'):
                self.writer.write_chunk('\n')

        # Process each block
        for i, block in enumerate(self.config.blocks, 1):
            if self.engine.quit:
                break

            self._display_block_header(i, len(self.config.blocks), block)

            # Type the code
            typed_code = self._type_block(block)

            if self.engine.quit:
                break

            if block.execute and self.execute_enabled and block.type == 'code' and not self.config.is_shiny:
                self._execute_block(block, typed_code)

            # Pause between blocks
            if i < len(self.config.blocks) and not self.engine.quit:
                time.sleep(block.pause_after)

        if not self.engine.quit:
            self.writer.finalize(self.console)

            # Format the output file if enabled
            if self.formatter:
                self.console.print("\n[cyan]Formatting code...[/cyan]")
                self.formatter.format_file(self.config.output_file)

            self._display_completion()

            if self.config.is_shiny and self.execute_enabled:
                self.executor.execute_shiny(self.config.output_file, self.config.browser_command)

    def _display_welcome(self):
        """Display welcome screen."""
        self.console.print(Panel.fit(
            f"[bold cyan]CodeTyper[/bold cyan]\n"
            f"Terminal Typewriter for Coding Tutorials\n\n"
            f"File: {self.config.output_file}\n"
            f"Language: {self.config.language}\n"
            f"Blocks: {len(self.config.blocks)}",
            border_style="cyan"
        ))
        self.console.print()

    def _display_controls(self):
        """Show keyboard controls."""
        controls = (
            "[SPACE] Pause/Resume  [↑] Faster  [↓] Slower  "
            "[→] Skip Block  [Q/ESC] Quit"
        )
        self.console.print(Panel(controls, style="bold", border_style="blue"))
        self.console.print()

    def _display_block_header(self, block_num: int, total: int, block: CodeBlock):
        """Display block header."""
        header = f"[Block {block_num}/{total}] {block.name}"
        if block.description:
            header += f" - {block.description}"

        self.console.print()
        self.console.print(f"[bold yellow]{header}[/bold yellow]")
        self.console.print()

    def _type_block(self, block: CodeBlock) -> str:
        """Type a code block and write to file."""
        code = block.code
        if not code.endswith('\n'):
            code += '\n'

        typed = self.engine.type_text(code, self._get_syntax(block))
        self.writer.write_chunk(typed)

        return typed

    def _get_syntax(self, block: CodeBlock) -> str:
        """Determine syntax highlighting type."""
        if self.config.language == 'quarto':
            if block.type == 'markdown':
                return 'markdown'
            elif block.language:
                return block.language
        return self.config.language

    def _execute_block(self, block: CodeBlock, code: str):
        """Execute a code block and display results."""
        self.console.print("\n[dim]Executing...[/dim]")
        stdout, stderr, returncode = self.executor.execute_block(code)
        self.executor.display_output(stdout, stderr, returncode)

    def _display_completion(self):
        """Display completion message."""
        self.console.print()
        self.console.print(Panel.fit(
            "[bold green]✓ Typing complete![/bold green]\n"
            f"Output saved to: {self.config.output_file}",
            border_style="green"
        ))


def parse_script_file(script_file: Path) -> Config:
    """Parse an R or Python script file with YAML frontmatter and markdown headers."""
    try:
        with open(script_file) as f:
            content = f.read()

        # Check for YAML frontmatter
        if not content.startswith('---'):
            raise ConfigurationError(
                "Script file must start with YAML frontmatter between --- delimiters.\n"
                "Example:\n"
                "---\n"
                "language: python\n"
                "output_file: demo.py\n"
                "---\n"
            )

        # Split frontmatter and code
        parts = content.split('---', 2)
        if len(parts) < 3:
            raise ConfigurationError("Missing closing --- for YAML frontmatter")

        frontmatter_text = parts[1].strip()
        code_content = parts[2].lstrip('\n')

        # Parse frontmatter
        try:
            metadata = yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML frontmatter: {e}")

        # Detect language from file extension if not specified
        language = metadata.get('language')
        if not language:
            ext = script_file.suffix.lower()
            if ext in ['.py']:
                language = 'python'
            elif ext in ['.r', '.R']:
                language = 'r'
            else:
                raise ConfigurationError(
                    f"Cannot detect language from extension '{ext}'. "
                    "Please specify 'language: python' or 'language: r' in frontmatter."
                )

        # Set output_file default if not specified
        output_file = metadata.get('output_file')
        if not output_file:
            output_file = str(script_file)

        # Determine comment character based on language
        comment_char = '#'

        # Parse blocks from markdown headers
        blocks = []
        lines = code_content.split('\n')
        current_block_name = None
        current_block_code = []
        current_block_settings = {}

        for line in lines:
            stripped = line.strip()

            # Check if this is a markdown header (## Block Name)
            if stripped.startswith('##') and not stripped.startswith('###'):
                # Save previous block if exists
                if current_block_name is not None:
                    blocks.append(CodeBlock(
                        name=current_block_name,
                        code='\n'.join(current_block_code),
                        execute=current_block_settings.get('execute', True),
                        pause_after=current_block_settings.get('pause_after', 1.0),
                    ))

                # Parse new block header
                header = stripped[2:].strip()  # Remove ##

                # Check for settings like: ## Block Name | execute=false, pause_after=2.0
                if '|' in header:
                    block_name, settings_str = header.split('|', 1)
                    current_block_name = block_name.strip()

                    # Parse settings
                    current_block_settings = {}
                    for setting in settings_str.split(','):
                        setting = setting.strip()
                        if '=' in setting:
                            key, value = setting.split('=', 1)
                            key = key.strip()
                            value = value.strip()

                            # Convert types
                            if key == 'execute':
                                current_block_settings[key] = value.lower() in ['true', 'yes', '1']
                            elif key == 'pause_after':
                                try:
                                    current_block_settings[key] = float(value)
                                except ValueError:
                                    pass
                else:
                    current_block_name = header
                    current_block_settings = {}

                current_block_code = []
            else:
                # Regular code line
                if current_block_name is None:
                    # First block before any header
                    current_block_name = "Code"
                    current_block_settings = {}

                current_block_code.append(line)

        # Save last block
        if current_block_name is not None and current_block_code:
            blocks.append(CodeBlock(
                name=current_block_name,
                code='\n'.join(current_block_code),
                execute=current_block_settings.get('execute', True),
                pause_after=current_block_settings.get('pause_after', 1.0),
            ))

        if not blocks:
            raise ConfigurationError("No code blocks found in script file")

        # Create config
        config = Config(
            language=language,
            output_file=output_file,
            typing_speed=metadata.get('typing_speed', 0.05),
            execute_blocks=metadata.get('execute_blocks', True),
            pause_between_blocks=metadata.get('pause_between_blocks', 2.0),
            blocks=blocks,
            mode=metadata.get('mode', 'terminal'),
            ide_path=metadata.get('ide_path'),
            format_output=metadata.get('format_output', False),
            browser_command=metadata.get('browser_command'),
        )

        if config.is_shiny:
            parent_dir = Path(config.output_file).parent
            filename = "app.py" if config.language == 'python' else "app.R"
            config.output_file = str(parent_dir / filename)

        return config

    except FileNotFoundError:
        raise ConfigurationError(f"Script file not found: {script_file}")
    except Exception as e:
        if isinstance(e, ConfigurationError):
            raise
        raise ConfigurationError(f"Error parsing script file: {e}")


def load_config(config_file: Path) -> Config:
    """Load and parse YAML configuration file."""
    try:
        with open(config_file) as f:
            data = yaml.safe_load(f)

        if not data:
            raise ConfigurationError("Empty configuration file")

        metadata = data.get('metadata', {})
        blocks_data = data.get('blocks', [])

        # Parse blocks
        blocks = []
        for block_data in blocks_data:
            blocks.append(CodeBlock(**block_data))

        # Create config
        config = Config(
            language=metadata.get('language'),
            output_file=metadata.get('output_file'),
            typing_speed=metadata.get('typing_speed', 0.05),
            execute_blocks=metadata.get('execute_blocks', True),
            pause_between_blocks=metadata.get('pause_between_blocks', 2.0),
            blocks=blocks,
            frontmatter=data.get('frontmatter'),
            browser_command=metadata.get('browser_command'),
        )

        if config.is_shiny:
            parent_dir = Path(config.output_file).parent
            filename = "app.py" if config.language == 'python' else "app.R"
            config.output_file = str(parent_dir / filename)

        return config

    except FileNotFoundError:
        raise ConfigurationError(f"Configuration file not found: {config_file}")
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML: {e}")
    except TypeError as e:
        raise ConfigurationError(f"Invalid configuration structure: {e}")


# CLI
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
        python codetyper.py type-code examples/example_r.yaml
        python codetyper.py type-code examples/example_python.yaml --speed 0.03
        python codetyper.py type-code examples/example_simple.yaml --ide
        python codetyper.py type-code my_script.py --ide
        python codetyper.py type-code my_script.R
    """
    try:
        # Detect file type and load config
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

        # Apply CLI overrides
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
        python codetyper.py init python
        python codetyper.py init r -o my_tutorial.R
    """
    templates = {
        'r': '''---
language: r
output_file: demo.R
typing_speed: 0.05
execute_blocks: true
---

## Setup
library(ggplot2)
library(dplyr)

## Load data | pause_after=1.5
# Add your data loading code here
data <- data.frame(
  x = 1:10,
  y = rnorm(10)
)

## Process and visualize | execute=true, pause_after=2.0
# Add your analysis code here
print(data)
summary(data)
''',
        'python': '''---
language: python
output_file: demo.py
typing_speed: 0.05
execute_blocks: true
---

## Import libraries
import pandas as pd
import numpy as np

## Load data | pause_after=1.5
# Add your data loading code here
data = {
    'x': range(1, 11),
    'y': np.random.randn(10)
}
df = pd.DataFrame(data)

## Process and display | execute=true, pause_after=2.0
# Add your analysis code here
print(df)
print(df.describe())
'''
    }

    if language not in templates:
        typer.secho(
            f"Unknown language: {language}. Choose from: r, python",
            fg=typer.colors.RED,
            err=True
        )
        raise typer.Exit(1)

    # Set default output filename if not specified
    if output is None:
        output = Path(f"demo.{language if language == 'r' else 'py'}")

    output.write_text(templates[language])
    typer.secho(f"✓ Created template: {output}", fg=typer.colors.GREEN)
    typer.secho(f"\nTo use this template:", fg=typer.colors.CYAN)
    typer.secho(f"  1. Edit {output} with your code", fg=typer.colors.CYAN)
    typer.secho(f"  2. Run: python codetyper.py type-code {output}", fg=typer.colors.CYAN)
    typer.secho(f"  3. Or with IDE mode: python codetyper.py type-code {output} --ide", fg=typer.colors.CYAN)


if __name__ == "__main__":
    app()
