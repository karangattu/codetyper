"""Configuration schema for CodeTyper."""

from dataclasses import dataclass
from typing import List, Optional, Literal


@dataclass
class CodeBlock:
    """Represents a single code block to be typed."""
    name: str
    code: str
    description: Optional[str] = None
    execute: bool = True
    pause_after: float = 1.0
    type: Literal['code', 'markdown'] = 'code'
    language: Optional[str] = None


@dataclass
class Config:
    """Main configuration for CodeTyper."""
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
