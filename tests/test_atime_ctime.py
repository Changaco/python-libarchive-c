from __future__ import division, print_function, unicode_literals

from copy import copy
from os import stat

from libarchive import (file_reader, file_writer, memory_reader,
                        memory_writer)

from . import treestat


def check_atime_ctime(archive, tree):
    tree2 = copy(tree)
    for e in archive:
        epath = str(e).rstrip('/')
        assert epath in tree2
        estat = tree2.pop(epath)
        assert e.atime == int(estat['atime'])
        assert e.ctime == int(estat['ctime'])


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
