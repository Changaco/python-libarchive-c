from contextlib import contextmanager
from ctypes import c_char_p, create_string_buffer
import math

from . import ffi


@contextmanager
def new_archive_entry():
    entry_p = ffi.entry_new()
    try:
        yield entry_p
    finally:
        ffi.entry_free(entry_p)


def format_time(seconds, nanos):
    """ return float of seconds.nanos when nanos set, or seconds when not """
    if nanos:
        return float(seconds) + float(nanos) / 1000000000.0
    return int(seconds)


class ArchiveEntry:

    __slots__ = ('_archive_p', '_entry_p')

    def __init__(self, archive_p):
        self._archive_p = archive_p
        self._entry_p = ffi.entry_new()

    def __del__(self):
        ffi.entry_free(self._entry_p)

    def __str__(self):
        return self.pathname

    @property
    def filetype(self):
        return ffi.entry_filetype(self._entry_p)

    @filetype.setter
    def filetype(self, value):
        ffi.entry_set_filetype(self._entry_p, value)

    @property
    def uid(self):
        return ffi.entry_uid(self._entry_p)

    @uid.setter
    def uid(self, uid):
        ffi.entry_set_uid(self._entry_p, uid)

    @property
    def gid(self):
        return ffi.entry_gid(self._entry_p)

    @gid.setter
    def gid(self, gid):
        ffi.entry_set_gid(self._entry_p, gid)

    def get_blocks(self, block_size=ffi.page_size):
        archive_p = self._archive_p
        buf = create_string_buffer(block_size)
        read = ffi.read_data
        while 1:
            r = read(archive_p, buf, block_size)
            if r == 0:
                break
            yield buf.raw[0:r]

    @property
    def isblk(self):
        return self.filetype & 0o170000 == 0o060000

    @property
    def ischr(self):
        return self.filetype & 0o170000 == 0o020000

    @property
    def isdir(self):
        return self.filetype & 0o170000 == 0o040000

    @property
    def isfifo(self):
        return self.filetype & 0o170000 == 0o010000

    @property
    def islnk(self):
        return bool(ffi.entry_hardlink_w(self._entry_p) or
                    ffi.entry_hardlink(self._entry_p))

    @property
    def issym(self):
        return self.filetype & 0o170000 == 0o120000

    @property
    def isreg(self):
        return self.filetype & 0o170000 == 0o100000

    @property
    def isfile(self):
        return self.isreg

    @property
    def issock(self):
        return self.filetype & 0o170000 == 0o140000

    @property
    def isdev(self):
        return self.ischr or self.isblk or self.isfifo or self.issock

    @property
    def atime(self):
        sec_val = ffi.entry_atime(self._entry_p)
        nsec_val = ffi.entry_atime_nsec(self._entry_p)
        return format_time(sec_val, nsec_val)

    @atime.setter
    def atime(self, value):
        if isinstance(value, int):
            self.set_atime(value)
        elif isinstance(value, tuple):
            self.set_atime(*value)
        else:
            seconds, fraction = math.modf(value)
            self.set_atime(int(seconds), int(fraction * 1_000_000_000))

    def set_atime(self, timestamp_sec, timestamp_nsec):
        return ffi.entry_set_atime(self._entry_p,
                                   timestamp_sec, timestamp_nsec)

    @property
    def mtime(self):
        sec_val = ffi.entry_mtime(self._entry_p)
        nsec_val = ffi.entry_mtime_nsec(self._entry_p)
        return format_time(sec_val, nsec_val)

    @mtime.setter
    def mtime(self, value):
        if isinstance(value, int):
            self.set_mtime(value)
        elif isinstance(value, tuple):
            self.set_mtime(*value)
        else:
            seconds, fraction = math.modf(value)
            self.set_mtime(int(seconds), int(fraction * 1_000_000_000))

    def set_mtime(self, timestamp_sec, timestamp_nsec):
        return ffi.entry_set_mtime(self._entry_p,
                                   timestamp_sec, timestamp_nsec)

    @property
    def ctime(self):
        sec_val = ffi.entry_ctime(self._entry_p)
        nsec_val = ffi.entry_ctime_nsec(self._entry_p)
        return format_time(sec_val, nsec_val)

    @ctime.setter
    def ctime(self, value):
        if isinstance(value, int):
            self.set_ctime(value)
        elif isinstance(value, tuple):
            self.set_ctime(*value)
        else:
            seconds, fraction = math.modf(value)
            self.set_ctime(int(seconds), int(fraction * 1_000_000_000))

    def set_ctime(self, timestamp_sec, timestamp_nsec):
        return ffi.entry_set_ctime(self._entry_p,
                                   timestamp_sec, timestamp_nsec)

    @property
    def birthtime(self):
        sec_val = ffi.entry_birthtime(self._entry_p)
        nsec_val = ffi.entry_birthtime_nsec(self._entry_p)
        return format_time(sec_val, nsec_val)

    @birthtime.setter
    def birthtime(self, value):
        if isinstance(value, int):
            self.set_birthtime(value)
        elif isinstance(value, tuple):
            self.set_birthtime(*value)
        else:
            seconds, fraction = math.modf(value)
            self.set_birthtime(int(seconds), int(fraction * 1_000_000_000))

    def set_birthtime(self, timestamp_sec, timestamp_nsec=0):
        return ffi.entry_set_birthtime(
            self._entry_p, timestamp_sec, timestamp_nsec
        )

    @property
    def pathname(self):
        return (ffi.entry_pathname_w(self._entry_p) or
                ffi.entry_pathname(self._entry_p))

    @pathname.setter
    def pathname(self, value):
        if not isinstance(value, bytes):
            value = value.encode('utf8')
        ffi.entry_update_pathname_utf8(self._entry_p, c_char_p(value))

    @property
    def linkpath(self):
        return (ffi.entry_symlink_w(self._entry_p) or
                ffi.entry_hardlink_w(self._entry_p) or
                ffi.entry_symlink(self._entry_p) or
                ffi.entry_hardlink(self._entry_p))

    @linkpath.setter
    def linkpath(self, value):
        ffi.entry_update_link_utf8(self._entry_p, value)

    # aliases for compatibility with the standard `tarfile` module
    path = property(pathname.fget, pathname.fset, doc="alias of pathname")
    name = path
    linkname = property(linkpath.fget, linkpath.fset, doc="alias of linkpath")

    @property
    def size(self):
        if ffi.entry_size_is_set(self._entry_p):
            return ffi.entry_size(self._entry_p)

    @size.setter
    def size(self, value):
        ffi.entry_set_size(self._entry_p, value)

    @property
    def mode(self):
        return ffi.entry_mode(self._entry_p)

    @mode.setter
    def mode(self, value):
        ffi.entry_set_mode(self._entry_p, value)

    @property
    def strmode(self):
        # note we strip the mode because archive_entry_strmode
        # returns a trailing space: strcpy(bp, "?rwxrwxrwx ");
        return ffi.entry_strmode(self._entry_p).strip()

    @property
    def perm(self):
        return ffi.entry_perm(self._entry_p)

    @perm.setter
    def perm(self, value):
        ffi.entry_set_perm(self._entry_p, value)

    @property
    def rdevmajor(self):
        return ffi.entry_rdevmajor(self._entry_p)

    @rdevmajor.setter
    def rdevmajor(self, value):
        ffi.entry_set_rdevmajor(self._entry_p, value)

    @property
    def rdevminor(self):
        return ffi.entry_rdevminor(self._entry_p)

    @rdevminor.setter
    def rdevminor(self, value):
        ffi.entry_set_rdevminor(self._entry_p, value)
