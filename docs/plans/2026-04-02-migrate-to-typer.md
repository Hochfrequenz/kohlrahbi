# Migrate CLI from Click to Typer with Rich UX

## Goal

Replace click with typer for the CLI framework. Improve user experience with rich progress bars and summary panels. Default to clean output with `--verbose` flag for debug logging.

## Decisions

- **Framework**: typer[all] (bundles rich)
- **Progress**: rich.progress bars showing file-level progress
- **Summary**: Rich panel at end showing files processed, output path, warnings
- **Logging**: Default WARNING level (quiet), --verbose enables DEBUG with RichHandler
- **Command structure**: Unchanged (ahb, conditions, changehistory docx/bnetza, qualitymap)
- **Remove**: colorlog dependency (replaced by rich)

## Changes

### pyproject.toml
- Replace `click>=8.1.7` with `typer[all]>=0.15.0`
- Remove `colorlog>=6.9.0`

### src/kohlrahbi/__init__.py
- Replace click.group with typer.Typer app
- Add version callback

### src/kohlrahbi/logger.py
- Add `setup_logging(verbose: bool)` function
- Default: WARNING level, suppresses info spam
- Verbose: DEBUG level with RichHandler

### Command files (ahb, conditions, changehistory, qualitymap)
- Replace @click decorators with typer commands
- Add --verbose flag to each command
- Wrap scraping calls with rich progress tracking
- Add summary panel on completion

### Scraping functions
- Minimal changes: pass progress callback where needed for file-level tracking
