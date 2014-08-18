# This file is part of a program licensed under the terms of the GNU Lesser
# General Public License version 2 (or at your option any later version)
# as published by the Free Software Foundation: http://www.gnu.org/licenses/


from __future__ import division, print_function, unicode_literals

from contextlib import contextmanager
from copy import copy
from os import chdir, getcwd, stat, walk
from os.path import abspath, join
from stat import S_ISREG


def check_archive(archive, tree):
    tree2 = copy(tree)
    for e in archive:
        epath = str(e).rstrip('/')
        assert epath in tree2
        estat = tree2.pop(epath)
        assert e.mtime == int(estat['mtime'])
        if not e.isdir:
            size = e.size
            if size is not None:
                assert size == estat['size']
            with open(epath, 'rb') as f:
                for block in e.get_blocks():
                    assert f.read(len(block)) == block
                assert not f.read()

    # Check that there are no missing directories or files
    assert len(tree2) == 0


@contextmanager
def in_dir(dirpath):
    prev = abspath(getcwd())
    chdir(dirpath)
    try:
        yield
    finally:
        chdir(prev)


def stat_dict(path):
    keys = set(('uid', 'gid', 'mtime'))
    mode, _, _, _, uid, gid, size, _, mtime, _ = stat(path)
    if S_ISREG(mode):
        keys.add('size')
    return {k: v for k, v in locals().items() if k in keys}


def treestat(d):
    r = {}
    for dirpath, dirnames, filenames in walk(d):
        r[dirpath] = stat_dict(dirpath)
        for fname in filenames:
            fpath = join(dirpath, fname)
            r[fpath] = stat_dict(fpath)
    return r
