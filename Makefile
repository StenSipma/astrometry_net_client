PY=python3
PIP=pip

PY_FILES=astrometry_net_client/*.py tests/*.py setup.py

all: check-in-venv package install test

check-in-venv:
	env | grep 'VIRTUAL_ENV'

install:
	$(PIP) install dist/astrometry_net_client-*.tar.gz

package:
	$(PY) setup.py sdist bdist_wheel

dependencies:
	$(PIP) install -r requirements.txt

test:
	$(PY) tests/test.py

format:
	black -l 80 $(PY_FILES)

lint:


clean:
	-rm -r astrometry_net_client.egg-info 
	-rm -r build 
	-rm -r dist


