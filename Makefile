PY=python3
PIP=pip
TEST=pytest

PROJECT_NAME=astrometry_net_client
PY_FILES=$(PROJECT_NAME)/*.py tests/*.py setup.py examples/*.py

TEST_ARGS=--cov --cov=$(PROJECT_NAME) --cov-report html -v

BLACK_ARGS=-l 79
ISORT_ARGS=--multi-line=3 --trailing-comma --force-grid-wrap=0 --use-parentheses --line-width=79
FLAKE_ARGS=--docstring-style=numpy


default: check-in-venv format lint install

all: default dependencies test documentation

check-in-venv:
	env | grep 'VIRTUAL_ENV'

# Packaging
install: dependencies package package-install

package-install: 
	$(PIP) install dist/$(PROJECT_NAME)-*.tar.gz

package: 
	$(PY) setup.py sdist bdist_wheel

# Uploading
upload-test: package
	python3 -m twine upload --repository testpypi dist/*

# Dependencies for the development environment, 
# e.g. contains Sphinx, flake8, black, isort etc.
dependencies:
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install --upgrade -r requirements.txt

# Generate the documentation
documentation:
	make --directory=docs/ html

## Testing. The default test does not include the online tests 
test:
	$(TEST) $(TEST_ARGS) -m 'not online or not long' tests/

# Includes all tests, so also those that query the actual api.
test-all:
	$(TEST) $(TEST_ARGS) -m 'not long' tests/

## Formatting and linting
format:
	black $(BLACK_ARGS) $(PY_FILES)
	isort $(ISORT_ARGS) $(PY_FILES)

check-format:
	black --check $(BLACK_ARGS) $(PY_FILES)
	isort --check-only $(ISORT_ARGS) $(PY_FILES)

lint:
	flake8 $(FLAKE_ARGS) $(PY_FILES)

## Cleanup
clean: clean-package clean-docs clean-reports

clean-package:
	-rm -r *.egg-info 
	-rm -r build 
	-rm -r dist

clean-docs:
	make --directory=docs clean

clean-reports:
	-rm -r htmlcov
	-rm .coverage

virt-env:
	python3 -m venv .env
