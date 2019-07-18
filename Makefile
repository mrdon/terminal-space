.PHONY: run tunnel client help bin release

# Help system from https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

clean:
	rm -r dist

format: ## Format the imports and code
	echo Formatting code
	venv/bin/black -l 88 -t py37 pytw pytw_textui json_types *.py

virtualenv: ## Create a virtualenv
	python3.7 -m venv venv
	venv/bin/pip install -r requirements.dev.txt

run: ## Run the app
	venv/bin/python pytw/client_app.py

run-server: ## Run the standalone server, needed for joining a game
	venv/bin/python pytw/server_app.py

run-docker: ## Run the app in a docker container
	docker build -t pytw .
	echo "Run the app with:\n\ndocker run -it pytw"

bin: ## Build a single file distribution
	venv/bin/pyinstaller --onefile pytw-server.spec
	venv/bin/pyinstaller --onefile pytw-client.spec
	echo "Run the app with:\n\ndist/pytw-client"

release: clean  ## Release the game to pypi
	bumpversion release --allow-dirty
	python setup.py sdist
	python setup.py bdist_wheel
	twine upload dist/*
	bumpversion --no-tag patch
	git push origin master --tags
