format:
	uvx ruff format

format-imports:
	uvx ruff check --select I --fix

run:
	uv run ./main.py
