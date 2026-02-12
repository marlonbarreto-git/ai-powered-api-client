.PHONY: install test lint format typecheck clean

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --tb=short

lint:
	ruff check src/api_client/ tests/

format:
	ruff format src/api_client/ tests/

typecheck:
	mypy src/api_client/

clean:
	rm -rf .mypy_cache .ruff_cache .pytest_cache __pycache__ dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
