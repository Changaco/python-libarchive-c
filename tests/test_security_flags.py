"""Test security-related extraction flags."""

import pytest
import os

from libarchive import extract_file, file_reader
from libarchive.extract import (
    EXTRACT_SECURE_NOABSOLUTEPATHS, EXTRACT_SECURE_NODOTDOT,
)
from libarchive.exception import ArchiveError
from . import data_dir


def run_test(flags):
    archive_path = os.path.join(data_dir, 'flags.tar')
    try:
        extract_file(archive_path, 0)
        with pytest.raises(ArchiveError):
            extract_file(archive_path, flags)
    finally:
        with file_reader(archive_path) as archive:
            for entry in archive:
                if os.path.exists(entry.pathname):
                    os.remove(entry.pathname)


def test_extraction_is_secure_by_default():
    run_test(None)


def test_explicit_no_dot_dot():
    run_test(EXTRACT_SECURE_NODOTDOT)


def test_explicit_no_absolute_paths():
    run_test(EXTRACT_SECURE_NOABSOLUTEPATHS)
