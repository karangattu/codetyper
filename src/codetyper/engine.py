"""Typing engines for terminal and IDE modes."""

import sys
import time
import select
import tty
import termios
import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console

from codetyper.exceptions import ExecutionError


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
            self.old_terminal_settings = None

    def restore_terminal(self):
        """Restore terminal to normal mode."""
        if self.old_terminal_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_terminal_settings)

    def _check_keyboard_input(self) -> Optional[str]:
        """Non-blocking keyboard input check."""
        if not self.old_terminal_settings:
            return None
        try:
            if select.select([sys.stdin], [], [], 0)[0]:
                return sys.stdin.read(1)
        except (OSError, ValueError):
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
                self.quit = True
        elif key.lower() == 'q':
            self.quit = True

    def type_text(self, text: str, syntax: str = "python") -> str:
        """Types text character-by-character with syntax highlighting."""
        accumulated = ""

        for i, char in enumerate(text):
            key = self._check_keyboard_input()
            if key:
                self._handle_key(key)

            if self.quit or self.skip_block:
                break

            while self.paused and not self.quit:
                key = self._check_keyboard_input()
                if key:
                    self._handle_key(key)
                time.sleep(0.01)

            accumulated += char
            if char == '\n' and self.old_terminal_settings:
                sys.stdout.write('\r\n')
            else:
                sys.stdout.write(char)
            sys.stdout.flush()

            time.sleep(self.speed * self.speed_multiplier)

        if self.skip_block and not self.quit:
            remaining = text[len(accumulated):]
            if self.old_terminal_settings:
                sys.stdout.write(remaining.replace('\n', '\r\n'))
            else:
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
        file_path_obj = Path(file_path)
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)
        file_path_obj.write_text('')

        self.output_file = file_path_obj
        self.console.print(f"[cyan]Opening {file_path} in Positron...[/cyan]")

        try:
            subprocess.run([self.positron_cli, str(file_path), "-n"], check=True)
        except FileNotFoundError:
            raise ExecutionError(
                f"Positron not found at {self.ide_path}. "
                "Please install Positron or specify the correct path with --ide-path."
            )

        time.sleep(2)
        self.activate_positron()
        time.sleep(1.5)
        self.toggle_zen_mode()
        time.sleep(1.0)

    def activate_positron(self):
        applescript = 'tell application "Positron" to activate'
        subprocess.run(["osascript", "-e", applescript], check=True)

    def toggle_zen_mode(self):
        applescript = (
            'tell application "System Events"\n'
            '    tell process "Positron"\n'
            '        set frontmost to true\n'
            '        keystroke "k" using command down\n'
            '        delay 0.5\n'
            '        keystroke "z"\n'
            '    end tell\n'
            'end tell'
        )
        try:
            subprocess.run(["osascript", "-e", applescript], check=True,
                         capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            self.console.print(f"Warning: Failed to toggle Zen Mode: {e.stderr}")

    def type_keystroke(self, char: str):
        """Type a single character into Positron."""
        if char == '\n':
            applescript = 'tell application "System Events" to keystroke return'
        elif char == '\t':
            applescript = 'tell application "System Events" to keystroke tab'
        elif char == '\\':
            applescript = 'tell application "System Events" to keystroke "\\\\"'
        elif char == '"':
            applescript = 'tell application "System Events" to keystroke "\\"" using shift down'
        else:
            escaped = char.replace('\\', '\\\\').replace('"', '\\"')
            applescript = f'tell application "System Events" to keystroke "{escaped}"'

        try:
            subprocess.run(["osascript", "-e", applescript], check=True,
                         capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
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
            self.console.print(f"[yellow]Warning: Failed to type character '{char}': {e.stderr}[/yellow]")

    def type_text(self, text: str, syntax: str = None) -> str:
        """Types text character-by-character by writing to file (avoids auto-indent)."""
        if not self.output_file:
            for char in text:
                self.type_keystroke(char)
                time.sleep(self.speed)
            return text

        current_content = self.output_file.read_text()

        for char in text:
            current_content += char
            self.output_file.write_text(current_content)
            time.sleep(self.speed)

        return text

    def setup_terminal(self):
        """No-op for IDE mode."""
        pass

    def restore_terminal(self):
        """No-op for IDE mode."""
        pass
