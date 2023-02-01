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

clean: ## Clean package
	find . -type d -name '__pycache__' | xargs rm -rf
	find . -type d -name '.temp' | xargs rm -rf
	find . -type f -name '.coverage' | xargs rm -rf
	rm -rf build dist

deps: ## Install/Update dependencies
	poetry update
	poetry run pre-commit autoupdate
