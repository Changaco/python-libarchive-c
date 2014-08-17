# This file is part of a program licensed under the terms of the GNU Lesser
# General Public License version 2 (or at your option any later version)
# as published by the Free Software Foundation: http://www.gnu.org/licenses/


from __future__ import division, print_function, unicode_literals

import libarchive
from libarchive.extract import EXTRACT_OWNER, EXTRACT_PERM, EXTRACT_TIME

from . import check_archive, in_dir, treestat


def test_fd(tmpdir):
    archive_file = open(tmpdir.strpath+'/test.tar.bz2', 'w+b')
    fd = archive_file.fileno()

    # Collect information on what should be in the archive
    tree = treestat('libarchive')

    # Create an archive of our libarchive/ directory
    with libarchive.fd_writer(fd, 'v7tar', 'bzip2') as archive:
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
