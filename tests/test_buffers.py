# This file is part of a program licensed under the terms of the GNU Lesser
# General Public License version 2 (or at your option any later version)
# as published by the Free Software Foundation: http://www.gnu.org/licenses/


from __future__ import division, print_function, unicode_literals

from os import chdir, getcwd
from os.path import abspath
from shutil import rmtree
from tempfile import mkdtemp

import libarchive
from libarchive.extract import EXTRACT_OWNER, EXTRACT_PERM, EXTRACT_TIME

from . import check_archive, treestat


def test_buffers():

    # Collect information on what should be in the archive
    tree = treestat('libarchive')

    # Make a temporary dir
    basedir = abspath(getcwd())
    tmpdir = mkdtemp()

    try:

        # Create an archive of our libarchive/ directory
        buf = bytes(bytearray(1000000))
        with libarchive.memory_writer(buf, 'ustar', 'xz') as archive:
            archive.add_files('libarchive/')

        # Read the archive and check that the data is correct
        with libarchive.memory_reader(buf) as archive:
            check_archive(archive, tree)

        # Move to the temporary dir
        chdir(tmpdir)

        # Extract the archive and check that the data is intact
        flags = EXTRACT_OWNER | EXTRACT_PERM | EXTRACT_TIME
        libarchive.extract_memory(buf, flags)
        tree2 = treestat('libarchive')
        assert tree2 == tree

    finally:
        chdir(basedir)
        rmtree(tmpdir)
