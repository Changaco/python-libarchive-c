from __future__ import division, print_function, unicode_literals

from copy import copy
from os import stat

from libarchive import (file_reader, file_writer, memory_reader,
                        memory_writer)

from . import treestat


def check_atime_ctime(archive, tree):
    tree2 = copy(tree)
    for entry in archive:
        epath = str(entry).rstrip('/')
        assert epath in tree2
        estat = tree2.pop(epath)
        assert entry.atime == int(estat['atime'])
        assert entry.ctime == int(estat['ctime'])


def stat_dict(path):
    _, _, _, _, _, _, _, atime, _, ctime = stat(path)
    return {"atime": atime, "ctime": ctime}


def test_memory_atime_ctime():
    # Collect information on what should be in the archive
    tree = treestat('libarchive', stat_dict)

    # Create an archive of our libarchive/ directory
    buf = bytes(bytearray(1000000))
    with memory_writer(buf, 'zip') as archive1:
        archive1.add_files('libarchive/')

    # Check the data
    with memory_reader(buf) as archive2:
        check_atime_ctime(archive2, tree)


def test_file_atime_ctime(tmpdir):
    archive_path = tmpdir.strpath+'/test.zip'

    # Collect information on what should be in the archive
    tree = treestat('libarchive', stat_dict)

    # Create an archive of our libarchive/ directory
    with file_writer(archive_path, 'zip') as archive:
        archive.add_files('libarchive/')

    # Read the archive and check that the data is correct
    with file_reader(archive_path) as archive:
        check_atime_ctime(archive, tree)


def test_memory_time_setters():
    # Create an archive of our libarchive/ directory

    atimestamp = (1482144741, 495628118)
    mtimestamp = (1482155417, 659017086)
    ctimestamp = (1482145211, 536858081)
    buf = bytes(bytearray(1000000))
    with memory_writer(buf, "zip") as archive1:
        archive1.add_files('libarchive/')

    buf2 = bytes(bytearray(1000000))
    with memory_reader(buf) as archive1:
        with memory_writer(buf2, "zip") as archive2:
            for entry in archive1:
                entry.set_atime(*atimestamp)
                entry.set_mtime(*mtimestamp)
                entry.set_ctime(*ctimestamp)
                archive2.add_entries([entry])

    with memory_reader(buf2) as archive2:
        for entry in archive2:
            assert entry.atime == atimestamp[0]
            assert entry.mtime == mtimestamp[0]
            assert entry.ctime == ctimestamp[0]


def test_file_time_setters(tmpdir):
    # Create an archive of our libarchive/ directory
    archive_path = tmpdir.join('/test.zip').strpath
    archive2_path = tmpdir.join('/test2.zip').strpath

    atimestamp = (1482144741, 495628118)
    mtimestamp = (1482155417, 659017086)
    ctimestamp = (1482145211, 536858081)
    with file_writer(archive_path, "zip") as archive1:
        archive1.add_files('libarchive/')

    with file_reader(archive_path) as archive1:
        with file_writer(archive2_path, "zip") as archive2:
            for entry in archive1:
                entry.set_atime(*atimestamp)
                entry.set_mtime(*mtimestamp)
                entry.set_ctime(*ctimestamp)
                archive2.add_entries([entry])

    with file_reader(archive2_path) as archive2:
        for entry in archive2:
            assert entry.atime == atimestamp[0]
            assert entry.mtime == mtimestamp[0]
            assert entry.ctime == ctimestamp[0]
