# CodeTyper

Create realistic typing demonstrations for coding tutorials. Types code character-by-character into your terminal or directly into Positron IDE, perfect for screen recording.

## Features

- ⌨️ **Typewriter effect**: Character-by-character typing with configurable speed
- 🎨 **Two modes**: Type in terminal or directly into Positron IDE
- 🎮 **Keyboard controls**: Pause, speed up/down, skip blocks (terminal mode)
- ▶️ **Optional execution**: Run R or Python code blocks after typing (terminal mode)
- 📝 **Script-based**: Use actual .R or .py files with YAML frontmatter
- 🏷️ **Markdown headers**: Organize code into blocks with `##` headers
- 🔧 **Per-block settings**: Configure execution and timing for each block

## Installation

### Quick Install

```bash
pip install -e .
```

This installs codetyper as a command-line tool. After installation, use `codetyper` instead of `python codetyper.py`.

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

### Dependencies

- rich>=13.0.0
- PyYAML>=6.0
- typer>=0.9.0

## Quick Start

### 1. Create a script file

Use the `init` command to create a template:

```bash
codetyper init python -o my_tutorial.py
# Or for R: codetyper init r -o my_tutorial.R
```

Or use one of the examples:
- `examples/example_script.py` - Python with pandas
- `examples/example_script.R` - R with ggplot2

### 2. Run CodeTyper

**Terminal mode** (types in your terminal):
```bash
codetyper type-code examples/example_script.py
```

**IDE mode** (types into Positron):
```bash
codetyper type-code examples/example_script.py --ide
```

### 3. Record your tutorial

Either use external recording software (QuickTime, OBS, etc.), or enable automatic screen recording with FFmpeg:
```bash
codetyper type-code examples/example_script.py --record
```
*Note: Automatic recording requires FFmpeg (`brew install homebrew-ffmpeg/ffmpeg/ffmpeg`) and macOS Screen Recording permissions enabled for your terminal.*

## Usage

### Basic command

```bash
codetyper type-code <script-file.py>
```

### With options

```bash
# Type into Positron IDE
codetyper type-code my_script.py --ide

# Format output with Ruff (Python) or styler (R)
codetyper type-code my_script.py --format

# Combine IDE mode with formatting
codetyper type-code my_script.py --ide --format

# Override typing speed (faster)
codetyper type-code my_script.py --speed 0.02

# Disable code execution (terminal mode only)
codetyper type-code my_script.py --no-execute

# Override output file
codetyper type-code my_script.R -o /path/to/output.R

# Record screen automatically to recording.mp4
codetyper type-code my_script.py --record

# Customize recording output and input device index
# (the screen capture device is auto-detected; only override if needed)
codetyper type-code my_script.py --record --record-output demo.mp4 --record-device 2
```

### Terminal Mode vs IDE Mode

**Terminal Mode:**
- Types code in the terminal with syntax highlighting
- Optionally executes code blocks and shows output
- Keyboard controls available (pause, speed up/down, skip)
- Perfect for terminal-based tutorials

**IDE Mode:**
- Opens Positron IDE with a blank file
- Types code character-by-character into the editor
- Creates realistic "live coding" demonstrations
- Requires macOS accessibility permissions

## Keyboard Controls (Terminal Mode)

While CodeTyper is running in terminal mode:

- **SPACE**: Pause/resume typing
- **↑ (Up Arrow)**: Speed up (1.5x → 2x → 3x)
- **↓ (Down Arrow)**: Slow down (0.75x → 0.5x)
- **→ (Right Arrow)**: Skip current block (prints remaining text instantly)
- **Q or ESC**: Quit

## Script File Format

CodeTyper uses R or Python script files with YAML frontmatter and markdown headers.

### Basic structure

```python
---
language: python               # python or r
output_file: demo.py          # Where to save the typed code
typing_speed: 0.05            # Seconds per character
execute_blocks: true          # Execute code in terminal mode
---

## Block name
# Your code here
import pandas as pd

## Another block | pause_after=2.0
# More code
df = pd.read_csv('data.csv')
```

### R example

```r
---
language: r
output_file: demo.R
typing_speed: 0.05
execute_blocks: true
---

## Setup
library(ggplot2)
library(dplyr)

## Analysis | execute=false, pause_after=2.0
df <- data.frame(x = 1:10, y = (1:10)^2)
ggplot(df, aes(x, y)) + geom_line()
```

### Python example

```python
---
language: python
output_file: demo.py
typing_speed: 0.04
execute_blocks: true
---

## Import libraries
import pandas as pd
from plotnine import ggplot, aes, geom_line

## Create plot | execute=false
df = pd.DataFrame({'x': range(10), 'y': [i**2 for i in range(10)]})
(ggplot(df, aes('x', 'y')) + geom_line())
```

