"""Configuration file parsers."""

from pathlib import Path
import yaml

from codetyper.config import Config, CodeBlock
from codetyper.exceptions import ConfigurationError


def parse_script_file(script_file: Path) -> Config:
    """Parse an R or Python script file with YAML frontmatter and markdown headers."""
    try:
        with open(script_file) as f:
            content = f.read()

        if not content.startswith('---'):
            raise ConfigurationError(
                "Script file must start with YAML frontmatter between --- delimiters.\n"
                "Example:\n"
                "---\n"
                "language: python\n"
                "output_file: demo.py\n"
                "---\n"
            )

        parts = content.split('---', 2)
        if len(parts) < 3:
            raise ConfigurationError("Missing closing --- for YAML frontmatter")

        frontmatter_text = parts[1].strip()
        code_content = parts[2].lstrip('\n')

        try:
            metadata = yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML frontmatter: {e}")

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

        output_file = metadata.get('output_file')
        if not output_file:
            output_file = str(script_file)


        blocks = []
        lines = code_content.split('\n')
        current_block_name = None
        current_block_code = []
        current_block_settings = {}

        for line in lines:
            stripped = line.strip()

            if stripped.startswith('##') and not stripped.startswith('###'):
                if current_block_name is not None:
                    blocks.append(CodeBlock(
                        name=current_block_name,
                        code='\n'.join(current_block_code),
                        execute=current_block_settings.get('execute', True),
                        pause_after=current_block_settings.get('pause_after', 1.0),
                    ))

                header = stripped[2:].strip()

                if '|' in header:
                    block_name, settings_str = header.split('|', 1)
                    current_block_name = block_name.strip()

                    current_block_settings = {}
                    for setting in settings_str.split(','):
                        setting = setting.strip()
                        if '=' in setting:
                            key, value = setting.split('=', 1)
                            key = key.strip()
                            value = value.strip()

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
                if current_block_name is None:
                    current_block_name = "Code"
                    current_block_settings = {}

                current_block_code.append(line)

        if current_block_name is not None and current_block_code:
            blocks.append(CodeBlock(
                name=current_block_name,
                code='\n'.join(current_block_code),
                execute=current_block_settings.get('execute', True),
                pause_after=current_block_settings.get('pause_after', 1.0),
            ))

        if not blocks:
            raise ConfigurationError("No code blocks found in script file")

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

        blocks = []
        for block_data in blocks_data:
            blocks.append(CodeBlock(**block_data))

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
