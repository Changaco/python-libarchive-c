"""Test security-related extraction flags."""

from __future__ import division, print_function, unicode_literals
import pytest
import os

from libarchive import extract_file
from libarchive.ffi import version_number
from libarchive.extract import (
    EXTRACT_SECURE_NOABSOLUTEPATHS, EXTRACT_SECURE_NODOTDOT,
)
from libarchive.exception import ArchiveError
from . import data_dir


def run_test(flag, filename):
    archive_path = os.path.join(data_dir, 'flags.tar')
    try:
        extract_file(archive_path)
        with pytest.raises(ArchiveError):
            extract_file(archive_path, flag)
    finally:
        if os.path.exists(filename):
            os.remove(filename)


def test_no_dot_dot():
    run_test(EXTRACT_SECURE_NODOTDOT, '../python-libarchive-c-test-dot-dot-file')


def test_absolute():
    # EXTRACT_SECURE_NOABSOLUTEPATHS was only added in 3.1.900
    # 3.1.900 -> 3001009
    if version_number() >= 3001009:
        run_test(
            EXTRACT_SECURE_NOABSOLUTEPATHS,
            '/tmp/python-libarchive-c-test-absolute-file'
        )
