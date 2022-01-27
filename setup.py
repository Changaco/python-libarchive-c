import os
from os.path import join, dirname

from setuptools import setup, find_packages

from version import get_version

os.umask(0o022)

with open(join(dirname(__file__), 'README.rst'), encoding="utf-8") as f:
    README = f.read()

setup(
    name='libarchive-c',
    version=get_version(),
    description='Python interface to libarchive',
    author='Changaco',
    author_email='changaco@changaco.oy.lc',
    url='https://github.com/Changaco/python-libarchive-c',
    license='CC0',
    packages=find_packages(exclude=['tests']),
    long_description=README,
    long_description_content_type='text/x-rst',
    keywords='archive libarchive 7z tar bz2 zip gz',
)
