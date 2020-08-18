PY=python3
PIP=pip
TEST=pytest

PY_FILES=astrometry_net_client/*.py tests/*.py setup.py examples/*.py

TEST_ARGS=-v

BLACK_ARGS=-l 79
ISORT_ARGS=--multi-line=3 --trailing-comma --force-grid-wrap=0 --use-parentheses --line-width=79


default: check-in-venv format lint install

all: default dependencies test documentation

check-in-venv:
	env | grep 'VIRTUAL_ENV'

# Packaging
install: package-install

package-install: package
	$(PIP) install dist/astrometry_net_client-*.tar.gz

package: dependencies
	$(PY) setup.py sdist bdist_wheel

# Dependencies for the development environment, 
# e.g. contains Sphinx, flake8, black, isort etc.
dependencies:
	$(PIP) install -r requirements.txt

# Generate the documentation
documentation:
	make --directory=docs/ html

# Testing. The default test does not include the online tests 
test:
	$(TEST) $(TEST_ARGS) -m 'not online or not long' tests/

# Includes all tests, so also those that query the actual api.
test-all:
	$(TEST) $(TEST_ARGS) -m 'not long' tests/

# Formatting and linting
format:
	black $(BLACK_ARGS) $(PY_FILES)
	isort $(ISORT_ARGS) $(PY_FILES)

check-format:
	black --check $(BLACK_ARGS) $(PY_FILES)
	isort --check-only $(ISORT_ARGS) $(PY_FILES)

lint:
	flake8 $(PY_FILES)

# Cleanup
clean: clean-package clean-docs

clean-package:
	-rm -r astrometry_net_client.egg-info 
	-rm -r build 
	-rm -r dist

clean-docs:
	make --directory=docs clean

virt-env:
	python3 -m venv .env
