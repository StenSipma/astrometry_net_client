PY=python3
PIP=pip

all: check-in-venv package install test

check-in-venv:
	env | grep 'VIRTUAL_ENV'

install:
	$(PIP) install dist/astrometry_net_client-*.tar.gz

package:
	$(PY) setup.py sdist bdist_wheel

test:
	$(PY) tests/test.py

clean:
	-rm -r astrometry_net_client.egg-info 
	-rm -r build 
	-rm -r dist
