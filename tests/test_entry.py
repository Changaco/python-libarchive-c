# -*- coding: utf-8 -*-

from __future__ import division, print_function, unicode_literals

from codecs import open
import json
import locale
from os import environ, stat
from os.path import join
import sys
import unicodedata

from libarchive import memory_reader, memory_writer

from . import data_dir, get_entries, get_tarinfos


locale.setlocale(locale.LC_ALL, '')

# needed for sane time stamp comparison
environ['TZ'] = 'UTC'


def test_entry_properties():

    buf = bytes(bytearray(1000000))
    with memory_writer(buf, 'gnutar') as archive:
        archive.add_files('README.rst')

    readme_stat = stat('README.rst')

    with memory_reader(buf) as archive:
        for entry in archive:
            assert entry.uid == readme_stat.st_uid
            assert entry.gid == readme_stat.st_gid
            assert entry.mode == readme_stat.st_mode
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


def test_check_ArchiveEntry_against_TarInfo():
    for name in ('special.tar', 'tar_relative.tar'):
        path = join(data_dir, name)
        tarinfos = list(get_tarinfos(path))
        entries = list(get_entries(path))
        for tarinfo, entry in zip(tarinfos, entries):
            assert tarinfo == entry
        assert len(tarinfos) == len(entries)


def test_check_archiveentry_using_python_testtar():
    check_entries(join(data_dir, 'testtar.tar'))


def test_check_archiveentry_with_unicode_and_binary_entries_tar():
    check_entries(join(data_dir, 'unicode.tar'))


def test_check_archiveentry_with_unicode_and_binary_entries_zip():
    check_entries(join(data_dir, 'unicode.zip'))


def test_check_archiveentry_with_unicode_and_binary_entries_zip2():
    check_entries(join(data_dir, 'unicode2.zip'), ignore='mode')


def test_check_archiveentry_with_unicode_entries_and_name_zip():
    check_entries(join(data_dir, '\ud504\ub85c\uadf8\ub7a8.zip'))


def check_entries(test_file, regen=False, ignore=''):
    ignore = ignore.split()
    fixture_file = test_file + '.json'
    if regen:
        entries = list(get_entries(test_file))
        with open(fixture_file, 'w', encoding='UTF-8') as ex:
            json.dump(entries, ex, indent=2, sort_keys=True)
    with open(fixture_file, encoding='UTF-8') as ex:
        expected = json.load(ex)
    actual = list(get_entries(test_file))
    for e1, e2 in zip(actual, expected):
        for key in ignore:
            e1.pop(key)
            e2.pop(key)
        # Normalize all unicode (can vary depending on the system)
        for d in (e1, e2):
            for key in d:
                if sys.version_info[0] < 3:
                    IS_UNICODE = isinstance(d[key], unicode)  # noqa: F821
                else:
                    IS_UNICODE = isinstance(d[key], str)
                if IS_UNICODE:
                    d[key] = unicodedata.normalize('NFC', d[key])
        assert e1 == e2
