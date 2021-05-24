from contextlib import closing, contextmanager
from copy import copy
from os import chdir, getcwd, stat, walk
from os.path import abspath, dirname, join
from stat import S_ISREG
import tarfile
try:
    from stat import filemode
except ImportError:  # Python 2
    filemode = tarfile.filemode

from libarchive import file_reader


data_dir = join(dirname(__file__), 'data')


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
                leftover = f.read()
                assert not leftover

    # Check that there are no missing directories or files
    assert len(tree2) == 0


def get_entries(location):
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
                'path': surrogate_decode(entry.pathname),
                'mtime': entry.mtime,
                'size': entry.size,
                'mode': mode,
                'isreg': entry.isreg,
                'isdir': entry.isdir,
                'islnk': entry.islnk,
                'issym': entry.issym,
                'linkpath': surrogate_decode(entry.linkpath),
                'isblk': entry.isblk,
                'ischr': entry.ischr,
                'isfifo': entry.isfifo,
                'isdev': entry.isdev,
                'uid': entry.uid,
                'gid': entry.gid
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
        for entry in tar:
            path = surrogate_decode(entry.path or '')
            if entry.isdir() and not path.endswith('/'):
                path += '/'
            # libarchive introduces prefixes such as h prefix for
            # hardlinks: tarfile does not, so we ignore the first char
            mode = filemode(entry.mode)[1:]
            yield {
                'path': path,
                'mtime': entry.mtime,
                'size': entry.size,
                'mode': mode,
                'isreg': entry.isreg(),
                'isdir': entry.isdir(),
                'islnk': entry.islnk(),
                'issym': entry.issym(),
                'linkpath': surrogate_decode(entry.linkpath or None),
                'isblk': entry.isblk(),
                'ischr': entry.ischr(),
                'isfifo': entry.isfifo(),
                'isdev': entry.isdev(),
                'uid': entry.uid,
                'gid': entry.gid
            }


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


def treestat(d, stat_dict=stat_dict):
    r = {}
    for dirpath, dirnames, filenames in walk(d):
        r[dirpath] = stat_dict(dirpath)
        for fname in filenames:
            fpath = join(dirpath, fname)
            r[fpath] = stat_dict(fpath)
    return r


def surrogate_decode(o):
    if isinstance(o, bytes):
        return o.decode('utf8', errors='surrogateescape')
    return o
