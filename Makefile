PY=python3
PIP=pip

PY_FILES=astrometry_net_client/*.py tests/*.py setup.py

BLACK_ARGS=-l 79
ISORT_ARGS=--multi-line=3 --trailing-comma --force-grid-wrap=0 --use-parentheses --line-width=79


default: check-in-venv format lint install

all: default test documentation

check-in-venv:
	env | grep 'VIRTUAL_ENV'

# Packaging
install: package
	$(PIP) install dist/astrometry_net_client-*.tar.gz

package:
	$(PY) setup.py sdist bdist_wheel

# Dependencies for the development environment, 
# e.g. contains Sphinx, flake8, black, isort etc.
dependencies:
	$(PIP) install -r requirements.txt

# Generate the documentation
documentation:
	make --directory=docs/ html

# Testing (will be improved)
test:
	$(PY) tests/test.py

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

