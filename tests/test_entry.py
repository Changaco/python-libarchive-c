# This file is part of a program licensed under the terms of the GNU Lesser
# General Public License version 2 (or at your option any later version)
# as published by the Free Software Foundation: http://www.gnu.org/licenses/


from __future__ import division, print_function, unicode_literals

from os import stat

from libarchive import memory_reader, memory_writer


def test_entry_properties():

    buf = bytes(bytearray(1000000))
    with memory_writer(buf, 'gnutar') as archive:
        archive.add_files('README.rst')

    with memory_reader(buf) as archive:
        for entry in archive:
            assert entry.mode == stat('README.rst')[0]
            assert b'rw' in entry.strmode
