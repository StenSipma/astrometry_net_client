PY=python3
PIP=pip

PY_FILES=astrometry_net_client/*.py tests/*.py setup.py

BLACK_ARGS=-l 79
ISORT_ARGS=--multi-line=3 --trailing-comma --force-grid-wrap=0 --use-parentheses --line-width=79


default: check-in-venv format lint package install test

check-in-venv:
	env | grep 'VIRTUAL_ENV'

# Packaging
install:
	$(PIP) install dist/astrometry_net_client-*.tar.gz

package:
	$(PY) setup.py sdist bdist_wheel

dependencies:
	$(PIP) install -r requirements.txt

# Testing
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
clean:
	-rm -r astrometry_net_client.egg-info 
	-rm -r build 
	-rm -r dist


