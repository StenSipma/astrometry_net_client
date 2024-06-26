PY=python3
PIP=pip
TEST=python3 -m pytest

# Override this variable (or any other) by using the --environment option:
#  $ PY_VERSION=3.8 make --environment type-check
PY_VERSION=3.12

PROJECT_NAME=astrometry_net_client

PROJ_FILES=$(PROJECT_NAME)/*.py $(PROJECT_NAME)/**/*.py 
TEST_FILES=tests/*.py
EXAMPLE_FILES=examples/*.py
CONFIG_FILES=setup.py
PY_FILES=$(PROJ_FILES) $(TEST_FILES) $(EXAMPLE_FILES) $(CONFIG_FILES)

TEST_FILTER=
# Add the following options for a testresults JUnit like xml report
#-o junit_family=xunit2 --junitxml="testresults.xml"
TEST_ARGS=--cov=$(PROJECT_NAME) --cov-report html -v -k '$(TEST_FILTER)'

PIP_IGNORE_PKG=--exclude pynvim --exclude astrometry_net_client

default: help

#default: check-in-venv dependencies format lint type-check install ## perform formatting and install

all: check-in-venv deps-package deps-dev format lint type-check install test documentation ## perform all checks, including formatting and testing

check-in-venv:
	env | grep 'VIRTUAL_ENV'

# Packaging
install: deps-package package package-install  ## package and install

package-install:
	$(PIP) install dist/$(PROJECT_NAME)-*.tar.gz

package:
	$(PY) -m build

# Uploading
upload-pypi: package
	pip install --upgrade twine
	python3 -m twine upload dist/*

upload-test: package
	pip install --upgrade twine
	python3 -m twine upload --repository testpypi dist/*

dependencies: deps-package deps-dev

deps-general:
	$(PIP) install --upgrade pip setuptools wheel pip-tools

deps-package: deps-general
	$(PIP) install --upgrade -r requirements.txt

# Dependencies for the development environment,
# e.g. contains Sphinx, flake8, black, isort etc.
deps-dev: deps-general ## Download development dependencies
	$(PIP) install --upgrade -r requirements.dev.txt


documentation: ## Generate the documentation
	make --directory=docs/ html


test: ## Run the default tests (not online & not long)
	$(TEST) $(TEST_ARGS) -m 'not online and not long' tests/

test-long: ## test, also include the tests which are longer (but not online)
	$(TEST) $(TEST_ARGS) -m 'not online' tests/

test-online: ## test, also include the tests which query the online api.
	$(TEST) $(TEST_ARGS) -m 'not long' tests/


test-all: ## test-online, also include the long tests (i.e. uploading files)
	$(TEST) $(TEST_ARGS)  tests/

help: ## Prints help for targets with comments
	@cat $(MAKEFILE_LIST) | grep -E '^[a-zA-Z_-]+:.*?## .*$$' | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

git-pre-push: check-format lint

## Formatting and linting
format: ## Format all the files using black and isort
	black $(PY_FILES)
	isort $(PY_FILES)

check-format: ## Only check if the formatting is correct
	# TODO: change this
	black --check $(PY_FILES)
	isort --check-only $(PY_FILES)

lint: ## Check the linting of all files
	flake8 $(PY_FILES)

type-check: ## Check Type annotations using MyPy
	mypy --python-version=$(PY_VERSION) $(PROJ_FILES) $(TEST_FILES) $(EXAMPLE_FILES)


## Cleanup rules
clean: clean-package clean-docs clean-reports  ## Cleanup all build files (like package, test results, documentation)

clean-package:
	-rm -r *.egg-info
	-rm -r build
	-rm -r dist

clean-docs:
	-make --directory=docs clean

clean-reports:
	-rm -r htmlcov
	-rm .coverage
	-rm testresults.xml

## Misc rules
virt-env:  ## Make a virtual environment
	python3 -m venv .env

deps-upgrade: setup.py requirements.dev.in  ## Run pip-compile
	pip-compile --upgrade
	pip-compile requirements.dev.in --upgrade


pip-freeze: ## Update requirements.txt and make a backup (for safety) of the current one
	mv requirements.txt requirements.txt.bak
	pip freeze $(PIP_IGNORE_PKG) > requirements.txt
