from contextlib import contextmanager
from ctypes import create_string_buffer
from enum import IntEnum
import math

from . import ffi


class FileType(IntEnum):
    NAMED_PIPE     = AE_IFIFO  = 0o010000  # noqa: E221
    CHAR_DEVICE    = AE_IFCHR  = 0o020000  # noqa: E221
    DIRECTORY      = AE_IFDIR  = 0o040000  # noqa: E221
    BLOCK_DEVICE   = AE_IFBLK  = 0o060000  # noqa: E221
    REGULAR_FILE   = AE_IFREG  = 0o100000  # noqa: E221
    SYMBOLINK_LINK = AE_IFLNK  = 0o120000  # noqa: E221
    SOCKET         = AE_IFSOCK = 0o140000  # noqa: E221


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

    __slots__ = ('_archive_p', '_entry_p', 'header_codec')

    def __init__(self, archive_p=None, header_codec='utf-8', **attributes):
        """Allocate memory for an `archive_entry` struct.

        The `header_codec` is used to decode and encode file paths and other
        attributes.

        The `**attributes` are passed to the `modify` method.
        """
        self._archive_p = archive_p
        self._entry_p = ffi.entry_new()
        self.header_codec = header_codec
        if attributes:
            self.modify(**attributes)

    def __del__(self):
        """Free the C struct"""
        ffi.entry_free(self._entry_p)

    def __str__(self):
        """Returns the file's path"""
        return self.pathname

    def modify(self, header_codec=None, **attributes):
        """Convenience method to modify the entry's attributes.

        Args:
            filetype (int): the file's type, see the `FileType` class for values
            pathname (str): the file's path
            linkpath (str): the other path of the file, if the file is a link
            size (int | None): the file's size, in bytes
            perm (int): the file's permissions in standard Unix format, e.g. 0o640
            uid (int): the file owner's numerical identifier
            gid (int): the file group's numerical identifier
            uname (str | bytes): the file owner's name
            gname (str | bytes): the file group's name
            atime (int | Tuple[int, int] | float | None):
                the file's most recent access time,
                either in seconds or as a tuple (seconds, nanoseconds)
            mtime (int | Tuple[int, int] | float | None):
                the file's most recent modification time,
                either in seconds or as a tuple (seconds, nanoseconds)
            ctime (int | Tuple[int, int] | float | None):
                the file's most recent metadata change time,
                either in seconds or as a tuple (seconds, nanoseconds)
            birthtime (int | Tuple[int, int] | float | None):
                the file's creation time (for archive formats that support it),
                either in seconds or as a tuple (seconds, nanoseconds)
            rdev (int | Tuple[int, int]): device number, if the file is a device
            rdevmajor (int): major part of the device number
            rdevminor (int): minor part of the device number
        """
        if header_codec:
            self.header_codec = header_codec
        for name, value in attributes.items():
            setattr(self, name, value)

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

    @property
    def uname(self):
        uname = ffi.entry_uname_w(self._entry_p)
        if not uname:
            uname = ffi.entry_uname(self._entry_p)
            if uname is not None:
                try:
                    uname = uname.decode(self.header_codec)
                except UnicodeError:
                    pass
        return uname

    @uname.setter
    def uname(self, value):
        if not isinstance(value, bytes):
            value = value.encode(self.header_codec)
        if self.header_codec == 'utf-8':
            ffi.entry_update_uname_utf8(self._entry_p, value)
        else:
            ffi.entry_copy_uname(self._entry_p, value)

    @property
    def gname(self):
        gname = ffi.entry_gname_w(self._entry_p)
        if not gname:
            gname = ffi.entry_gname(self._entry_p)
            if gname is not None:
                try:
                    gname = gname.decode(self.header_codec)
                except UnicodeError:
                    pass
        return gname

    @gname.setter
    def gname(self, value):
        if not isinstance(value, bytes):
            value = value.encode(self.header_codec)
        if self.header_codec == 'utf-8':
            ffi.entry_update_gname_utf8(self._entry_p, value)
        else:
            ffi.entry_copy_gname(self._entry_p, value)

    def get_blocks(self, block_size=ffi.page_size):
        """Read the file's content, keeping only one chunk in memory at a time.

        Don't do anything like `list(entry.get_blocks())`, it would silently fail.

        Args:
            block_size (int): the buffer's size, in bytes
        """
        archive_p = self._archive_p
        if not archive_p:
            raise TypeError("this entry isn't linked to any content")
        buf = create_string_buffer(block_size)
        read = ffi.read_data
        while 1:
            r = read(archive_p, buf, block_size)
            if r == 0:
                break
            yield buf.raw[0:r]
        self.__class__ = ConsumedArchiveEntry

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
        if not ffi.entry_atime_is_set(self._entry_p):
            return None
        sec_val = ffi.entry_atime(self._entry_p)
        nsec_val = ffi.entry_atime_nsec(self._entry_p)
        return format_time(sec_val, nsec_val)

    @atime.setter
    def atime(self, value):
        if value is None:
            ffi.entry_unset_atime(self._entry_p)
        elif isinstance(value, int):
            self.set_atime(value)
        elif isinstance(value, tuple):
            self.set_atime(*value)
        else:
            seconds, fraction = math.modf(value)
            self.set_atime(int(seconds), int(fraction * 1_000_000_000))

    def set_atime(self, timestamp_sec, timestamp_nsec=0):
        "Kept for backward compatibility. `entry.atime = ...` is supported now."
        return ffi.entry_set_atime(self._entry_p, timestamp_sec, timestamp_nsec)

    @property
    def mtime(self):
        if not ffi.entry_mtime_is_set(self._entry_p):
            return None
        sec_val = ffi.entry_mtime(self._entry_p)
        nsec_val = ffi.entry_mtime_nsec(self._entry_p)
        return format_time(sec_val, nsec_val)

    @mtime.setter
    def mtime(self, value):
        if value is None:
            ffi.entry_unset_mtime(self._entry_p)
        elif isinstance(value, int):
            self.set_mtime(value)
        elif isinstance(value, tuple):
            self.set_mtime(*value)
        else:
            seconds, fraction = math.modf(value)
            self.set_mtime(int(seconds), int(fraction * 1_000_000_000))

    def set_mtime(self, timestamp_sec, timestamp_nsec=0):
        "Kept for backward compatibility. `entry.mtime = ...` is supported now."
        return ffi.entry_set_mtime(self._entry_p, timestamp_sec, timestamp_nsec)

    @property
    def ctime(self):
        if not ffi.entry_ctime_is_set(self._entry_p):
            return None
        sec_val = ffi.entry_ctime(self._entry_p)
        nsec_val = ffi.entry_ctime_nsec(self._entry_p)
        return format_time(sec_val, nsec_val)

    @ctime.setter
    def ctime(self, value):
        if value is None:
            ffi.entry_unset_ctime(self._entry_p)
        elif isinstance(value, int):
            self.set_ctime(value)
        elif isinstance(value, tuple):
            self.set_ctime(*value)
        else:
            seconds, fraction = math.modf(value)
            self.set_ctime(int(seconds), int(fraction * 1_000_000_000))

    def set_ctime(self, timestamp_sec, timestamp_nsec=0):
        "Kept for backward compatibility. `entry.ctime = ...` is supported now."
        return ffi.entry_set_ctime(self._entry_p, timestamp_sec, timestamp_nsec)

    @property
    def birthtime(self):
        if not ffi.entry_birthtime_is_set(self._entry_p):
            return None
        sec_val = ffi.entry_birthtime(self._entry_p)
        nsec_val = ffi.entry_birthtime_nsec(self._entry_p)
        return format_time(sec_val, nsec_val)

    @birthtime.setter
    def birthtime(self, value):
        if value is None:
            ffi.entry_unset_birthtime(self._entry_p)
        elif isinstance(value, int):
            self.set_birthtime(value)
        elif isinstance(value, tuple):
            self.set_birthtime(*value)
        else:
            seconds, fraction = math.modf(value)
            self.set_birthtime(int(seconds), int(fraction * 1_000_000_000))

    def set_birthtime(self, timestamp_sec, timestamp_nsec=0):
        "Kept for backward compatibility. `entry.birthtime = ...` is supported now."
        return ffi.entry_set_birthtime(
            self._entry_p, timestamp_sec, timestamp_nsec
        )

    @property
    def pathname(self):
        path = ffi.entry_pathname_w(self._entry_p)
        if not path:
            path = ffi.entry_pathname(self._entry_p)
            if path is not None:
                try:
                    path = path.decode(self.header_codec)
                except UnicodeError:
                    pass
        return path

    @pathname.setter
    def pathname(self, value):
        if not isinstance(value, bytes):
            value = value.encode(self.header_codec)
        if self.header_codec == 'utf-8':
            ffi.entry_update_pathname_utf8(self._entry_p, value)
        else:
            ffi.entry_copy_pathname(self._entry_p, value)

    @property
    def linkpath(self):
        path = (
            (
                ffi.entry_symlink_w(self._entry_p) or
                ffi.entry_symlink(self._entry_p)
            ) if self.issym else (
                ffi.entry_hardlink_w(self._entry_p) or
                ffi.entry_hardlink(self._entry_p)
            )
        )
        if isinstance(path, bytes):
            try:
                path = path.decode(self.header_codec)
            except UnicodeError:
                pass
        return path

    @linkpath.setter
    def linkpath(self, value):
        if not isinstance(value, bytes):
            value = value.encode(self.header_codec)
        if self.header_codec == 'utf-8':
            ffi.entry_update_link_utf8(self._entry_p, value)
        else:
            ffi.entry_copy_link(self._entry_p, value)

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
        if value is None:
            ffi.entry_unset_size(self._entry_p)
        else:
            ffi.entry_set_size(self._entry_p, value)

    @property
    def mode(self):
        return ffi.entry_mode(self._entry_p)

    @mode.setter
    def mode(self, value):
        ffi.entry_set_mode(self._entry_p, value)

    @property
    def strmode(self):
        """The file's mode as a string, e.g. '?rwxrwx---'"""
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
    def rdev(self):
        return ffi.entry_rdev(self._entry_p)

    @rdev.setter
    def rdev(self, value):
        if isinstance(value, tuple):
            ffi.entry_set_rdevmajor(self._entry_p, value[0])
            ffi.entry_set_rdevminor(self._entry_p, value[1])
        else:
            ffi.entry_set_rdev(self._entry_p, value)

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


class ConsumedArchiveEntry(ArchiveEntry):

    __slots__ = ()

    def get_blocks(self, **kw):
        raise TypeError("the content of this entry has already been read")


class PassedArchiveEntry(ArchiveEntry):

    __slots__ = ()

    def get_blocks(self, **kw):
        raise TypeError("this entry is passed, it's too late to read its content")
