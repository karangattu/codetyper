"""Configuration schema for CodeTyper."""

from dataclasses import dataclass
from typing import List, Optional, Literal


@dataclass
class CodeBlock:
    """Represents a single code block to be typed.

    A code block corresponds to a section marked with `##` headers in
    your script file. Each block can have its own execution and timing settings.

    Parameters
    ----------
    name : str
        Display name of the block (from the `##` header)
    code : str
        The actual code content to type
    description : Optional[str]
        Optional description (not currently used)
    execute : bool
        Whether to execute this block after typing (default: True)
    pause_after : float
        Seconds to pause after typing this block (default: 1.0)
    type : Literal['code', 'markdown']
        Block type (default: 'code')
    language : Optional[str]
        Language for this specific block (if different from main config)

    Examples
    --------
    >>> block = CodeBlock(
    ...     name="Import libraries",
    ...     code="import pandas as pd",
    ...     execute=True,
    ...     pause_after=1.5
    ... )
    """
    name: str
    code: str
    description: Optional[str] = None
    execute: bool = True
    pause_after: float = 1.0
    type: Literal['code', 'markdown'] = 'code'
    language: Optional[str] = None


@dataclass
class Config:
    """Main configuration for CodeTyper.

    This configuration controls all aspects of how CodeTyper types and
    executes your code. Created by parsing script files with YAML frontmatter.

    Parameters
    ----------
    language : Literal['r', 'python', 'quarto']
        Programming language of the code
    output_file : str
        Path where typed code will be saved
    typing_speed : float
        Seconds to wait between typing each character (default: 0.05)
    execute_blocks : bool
        Whether to execute code after typing in terminal mode (default: True)
    pause_between_blocks : float
        Seconds to pause between blocks (default: 2.0)
    blocks : List[CodeBlock]
        List of code blocks to type
    frontmatter : Optional[str]
        Raw frontmatter text (for Quarto files)
    mode : Literal['terminal', 'ide']
        Typing mode: 'terminal' or 'ide' (default: 'terminal')
    ide_path : Optional[str]
        Custom path to Positron.app (if not using default location)
    format_output : bool
        Whether to format output with Ruff/styler after typing (default: False)

    Examples
    --------
    >>> config = Config(
    ...     language='python',
    ...     output_file='demo.py',
    ...     typing_speed=0.05,
    ...     blocks=[...]
    ... )
    """
    language: Literal['r', 'python', 'quarto']
    output_file: str
    typing_speed: float = 0.05
    execute_blocks: bool = True
    pause_between_blocks: float = 2.0
    blocks: List[CodeBlock] = None
    frontmatter: Optional[str] = None
    mode: Literal['terminal', 'ide'] = 'terminal'
    ide_path: Optional[str] = None
    format_output: bool = False
    record: bool = False
    record_device: str = "1"
    record_output: str = "recording.mp4"
    browser_command: Optional[str] = None

    def __post_init__(self):
        if self.blocks is None:
            self.blocks = []

    @property
    def is_shiny(self) -> bool:
        full_code = "\n".join(b.code for b in self.blocks)
        if self.language == 'python':
            return "import shiny" in full_code or "from shiny" in full_code
        elif self.language == 'r':
            return "library(shiny)" in full_code or "require(shiny)" in full_code
        return False
