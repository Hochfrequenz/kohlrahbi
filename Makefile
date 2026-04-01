.PHONY: test lint formatting typecheck spelling check

test:
	uv run --group test pytest --cov kohlrahbi --cov-report term-missing --cov-fail-under 79

lint:
	uv run --group lint pylint src/kohlrahbi

formatting:
	uv run --group formatting black --check src/kohlrahbi unittests
	uv run --group formatting isort --check src/kohlrahbi unittests

typecheck:
	uv run --group typecheck mypy src/kohlrahbi unittests --strict

spelling:
	uv run --group spelling codespell src/kohlrahbi README.md

check: test lint formatting typecheck spelling
