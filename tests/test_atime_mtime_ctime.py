from copy import copy
from os import stat

from libarchive import (file_reader, file_writer, memory_reader, memory_writer)

import pytest

from . import treestat


# NOTE: zip does not support high resolution time data, but pax and others do
def check_atime_ctime(archive, tree, timefmt=int):
    tree2 = copy(tree)
    for entry in archive:
        epath = str(entry).rstrip('/')
        assert epath in tree2
        estat = tree2.pop(epath)
        assert entry.atime == timefmt(estat.st_atime)
        assert entry.ctime == timefmt(estat.st_ctime)


def stat_dict(path):
    # return the raw stat output, the tuple output only returns ints
    return stat(path)


def time_check(time_tuple, timefmt):
    seconds, nanos = time_tuple
    maths = float(seconds) + float(nanos) / 1000000000.0
    return timefmt(maths)


@pytest.mark.parametrize('archfmt,timefmt', [('zip', int), ('pax', float)])
def test_memory_atime_ctime(archfmt, timefmt):
    # Collect information on what should be in the archive
    tree = treestat('libarchive', stat_dict)

    # Create an archive of our libarchive/ directory
    buf = bytes(bytearray(1000000))
    with memory_writer(buf, archfmt) as archive1:
        archive1.add_files('libarchive/')

    # Check the data
    with memory_reader(buf) as archive2:
        check_atime_ctime(archive2, tree, timefmt=timefmt)


@pytest.mark.parametrize('archfmt,timefmt', [('zip', int), ('pax', float)])
def test_file_atime_ctime(archfmt, timefmt, tmpdir):
    archive_path = "{0}/test.{1}".format(tmpdir.strpath, archfmt)

    # Collect information on what should be in the archive
    tree = treestat('libarchive', stat_dict)

    # Create an archive of our libarchive/ directory
    with file_writer(archive_path, archfmt) as archive:
        archive.add_files('libarchive/')

    # Read the archive and check that the data is correct
    with file_reader(archive_path) as archive:
        check_atime_ctime(archive, tree, timefmt=timefmt)


@pytest.mark.parametrize('archfmt,timefmt', [('zip', int), ('pax', float)])
def test_memory_time_setters(archfmt, timefmt):
    has_birthtime = archfmt != 'zip'

    # Create an archive of our libarchive/ directory
    buf = bytes(bytearray(1000000))
    with memory_writer(buf, archfmt) as archive1:
        archive1.add_files('libarchive/')

    atimestamp = (1482144741, 495628118)
    mtimestamp = (1482155417, 659017086)
    ctimestamp = (1482145211, 536858081)
    btimestamp = (1482144740, 495628118)
    buf2 = bytes(bytearray(1000000))
    with memory_reader(buf) as archive1:
        with memory_writer(buf2, archfmt) as archive2:
            for entry in archive1:
                entry.set_atime(*atimestamp)
                entry.set_mtime(*mtimestamp)
                entry.set_ctime(*ctimestamp)
                if has_birthtime:
                    entry.set_birthtime(*btimestamp)
                archive2.add_entries([entry])

    with memory_reader(buf2) as archive2:
        for entry in archive2:
            assert entry.atime == time_check(atimestamp, timefmt)
            assert entry.mtime == time_check(mtimestamp, timefmt)
            assert entry.ctime == time_check(ctimestamp, timefmt)
            if has_birthtime:
                assert entry.birthtime == time_check(btimestamp, timefmt)


@pytest.mark.parametrize('archfmt,timefmt', [('zip', int), ('pax', float)])
def test_file_time_setters(archfmt, timefmt, tmpdir):
    has_birthtime = archfmt != 'zip'

    # Create an archive of our libarchive/ directory
    archive_path = tmpdir.join('/test.{0}'.format(archfmt)).strpath
    archive2_path = tmpdir.join('/test2.{0}'.format(archfmt)).strpath
    with file_writer(archive_path, archfmt) as archive1:
        archive1.add_files('libarchive/')

    atimestamp = (1482144741, 495628118)
    mtimestamp = (1482155417, 659017086)
    ctimestamp = (1482145211, 536858081)
    btimestamp = (1482144740, 495628118)
    with file_reader(archive_path) as archive1:
        with file_writer(archive2_path, archfmt) as archive2:
            for entry in archive1:
                entry.set_atime(*atimestamp)
                entry.set_mtime(*mtimestamp)
                entry.set_ctime(*ctimestamp)
                if has_birthtime:
                    entry.set_birthtime(*btimestamp)
                archive2.add_entries([entry])

    with file_reader(archive2_path) as archive2:
        for entry in archive2:
            assert entry.atime == time_check(atimestamp, timefmt)
            assert entry.mtime == time_check(mtimestamp, timefmt)
            assert entry.ctime == time_check(ctimestamp, timefmt)
            if has_birthtime:
                assert entry.birthtime == time_check(btimestamp, timefmt)
