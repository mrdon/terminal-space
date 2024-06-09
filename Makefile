.PHONY: run tunnel client help bin release

# Help system from https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

clean:
	rm -rf dist build *.egg-info __pycache__

format: ## Format the imports and code
	echo Formatting code
	pdm run black -l 88 -t py37 tspace

pyenv: ## Create a virtualenv
	pdm install -d

run: ## Run the app
	pdm run python -m tspace.client_app

run-server: ## Run the standalone server, needed for joining a game
	pdm run tspace/server_app.py

run-docker: ## Run the app in a docker container
	docker build -t tspace .
	echo "Run the app with:\n\ndocker run -it tspace"

bin: ## Build a single file distribution
	pdm export -o requirements.txt --without-hashes --prod
	#pdm run pyinstaller tspace-server.spec
	pdm run pyinstaller tspace-client.spec
	echo "Run the app with:\n\ndist/tspace-client"

release: clean  ## Release the game to pypi
	pdm run bump2version release --allow-dirty
	pdm run python setup.py sdist
	pdm run python setup.py bdist_wheel
	pdm run twine upload dist/*
	pdm run bump2version --no-tag patch
	git push origin master --tags
