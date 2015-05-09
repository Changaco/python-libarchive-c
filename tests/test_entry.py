# This file is part of a program licensed under the terms of the GNU Lesser
# General Public License version 2 (or at your option any later version)
# as published by the Free Software Foundation: http://www.gnu.org/licenses/


from __future__ import division, print_function, unicode_literals

from contextlib import closing
from os import path, stat
import tarfile

from libarchive import file_reader, memory_reader, memory_writer


def test_entry_properties():

    buf = bytes(bytearray(1000000))
    with memory_writer(buf, 'gnutar') as archive:
        archive.add_files('README.rst')

    with memory_reader(buf) as archive:
        for entry in archive:
            assert entry.mode == stat('README.rst')[0]
            assert not entry.isblk
            assert not entry.ischr
            assert not entry.isdir
            assert not entry.isfifo
            assert not entry.islnk
            assert not entry.issym
            assert not entry.linkpath
            assert entry.linkpath == entry.linkname
            assert entry.isreg
            assert entry.isfile
            assert not entry.issock
            assert not entry.isdev
            assert b'rw' in entry.strmode
            assert entry.pathname == entry.path
            assert entry.pathname == entry.name

def test_check_archiveentry_against_tarfile_tarinfo():
    test_data = path.join(path.dirname(__file__), 'data')
    test_file = path.join(test_data, 'special.tar')
    expected = list(get_tarinfos(test_file))
    result = list(get_entries(test_file))
    for i, e in enumerate(expected):
        assert e == result[i]
    assert len(expected) == len(result)


def test_check_archiveentry_against_tarfile_tarinfo_relative():
    test_data = path.join(path.dirname(__file__), 'data')
    test_file = path.join(test_data, 'tar_relative.tar')
    expected = list(get_tarinfos(test_file))
    result = list(get_entries(test_file))
    for i, e in enumerate(expected):
        assert e == result[i]
    assert len(expected) == len(result)


def get_entries(location):
    """
    Using the archive file at `location`, return an iterable of name->value
    mappings for each libarchive,ArchiveEntry objects essential attributes.
    """
    with file_reader(location) as arch:
        for entry in arch:
            # libarchive introduces prefixes such as h prefix for
            # hardlinks: tarfile does not, so we ignore the first char
            mode = entry.strmode[1:].decode('ascii')
            yield {
                'path': entry.pathname,
                'mtime': entry.mtime,
                'size': entry.size,
                'mode': mode,
                'isreg': entry.isreg,
                'isdir': entry.isdir,
                'islnk': entry.islnk,
                'issym': entry.issym,
                'linkpath': entry.linkpath or '',
                'isblk': entry.isblk,
                'ischr': entry.ischr,
                'isfifo': entry.isfifo,
                'isdev': entry.isdev,
            }


def get_tarinfos(location):
    """
    Using the tar archive file at `location`, return an iterable of
    name->value mappings for each tarfile.TarInfo objects essential
    attributes.
    """
    with closing(tarfile.open(location)) as tar:
        while True:
            tinfo = tar.next()
            if not tinfo:
                break
            path = tinfo.path or ''
            if tinfo.isdir() and not tinfo.path.endswith('/'):
                path += '/'
            # libarchive introduces prefixes such as h prefix for
            # hardlinks: tarfile does not, so we ignore the first char
            mode = tarfile.filemode(tinfo.mode)[1:]
            yield {
                'path': path,
                'mtime': tinfo.mtime,
                'size': tinfo.size,
                'mode': mode,
                'isreg': tinfo.isreg(),
                'isdir': tinfo.isdir(),
                'islnk': tinfo.islnk(),
                'issym': tinfo.issym(),
                'linkpath': tinfo.linkpath or '',
                'isblk': tinfo.isblk(),
                'ischr': tinfo.ischr(),
                'isfifo': tinfo.isfifo(),
                'isdev': tinfo.isdev(),
            }
