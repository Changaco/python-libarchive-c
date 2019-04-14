"""Test reading, writing and extracting archives."""

from __future__ import division, print_function, unicode_literals

import io
import json
import sys

import libarchive
from libarchive.extract import EXTRACT_OWNER, EXTRACT_PERM, EXTRACT_TIME
from libarchive.write import memory_writer
from mock import patch

import pytest

from . import check_archive, in_dir, treestat


def test_buffers(tmpdir):

    # Collect information on what should be in the archive
    tree = treestat('libarchive')

    # Create an archive of our libarchive/ directory
    buf = bytes(bytearray(1000000))
    with libarchive.memory_writer(buf, 'gnutar', 'xz') as archive:
        archive.add_files('libarchive/')

    # Read the archive and check that the data is correct
    with libarchive.memory_reader(buf) as archive:
        check_archive(archive, tree)

    # Extract the archive in tmpdir and check that the data is intact
    with in_dir(tmpdir.strpath):
        flags = EXTRACT_OWNER | EXTRACT_PERM | EXTRACT_TIME
        libarchive.extract_memory(buf, flags)
        tree2 = treestat('libarchive')
        assert tree2 == tree


def test_fd(tmpdir):
    archive_file = open(tmpdir.strpath+'/test.tar.bz2', 'w+b')
    fd = archive_file.fileno()

    # Collect information on what should be in the archive
    tree = treestat('libarchive')

    # Create an archive of our libarchive/ directory
    with libarchive.fd_writer(fd, 'gnutar', 'bzip2') as archive:
        archive.add_files('libarchive/')

    # Read the archive and check that the data is correct
    archive_file.seek(0)
    with libarchive.fd_reader(fd) as archive:
        check_archive(archive, tree)

    # Extract the archive in tmpdir and check that the data is intact
    archive_file.seek(0)
    with in_dir(tmpdir.strpath):
        flags = EXTRACT_OWNER | EXTRACT_PERM | EXTRACT_TIME
        libarchive.extract_fd(fd, flags)
        tree2 = treestat('libarchive')
        assert tree2 == tree


def test_files(tmpdir):
    archive_path = tmpdir.strpath+'/test.tar.gz'

    # Collect information on what should be in the archive
    tree = treestat('libarchive')

    # Create an archive of our libarchive/ directory
    with libarchive.file_writer(archive_path, 'ustar', 'gzip') as archive:
        archive.add_files('libarchive/')

    # Read the archive and check that the data is correct
    with libarchive.file_reader(archive_path) as archive:
        check_archive(archive, tree)

    # Extract the archive in tmpdir and check that the data is intact
    with in_dir(tmpdir.strpath):
        flags = EXTRACT_OWNER | EXTRACT_PERM | EXTRACT_TIME
        libarchive.extract_file(archive_path, flags)
        tree2 = treestat('libarchive')
        assert tree2 == tree


def test_custom_writer_and_stream_reader():
    # Collect information on what should be in the archive
    tree = treestat('libarchive')

    # Create an archive of our libarchive/ directory
    stream = io.BytesIO()
    with libarchive.custom_writer(stream.write, 'zip') as archive:
        archive.add_files('libarchive/')
    stream.seek(0)

    # Read the archive and check that the data is correct
    with libarchive.stream_reader(stream, 'zip') as archive:
        check_archive(archive, tree)


@patch('libarchive.ffi.write_fail')
def test_write_fail(write_fail_mock):
    buf = bytes(bytearray(1000000))
    try:
        with memory_writer(buf, 'gnutar', 'xz') as archive:
            archive.add_files('libarchive/')
            raise TypeError
    except TypeError:
        pass
    assert write_fail_mock.called


@patch('libarchive.ffi.write_fail')
def test_write_not_fail(write_fail_mock):
    buf = bytes(bytearray(1000000))
    with memory_writer(buf, 'gnutar', 'xz') as archive:
        archive.add_files('libarchive/')
    assert not write_fail_mock.called


@pytest.mark.parametrize(
    'archfmt,data_bytes',
    [('zip', b'content'),
     ('gnutar', 'a_string'.encode()),
     ('pax', json.dumps({'a': 1, 'b': 2, 'c': 3}).encode())])
def test_adding_entry_from_memory(archfmt, data_bytes):
    if sys.version_info[0] < 3:
        string_types = (str, unicode)  # noqa: F821
    else:
        string_types = (str,)

    entry_path = 'testfile.data'

    # entry_data must be a list of byte-like objects for maximum compatibility
    # (Use of other data types can have undesirable side-effects)
    # entry_size is the total size in bytes of the entry_data items
    entry_data = [data_bytes]
    entry_size = sum(len(bdata) for bdata in entry_data)

    blocks = []

    def write_callback(data):
        blocks.append(data[:])
        return len(data)

    with libarchive.custom_writer(write_callback, archfmt) as archive:
        archive.add_file_from_memory(
            entry_path, entry_size, entry_data)

    buf = b''.join(blocks)
    with libarchive.memory_reader(buf) as memory_archive:
        for archive_entry in memory_archive:
            expected = b''.join(
                [a.encode()
                 if isinstance(a, string_types)
                 else a for a in entry_data],
            )
            actual = b''.join(
                archive_entry.get_blocks(),
            )
            assert expected == actual
            assert archive_entry.path == entry_path
