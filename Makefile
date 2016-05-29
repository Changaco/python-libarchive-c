clean:
	rm -rf build dist *.egg-info
	find . -name \*.pyc -delete

env: requirements_tests.txt
	virtualenv3 ./env
	virtualenv2 ./env
	./env/bin/pip3 install -r requirements_tests.txt
	./env/bin/pip2 install -r requirements_tests.txt

dist:
	python3 setup.py sdist bdist_wheel
	python2 setup.py sdist

lint: env
	./env/bin/flake8 libarchive tests

test: env
	./env/bin/python3 -m pytest -s -vv --cov libarchive --cov-report html ./tests
	./env/bin/python2 -m pytest -s -vv --cov libarchive ./tests
	@$(MAKE) --no-print-directory lint

tests: test

upload:
	python3 setup.py sdist bdist_wheel upload
