# This file is part of a program licensed under the terms of the GNU Lesser
# General Public License version 2 (or at your option any later version)
# as published by the Free Software Foundation: http://www.gnu.org/licenses/


from __future__ import division, print_function, unicode_literals

from contextlib import contextmanager
from ctypes import c_char_p, create_string_buffer

from . import ffi


@contextmanager
def new_archive_entry():
    entry_p = ffi.entry_new()
    try:
        yield entry_p
    finally:
        ffi.entry_free(entry_p)


class ArchiveEntry(object):

    def __init__(self, archive_p, entry_p):
        self._archive_p = archive_p
        self._entry_p = entry_p

    def __str__(self):
        return self.pathname

    @property
    def filetype(self):
        return ffi.entry_filetype(self._entry_p)

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
        return self.filetype & 0o170000 == 0o120000

    @property
    def isreg(self):
        return self.filetype & 0o170000 == 0o100000

    @property
    def issock(self):
        return self.filetype & 0o170000 == 0o140000

    @property
    def mtime(self):
        return ffi.entry_mtime(self._entry_p)

    @property
    def pathname(self):
        return ffi.entry_pathname_w(self._entry_p)

    @pathname.setter
    def pathname(self, value):
        if not isinstance(value, bytes):
            value = value.encode('utf8')
        ffi.entry_update_pathname_utf8(self._entry_p, c_char_p(value))

    @property
    def size(self):
        if ffi.entry_size_is_set(self._entry_p):
            return ffi.entry_size(self._entry_p)

    @property
    def mode(self):
        return ffi.entry_mode(self._entry_p)

    @property
    def strmode(self):
        return ffi.entry_strmode(self._entry_p)
