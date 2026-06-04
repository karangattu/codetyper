# CodeTyper Quick Start Guide

## What is CodeTyper?

CodeTyper types code character-by-character with a typewriter effect in your terminal. Perfect for recording coding tutorials with external screen recording software (QuickTime, OBS, etc.).

## Installation

```bash
pip install -e .
```

After installation, use the `codetyper` command instead of `python codetyper.py`.

## Try it now (1 minute)

### Option 1: Terminal Mode (type in terminal)

```bash
codetyper type-code examples/example_script.py
```

This will:
1. Show a welcome screen with controls
2. Type out Python code character-by-character in the terminal
3. Execute the code and show output
4. Save to `demo_from_script.py`

### Option 2: IDE Mode (type into Positron)

**Python example:**
```bash
codetyper type-code examples/example_script.py --ide
```

**R example:**
```bash
codetyper type-code examples/example_script.R --ide
```

This will:
1. Create a blank file at the output location
2. Open the blank file in Positron IDE
3. Type the code from your script character-by-character into the editor
4. The typed code is saved to the output location specified in the script's frontmatter

**How it works:**
- Your source script (`example_script.py` or `example_script.R`) contains the code with YAML frontmatter and `##` headers
- The output file gets only the pure code (no frontmatter, no headers) typed into it
- Perfect for recording tutorials that look like live coding!

**Note:** IDE mode requires accessibility permissions on macOS. If you get an error, go to:
System Settings → Privacy & Security → Accessibility and enable permissions for your terminal app.

### Option 3: Create your own

```bash
# Generate a template
codetyper init python -o my_tutorial.py
# Or for R: codetyper init r -o my_tutorial.R

# Edit my_tutorial.py with your code (use any text editor)

# Run it in terminal mode
codetyper type-code my_tutorial.py

# Or run it in IDE mode
codetyper type-code my_tutorial.py --ide
```

## Script File Format

CodeTyper uses R or Python script files with YAML frontmatter and markdown headers:

```python
---
language: python
output_file: demo.py
typing_speed: 0.05
execute_blocks: true
---

## Import libraries
import pandas as pd

## Load data | pause_after=1.5
df = pd.read_csv('data.csv')

## Process | execute=true, pause_after=2.0
print(df.head())
```

**Key features:**
- **YAML frontmatter** at the top (between `---` delimiters) for configuration
- **Markdown headers** (`##`) mark the start of each code block
- **Optional settings** after block names: `| execute=false, pause_after=2.0`
- The output file contains only the code (no headers or frontmatter)

## Keyboard Controls (Terminal Mode only)

- **SPACE**: Pause/resume
- **↑**: Speed up
- **↓**: Slow down  
- **→**: Skip current block
- **Q or ESC**: Quit

**Note:** Keyboard controls are not available in IDE mode. Once typing starts in Positron, it will complete all blocks automatically.

## For Recording Tutorials

1. **Prepare**: Create your script file with the code you want to type
2. **Test**: Run CodeTyper once to verify it works
3. **Setup**: Start your screen recording software
4. **Record**: Run CodeTyper and let it type your tutorial
5. **Done**: Stop recording when CodeTyper finishes

## Examples Included

- `examples/example_script.py` - Python with pandas
- `examples/example_script.R` - R with ggplot2

## Common Options

```bash
# Type faster
codetyper type-code my_script.py --speed 0.02

# Type into Positron IDE
codetyper type-code my_script.py --ide

# Format output with Ruff (Python) or styler (R)
codetyper type-code my_script.py --format

# Combine IDE mode with formatting
codetyper type-code my_script.py --ide --format

# Don't execute code (just type it) - terminal mode only
codetyper type-code my_script.py --no-execute

# Save to different location
codetyper type-code my_script.R -o /path/to/output.R

# Use different Positron path
codetyper type-code my_script.py --ide --ide-path /custom/path/to/Positron.app
```

## Tips

### General
- Start with `typing_speed: 0.05` (normal speed)
- Use `typing_speed: 0.02` for faster demos
- Test run before recording

### Terminal Mode
- Set `execute: false` for plot code (won't display in terminal)
- Increase terminal font size for better visibility
- Use keyboard controls to adjust speed on the fly

### IDE Mode
- Make sure Positron window stays focused during typing
- Grant accessibility permissions before first use
- Code is typed into the editor but not automatically executed
- Perfect for recording demos that look like real coding sessions
- The source script (with frontmatter and headers) is your "script", the output file is what gets typed
- Use `--format` to auto-format the output file after typing completes

### Formatting
- Use `--format` flag to automatically format output after typing
- **Python**: Uses Ruff (`pip install ruff`)
- **R**: Uses styler package (`install.packages("styler")`)
- Gracefully skips formatting if formatter is not installed

## Next Steps

See [README.md](README.md) for complete documentation including:
- Detailed configuration options
- Quarto document support
- Error handling
- Troubleshooting
- Advanced usage

## Get Help

```bash
codetyper --help
codetyper type-code --help
codetyper init --help
```

## Workflow Example

Here's a typical workflow for creating a coding tutorial:

1. **Create your script with content:**
   ```bash
   codetyper init python -o tutorial.py
   # Edit tutorial.py - add your code between ## headers
   ```

2. **Test in terminal mode:**
   ```bash
   codetyper type-code tutorial.py
   # Verify the code works and timing is good
   ```

3. **Record with IDE mode:**
   ```bash
   # Start screen recording (QuickTime, OBS, etc.)
   codetyper type-code tutorial.py --ide --output demo.py
   # tutorial.py = your script with headers (the "script")
   # demo.py = blank file that gets typed into (the "output")
   ```

4. **The result:** A video of code being typed into Positron, creating `demo.py`

## Choosing Between Terminal and IDE Mode

**Use Terminal Mode when:**
- You want to see code execution results in real-time
- You need keyboard controls to pause or adjust speed
- You're recording a terminal-based tutorial
- You want automatic code execution

**Use IDE Mode when:**
- You want to show realistic typing in Positron IDE
- You're creating a tutorial that demonstrates IDE features
- You want the code to appear as if you're typing it live
- You prefer to execute code manually after typing

Enjoy creating beautiful code tutorials! 🎬
