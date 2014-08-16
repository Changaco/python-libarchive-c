# This file is part of a program licensed under the terms of the GNU Lesser
# General Public License version 2 (or at your option any later version)
# as published by the Free Software Foundation: http://www.gnu.org/licenses/


from __future__ import division, print_function, unicode_literals

import libarchive
from libarchive.extract import EXTRACT_OWNER, EXTRACT_PERM, EXTRACT_TIME

from . import check_archive, in_dir, treestat


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
