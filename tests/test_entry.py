# This file is part of a program licensed under the terms of the GNU Lesser
# General Public License version 2 (or at your option any later version)
# as published by the Free Software Foundation: http://www.gnu.org/licenses/


from __future__ import division, print_function, unicode_literals

import codecs
from contextlib import closing
import json
from os import environ, path, stat
import tarfile

from libarchive import file_reader, memory_reader, memory_writer
from base64 import b64decode
from base64 import b64encode


test_data = path.join(path.dirname(__file__), 'data')

# flake8: noqa

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
    test_file = path.join(test_data, 'special.tar')
    expected = list(get_tarinfos(test_file))
    result = list(get_entries(test_file))
    for i, e in enumerate(expected):
        assert e == result[i]
    assert len(expected) == len(result)


def test_check_archiveentry_against_tarfile_tarinfo_relative():
    test_file = path.join(test_data, 'tar_relative.tar')
    expected = list(get_tarinfos(test_file))
    result = list(get_entries(test_file))
    for i, e in enumerate(expected):
        assert e == result[i]
    assert len(expected) == len(result)


def test_check_archiveentry_using_python_testtar():
    test_file = path.join(test_data, 'testtar.tar')
    check_entries(test_file, regen=False)


def test_check_archiveentry_with_unicode_and_binary_entries_tar():
    test_file = path.join(test_data, 'unicode.tar')
    check_entries(test_file, regen=False)


def test_check_archiveentry_with_unicode_and_binary_entries_zip():
    test_file = path.join(test_data, 'unicode.zip')
    check_entries(test_file, regen=False)


def test_check_archiveentry_with_unicode_and_binary_entries_zip2():
    test_file = path.join(test_data, 'unicode2.zip')
    check_entries(test_file, regen=False)


def check_entries(test_file, regen=False):
    expected_file = test_file + '.json'
    # needed for sane time stamp comparison
    environ['TZ'] = 'UTC'
    if regen:
        encoded = list(get_entries2(test_file, encode=True))
        with codecs.open(expected_file, 'w', encoding='UTF-8') as ex:
            json.dump(encoded, ex, indent=2)

    result = list(get_entries2(test_file, encode=False))

    with codecs.open(expected_file, encoding='UTF-8') as ex:
        expected = json.load(ex)
        # decode encoded paths back to bytes to get meaningful test failures
        for ex in expected:
            ex['path'] = decode_path(ex['path'])
            #ex['pathw'] = decode_path(ex['pathw'])
            ex['linkpath'] = decode_path(ex['linkpath'])
    assert expected == result


def encode_path(arch_path):
    """
    Return the `arch_path` bytes string as a base64-encoded unicode string.
    Rationale: tests expectations are stored as UTF-8 JSON yet paths can be
    arbitrary byte strings. This encoding ensures that we can safely store
    bytes in UTF-8 strings.
    """
    return unicode(b64encode(arch_path)) if arch_path else arch_path


def decode_path(arch_path):
    """
    Return a `arch_path` bytes string decoded from a base64-encoded unicode
    string.
    Rationale: tests expectations are stored as UTF-8 JSON yet paths can be
    arbitrary byte strings. This encoding ensures that we can safely store
    bytes in UTF-8 strings.
    """
    return str(b64decode(arch_path)) if arch_path else arch_path


def get_entries2(location, encode=False):
    """
    Using the archive file at `location`, return an iterable of name->value
    mappings for each libarchive.ArchiveEntry objects essential attributes.
    Paths are base64-encoded because JSON is UTF-8 and cannot handle
    arbitrary binary pathdata.
    """
    with file_reader(location) as arch:
        for entry in arch:
            # libarchive introduces prefixes such as h prefix for
            # hardlinks: tarfile does not, so we ignore the first char
            mode = entry.strmode[1:].decode('ascii')
            yield {
                'path': encode_path(entry.pathname) if encode else entry.pathname,
                'pathw': entry.pathw,
                'mtime': entry.mtime,
                'size': entry.size,
                'mode': mode,
                'isreg': entry.isreg,
                'isdir': entry.isdir,
                'islnk': entry.islnk,
                'issym': entry.issym,
                'linkpath': encode_path(entry.linkpath) if encode else entry.linkpath,
                'isblk': entry.isblk,
                'ischr': entry.ischr,
                'isfifo': entry.isfifo,
                'isdev': entry.isdev,
            }

def get_entries(location, encode=False):
    """
    Using the archive file at `location`, return an iterable of name->value
    mappings for each libarchive.ArchiveEntry objects essential attributes.
    Paths are base64-encoded because JSON is UTF-8 and cannot handle
    arbitrary binary pathdata.
    """
    with file_reader(location) as arch:
        for entry in arch:
            # libarchive introduces prefixes such as h prefix for
            # hardlinks: tarfile does not, so we ignore the first char
            mode = entry.strmode[1:].decode('ascii')
            yield {
                'path': encode_path(entry.pathname) if encode else entry.pathname,
                'mtime': entry.mtime,
                'size': entry.size,
                'mode': mode,
                'isreg': entry.isreg,
                'isdir': entry.isdir,
                'islnk': entry.islnk,
                'issym': entry.issym,
                'linkpath': encode_path(entry.linkpath) if encode else entry.linkpath,
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
    Paths are base64-encoded because JSON is UTF-8 and cannot handle
    arbitrary binary pathdata.
    """
    with closing(tarfile.open(location)) as tar:
        while True:
            entry = tar.next()
            if not entry:
                break
            path = entry.path or ''
            if entry.isdir() and not entry.path.endswith('/'):
                path += '/'
            # libarchive introduces prefixes such as h prefix for
            # hardlinks: tarfile does not, so we ignore the first char
            mode = tarfile.filemode(entry.mode)[1:].decode('ascii')
            yield {
                'path': path,
                'mtime': entry.mtime,
                'size': entry.size,
                'mode': mode,
                'isreg': entry.isreg(),
                'isdir': entry.isdir(),
                'islnk': entry.islnk(),
                'issym': entry.issym(),
                'linkpath': entry.linkpath or None,
                'isblk': entry.isblk(),
                'ischr': entry.ischr(),
                'isfifo': entry.isfifo(),
                'isdev': entry.isdev(),
            }
