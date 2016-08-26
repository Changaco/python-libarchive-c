clean:
	rm -rf build dist *.egg-info
	find . -name \*.pyc -delete

chmod:
	git ls-files -z | xargs -0 chmod u=rwX,g=rX,o=rX

dist: chmod
	python3 setup.py sdist bdist_wheel
	python2 setup.py sdist

upload: chmod
	python3 setup.py sdist bdist_wheel upload
