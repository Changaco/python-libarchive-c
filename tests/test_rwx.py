"""Test reading, writing and extracting archives."""

import io
import json

import libarchive
from libarchive.entry import format_time
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


def test_adding_nonexistent_file_to_archive():
    stream = io.BytesIO()
    with libarchive.custom_writer(stream.write, 'zip') as archive:
        with pytest.raises(libarchive.ArchiveError):
            archive.add_files('nonexistent')
        archive.add_files('libarchive/')


@pytest.mark.parametrize(
    'archfmt,data_bytes',
    [('zip', b'content'),
     ('gnutar', b''),
     ('pax', json.dumps({'a': 1, 'b': 2, 'c': 3}).encode()),
     ('7zip', b'lorem\0ipsum')])
def test_adding_entry_from_memory(archfmt, data_bytes):
    entry_path = 'testfile.data'
    entry_data = data_bytes
    entry_size = len(data_bytes)

    blocks = []

    archfmt = 'zip'
    has_birthtime = archfmt != 'zip'

    atime = (1482144741, 495628118)
    mtime = (1482155417, 659017086)
    ctime = (1482145211, 536858081)
    btime = (1482144740, 495628118) if has_birthtime else None

    def write_callback(data):
        blocks.append(data[:])
        return len(data)

    with libarchive.custom_writer(write_callback, archfmt) as archive:
        archive.add_file_from_memory(
            entry_path, entry_size, entry_data,
            atime=atime, mtime=mtime, ctime=ctime, birthtime=btime,
            uid=1000, gid=1000,
        )

    buf = b''.join(blocks)
    with libarchive.memory_reader(buf) as memory_archive:
        for archive_entry in memory_archive:
            expected = entry_data
            actual = b''.join(archive_entry.get_blocks())
            assert expected == actual
            assert archive_entry.path == entry_path
            assert archive_entry.atime in (atime[0], format_time(*atime))
            assert archive_entry.mtime in (mtime[0], format_time(*mtime))
            assert archive_entry.ctime in (ctime[0], format_time(*ctime))
            if has_birthtime:
                assert archive_entry.birthtime in (
                    btime[0], format_time(*btime)
                )
            assert archive_entry.uid == 1000
            assert archive_entry.gid == 1000
