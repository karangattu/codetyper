"""Code execution functionality."""

import subprocess
import time
from typing import Tuple, Optional

from rich.console import Console
from rich.panel import Panel


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
