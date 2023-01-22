setup:
	poetry install
	poetry run pre-commit install
	poetry shell

black:
	poetry run black .

bandit:
	poetry run bandit -c pyproject.toml -r oracle_of_ammon/

test:
	poetry run pytest

cicd: black bandit test