### Block Settings

You can add settings to individual blocks using the pipe syntax:

```python
## Block name | execute=false, pause_after=2.0
```

Available settings:
- `execute=true/false` - Whether to execute this block (terminal mode only)
- `pause_after=1.5` - Seconds to pause after typing this block

### Frontmatter Options

```yaml
---
language: python           # python or r (required)
output_file: demo.py      # Output file path (required)
typing_speed: 0.05        # Seconds per character (default: 0.05)
execute_blocks: true      # Execute in terminal mode (default: true)
mode: terminal            # terminal or ide (default: terminal)
ide_path: /path/to/Positron.app  # Custom Positron path (optional)
format_output: false      # Format with Ruff/styler after typing (default: false)
---

## Code Formatting

CodeTyper can automatically format your output files after typing completes using `--format`:

### Python (Ruff)
```bash
pip install ruff
python codetyper.py type-code my_script.py --format
```

### R (styler)
```r
install.packages("styler")
```
```bash
python codetyper.py type-code my_script.R --format
```

**Why format after typing?**
- IDE auto-formatting can interfere with character-by-character typing
- Formatting after ensures clean, properly-styled output
- Especially useful with IDE mode where Positron's formatter might trigger

If the formatter isn't installed, CodeTyper will skip formatting gracefully.

## IDE Mode Setup (macOS)

To use IDE mode, you need to grant accessibility permissions:

1. Open **System Settings** → **Privacy & Security** → **Accessibility**
2. Click the lock icon to make changes
3. Find your terminal app (Terminal, iTerm2, etc.) in the list
4. Enable the checkbox next to it
5. Restart your terminal

Once permissions are granted, CodeTyper can send keystrokes to Positron.

## Tips for Recording

### General
1. **Test first**: Run through your script once before recording
2. **Speed**: Start with 0.05s per character, adjust as needed
3. **Output validation**: The typed file will match exactly what's typed

### Terminal Mode
1. **Terminal size**: Make sure your terminal is sized appropriately for recording
2. **Font size**: Increase terminal font size for better visibility
3. **Dark theme**: Usually records better than light themes
4. **Practice keyboard controls**: Get comfortable with SPACE and arrow keys

### IDE Mode
1. **Keep focused**: Positron window must stay focused during typing
2. **Clean workspace**: Close unnecessary panels for cleaner recording
3. **Test permissions**: Make sure accessibility permissions are granted
4. **Font size**: Adjust Positron editor font size for visibility

## Examples

### Record an R tutorial

```bash
# 1. Create template
codetyper init r -o r_tutorial.R

# 2. Edit r_tutorial.R with your code

# 3. Test run (no recording)
codetyper type-code r_tutorial.R

# 4. Start QuickTime screen recording

# 5. Run for recording
codetyper type-code r_tutorial.R
```

### Fast Python demo

```bash
codetyper type-code examples/example_script.py --speed 0.02
```

### Python script (no execution)

```bash
codetyper type-code my_script.py --no-execute
```

## Troubleshooting

### Terminal gets corrupted after crash

If CodeTyper exits unexpectedly and your terminal looks broken:

```bash
reset
```

Or close and reopen the terminal.

### Code execution fails

- Ensure R (via `Rscript`) or Python 3 is in your PATH
- Check that required packages are installed
- Use `execute: false` for blocks that shouldn't run (like plots)
- Check execution output for error messages

### Keyboard controls not working

- Make sure you're running in a real terminal (not a script or cron job)
- Some terminal emulators may have different key bindings
- Try Q instead of ESC if escape key doesn't work

### File not being created

- Check that the output directory exists or can be created
- Verify you have write permissions
- Check for typos in the output_file path

## Advanced Usage

### Variable speed by block

Different blocks can have different speeds by running multiple configs or using speed multipliers during typing.

### Multiple files

Create separate configurations for each file and run them sequentially.

### Complex workflows

For multi-file projects, create a shell script that runs multiple CodeTyper commands in sequence.

## Development

The codebase is modular and organized:

```
src/codetyper/
├── __init__.py      # Package initialization
├── __main__.py      # python -m codetyper support
├── app.py           # Main application orchestrator
├── cli.py           # Command-line interface
├── config.py        # Configuration dataclasses
├── engine.py        # Typing engines (terminal & IDE)
├── exceptions.py    # Custom exceptions
├── executor.py      # Code execution
├── formatter.py     # Code formatting
├── parser.py        # Config file parsers
├── templates.py     # Script templates
└── writer.py        # File writing
```

See [INSTALL.md](INSTALL.md) for development setup instructions.

## License

Built with Claude Code for creating beautiful coding tutorials.
