# Migrate to uv for Dependency Management

## Goal

Replace tox + pip-compile with uv. Clean separation between package and developer dependencies using PEP 735 dependency groups. Single tool for dependency resolution, locking, and running commands.

## Decisions

- **Build backend**: Keep hatchling + hatch-vcs (uv_build doesn't support dynamic git tag versioning yet)
- **Drop**: hatch-fancy-pypi-readme (only used to include README.md, replaceable with static `readme` field)
- **Dependency groups**: PEP 735 `[dependency-groups]` for all dev tooling; `sqlmodels` stays as optional dependency (user-facing)
- **CI**: Update GitHub Actions to use `astral-sh/setup-uv` + `uv run` directly
- **Release**: `uv build` replaces `python -m build` + `twine`; keep trusted publisher for upload
- **Python versions**: Keep current setup (test on 3.13, publish on 3.12, requires >=3.11)
- **Pre-commit**: Developers run `uv sync && pre-commit install` manually

## Changes

### pyproject.toml

1. Remove `hatch-fancy-pypi-readme` from `[build-system].requires`
2. Change `dynamic = ["readme", "version"]` to `dynamic = ["version"]`, add `readme = "README.md"`
3. Remove all dev-only optional extras (test, lint, typecheck, formatting, spell_check, coverage, test_packaging, dev)
4. Keep `sqlmodels` as optional dependency
5. Add `[dependency-groups]` section:
   - `test`: pytest, coverage, pytest-datafiles, syrupy, freezegun, dictdiffer, sqlmodel, sqlalchemy[mypy]
   - `lint`: pylint, pylint-pydantic
   - `typecheck`: mypy, pandas-stubs, pytest, types-freezegun, types-requests, networkx-stubs, sqlmodel, sqlalchemy[mypy]
   - `spelling`: codespell
   - `formatting`: black, isort
   - `dev`: includes all above groups
6. Remove `[tool.hatch.metadata.hooks.fancy-pypi-readme]` section

### Files to delete

- `tox.ini`
- `requirements.txt`

### Files generated

- `uv.lock` (via `uv lock`)

### .github/workflows/checks.yaml

- Replace tox with `astral-sh/setup-uv`
- Steps: `uv sync --group dev`, then individual `uv run` commands for pytest, pylint, mypy, black, isort, codespell

### .github/workflows/python-publish.yml

- Use `astral-sh/setup-uv`
- Replace `python -m build` with `uv build`
- Remove `twine` check, keep trusted publisher upload action

### No changes

- `.github/workflows/conventional-commit-check.yml`
- `.github/workflows/dependabot_automerge.yml`
- `.pre-commit-config.yaml`
- All `[tool.*]` config sections in pyproject.toml
