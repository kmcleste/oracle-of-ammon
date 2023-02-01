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

pre-commit:
	poetry run pre-commit run --all-files

serve:
	poetry run mkdocs serve

deploy-docs:
	poetry run mkdocs gh-deploy

build:
	poetry build

bump: build
	poetry run cz bump --changelog
