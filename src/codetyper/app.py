"""Main application orchestrator."""

import re
import time
import subprocess

from rich.console import Console
from rich.panel import Panel

from codetyper.config import Config, CodeBlock
from codetyper.engine import TypewriterEngine, IDETyper
from codetyper.executor import CodeExecutor
from codetyper.formatter import CodeFormatter
from codetyper.writer import FileWriter


class CodeTyperApp:
    """Main application orchestrator."""

    def __init__(self, config: Config):
        self.config = config
        self.console = Console()

        self.executor = CodeExecutor(config.language)
        if config.mode == 'ide':
            ide_path = config.ide_path or "/Applications/Positron.app"
            self.engine = IDETyper(config.typing_speed, ide_path)
            self.writer = None
        else:
            self.engine = TypewriterEngine(config.typing_speed)
            self.writer = FileWriter(config.output_file)

        self.execute_enabled = config.execute_blocks

        self.formatter = CodeFormatter(config.language) if config.format_output else None

    def run(self):
        """Main execution loop."""
        self._start_recording()
        try:
            if self.config.mode == 'ide':
                self._run_ide_mode()
            else:
                self._run_terminal_mode()
        finally:
            self.engine.restore_terminal()
            if self.writer:
                self.writer.close()
            self._stop_recording()

    def _run_ide_mode(self):
        """Run in IDE mode - type into Positron."""
        self._display_welcome()

        self.engine.open_positron(self.config.output_file)

        self.console.print("[green]Ready to type into Positron![/green]")
        self.console.print("[yellow]Keep Positron focused - typing will begin in 2 seconds...[/yellow]\n")
        time.sleep(2)

        if self.config.frontmatter:
            self.engine.type_text(self.config.frontmatter)
            if not self.config.frontmatter.endswith('\n'):
                self.engine.type_text('\n')

        for i, block in enumerate(self.config.blocks, 1):
            self.console.print(f"\n[dim]Typing block {i}/{len(self.config.blocks)}: {block.name}[/dim]")

            code = block.code
            if not code.endswith('\n'):
                code += '\n'
            self.engine.type_text(code)

            if i < len(self.config.blocks):
                time.sleep(block.pause_after)

        self.console.print("\n[green]✓ Typing complete![/green]")

        if self.formatter:
            self.console.print("\n[cyan]Formatting code...[/cyan]")
            time.sleep(1)
            self.formatter.format_file(self.config.output_file)

        self.console.print(f"[green]Code typed into: {self.config.output_file}[/green]")

        if self.config.is_shiny and self.execute_enabled:
            self.executor.execute_shiny(self.config.output_file, self.config.browser_command)

    def _run_terminal_mode(self):
        """Run in terminal mode - type to terminal with optional execution."""
        self._display_welcome()
        self._display_controls()

        self.writer.open()

        if self.config.frontmatter:
            self.writer.write_chunk(self.config.frontmatter)
            if not self.config.frontmatter.endswith('\n'):
                self.writer.write_chunk('\n')

        for i, block in enumerate(self.config.blocks, 1):
            if self.engine.quit:
                break

            self._display_block_header(i, len(self.config.blocks), block)

            typed_code = self._type_block(block)

            if self.engine.quit:
                break

            if block.execute and self.execute_enabled and block.type == 'code' and not self.config.is_shiny:
                self._execute_block(block, typed_code)

            if i < len(self.config.blocks) and not self.engine.quit:
                time.sleep(block.pause_after)

        if not self.engine.quit:
            self.writer.finalize(self.console)

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

        self.engine.setup_terminal()
        try:
            typed = self.engine.type_text(code, self._get_syntax(block))
        finally:
            self.engine.restore_terminal()

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

    def _detect_screen_device(self):
        """Return the avfoundation index of the screen capture device, or None."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-f", "avfoundation",
                 "-list_devices", "true", "-i", ""],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except Exception:
            return None

        # Device list is printed to stderr. Lines look like:
        #   [AVFoundation indev @ 0x...] [2] Capture screen 0
        # Only parse the video device section, since audio uses its own indices.
        in_video_section = False
        for line in result.stderr.splitlines():
            if "AVFoundation video devices:" in line:
                in_video_section = True
                continue
            if "AVFoundation audio devices:" in line:
                in_video_section = False
                continue
            if in_video_section and "capture screen" in line.lower():
                match = re.search(r"\[(\d+)\]", line.split("]", 1)[1])
                if match:
                    return match.group(1)
        return None

    def _start_recording(self):
        self.record_process = None
        if not self.config.record:
            return

        import shutil
        import sys
        if not shutil.which("ffmpeg"):
            self.console.print(Panel(
                "[bold red]FFmpeg is not installed or not in PATH![/bold red]\n\n"
                "Automatic screen recording requires FFmpeg.\n"
                "To install it on macOS, run:\n"
                "  [cyan]brew tap homebrew-ffmpeg/ffmpeg[/cyan]\n"
                "  [cyan]brew install homebrew-ffmpeg/ffmpeg/ffmpeg[/cyan]",
                title="Recording Error",
                border_style="red"
            ))
            sys.exit(1)

        device = self.config.record_device
        if device is None:
            device = self._detect_screen_device()
            if device is None:
                self.console.print(Panel(
                    "[bold red]Could not auto-detect a screen capture device![/bold red]\n\n"
                    "Run [cyan]ffmpeg -f avfoundation -list_devices true -i \"\"[/cyan] to list devices,\n"
                    "then pass the screen's index explicitly, e.g. [cyan]--record-device 2[/cyan].\n\n"
                    "If no [yellow]\"Capture screen\"[/yellow] device is listed, grant your terminal app\n"
                    "Screen Recording permission in System Settings → Privacy & Security.",
                    title="Recording Error",
                    border_style="red"
                ))
                sys.exit(1)

        cmd = [
            "ffmpeg",
            "-f", "avfoundation",
            "-framerate", "30",
            "-i", device,
            "-pix_fmt", "yuv420p",
            "-r", "30",
            "-c:v", "h264_videotoolbox",
            "-q:v", "80",
            "-y",
            self.config.record_output
        ]
        self.console.print(f"[cyan]Starting screen recording to {self.config.record_output}...[/cyan]")
        try:
            self.record_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True
            )
            time.sleep(1.5)
            ret = self.record_process.poll()
            if ret is not None:
                stderr_text = self.record_process.stderr.read()
                self.console.print(Panel(
                    f"[bold red]FFmpeg exited immediately with code {ret}![/bold red]\n\n"
                    f"[yellow]Error Details:[/yellow]\n{stderr_text.strip()}\n\n"
                    "[bold]Potential Solutions:[/bold]\n"
                    "1. [bold]Screen Recording Permission[/bold]: macOS requires permissions for your terminal app to capture the screen.\n"
                    "   Go to: System Settings → Privacy & Security → Screen Recording and check your terminal app.\n"
                    "2. [bold]Invalid Device Index[/bold]: Your specified device index may be incorrect.\n"
                    "   Run: [cyan]ffmpeg -f avfoundation -list_devices true -i \"\"[/cyan] to see your devices.",
                    title="Recording Failed to Start",
                    border_style="red"
                ))
                sys.exit(1)
        except Exception as e:
            self.console.print(f"[red]Failed to start screen recording: {e}[/red]")
            sys.exit(1)

    def _stop_recording(self):
        if hasattr(self, 'record_process') and self.record_process:
            self.console.print("[cyan]Stopping screen recording...[/cyan]")
            try:
                self.record_process.communicate(input=b'q', timeout=5)
            except Exception:
                try:
                    self.record_process.terminate()
                except Exception:
                    pass
            self.console.print(f"[green]Screen recording saved to {self.config.record_output}[/green]")
            self.record_process = None
