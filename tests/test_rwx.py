"""Test reading, writing and extracting archives."""

from __future__ import division, print_function, unicode_literals

import libarchive
from libarchive.extract import EXTRACT_OWNER, EXTRACT_PERM, EXTRACT_TIME

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


def test_custom_writer():

    # Collect information on what should be in the archive
    tree = treestat('libarchive')

    # Create an archive of our libarchive/ directory
    blocks = []

    def write_cb(data):
        blocks.append(data[:])
        return len(data)

    with libarchive.custom_writer(write_cb, 'zip') as archive:
        archive.add_files('libarchive/')
        pass

    # Read the archive and check that the data is correct
    buf = b''.join(blocks)
    with libarchive.memory_reader(buf) as archive:
        check_archive(archive, tree)
