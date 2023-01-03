setup:
	poetry install
	poetry run pre-commit install
	poetry shell

black:
	poetry run black .

bandit:
	poetry run bandit -c pyproject.toml -r search_cli/

test:
	poetry run pytest

cicd: black bandit test

oracle:
	poetry run python search_cli/cli/main.py
