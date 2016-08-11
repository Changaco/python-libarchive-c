from __future__ import division, print_function, unicode_literals

from contextlib import contextmanager
from ctypes import byref, cast, c_char, c_size_t, c_void_p, POINTER
from errno import EISDIR

from . import ffi
from .entry import ArchiveEntry, new_archive_entry
from .ffi import (
    OPEN_CALLBACK, WRITE_CALLBACK, CLOSE_CALLBACK, VOID_CB, REGULAR_FILE,
    DEFAULT_UNIX_PERMISSION, ARCHIVE_EOF,
    page_size, entry_sourcepath, entry_clear, read_disk_new, read_disk_open_w,
    read_next_header2, read_disk_descend, read_free, write_header, write_data,
    write_finish_entry, entry_set_pathname, entry_set_size, entry_set_filetype,
    entry_set_perm
)


@contextmanager
def new_archive_read_disk(path):
    archive_p = read_disk_new()
    read_disk_open_w(archive_p, path)
    try:
        yield archive_p
    finally:
        read_free(archive_p)


class ArchiveWrite(object):

    def __init__(self, archive_p):
        self._pointer = archive_p

    def add_entries(self, entries):
        """Add the given entries to the archive.
        """
        write_p = self._pointer
        for entry in entries:
            write_header(write_p, entry._entry_p)
            for block in entry.get_blocks():
                write_data(write_p, block, len(block))
            write_finish_entry(write_p)

    def add_files(self, *paths):
        """Read the given paths from disk and add them to the archive.
        """
        write_p = self._pointer

        block_size = ffi.write_get_bytes_per_block(write_p)
        if block_size <= 0:
            block_size = 10240  # pragma: no cover

        with new_archive_entry() as entry_p:
            entry = ArchiveEntry(None, entry_p)
            for path in paths:
                with new_archive_read_disk(path) as read_p:
                    while 1:
                        r = read_next_header2(read_p, entry_p)
                        if r == ARCHIVE_EOF:
                            break
                        entry.pathname = entry.pathname.lstrip('/')
                        read_disk_descend(read_p)
                        write_header(write_p, entry_p)
                        try:
                            with open(entry_sourcepath(entry_p), 'rb') as f:
                                while 1:
                                    data = f.read(block_size)
                                    if not data:
                                        break
                                    write_data(write_p, data, len(data))
                        except IOError as e:
                            if e.errno != EISDIR:
                                raise  # pragma: no cover
                        write_finish_entry(write_p)
                        entry_clear(entry_p)

    def add_entry_from_memory(self, entry):
        """"Add file from memory to archive.
        :param entry: `Entry` with path, size, iterable args
        :type entry: object
        """
        archive_pointer = self._pointer

        with new_archive_entry() as archive_entry_pointer:
            self._create_entry_archive(archive_entry_pointer, entry)

            for chunk in entry.iterable:
                if not chunk:
                    break
                write_data(archive_pointer, chunk, len(chunk))

            self._close_entry_archive(archive_entry_pointer)

    def _create_entry_archive(self, archive_entry_pointer, entry):
        """Helper for setting up necessary entry parameters."""
        archive_entry = ArchiveEntry(None, archive_entry_pointer)

        entry_set_pathname(archive_entry_pointer, entry.path)
        archive_entry.pathname = entry.path
        entry_set_size(archive_entry_pointer, entry.size)
        entry_set_filetype(archive_entry_pointer, REGULAR_FILE)
        entry_set_perm(archive_entry_pointer, DEFAULT_UNIX_PERMISSION)
        write_header(self._pointer, archive_entry_pointer)

    def _close_entry_archive(self, archive_entry_pointer):
        """Helper for closing archive."""
        write_finish_entry(self._pointer)
        entry_clear(archive_entry_pointer)


@contextmanager
def new_archive_write(format_name, filter_name=None):
    archive_p = ffi.write_new()
    getattr(ffi, 'write_set_format_'+format_name)(archive_p)
    if filter_name:
        getattr(ffi, 'write_add_filter_'+filter_name)(archive_p)
    try:
        yield archive_p
    finally:
        ffi.write_close(archive_p)
        ffi.write_free(archive_p)


@contextmanager
def custom_writer(write_func, format_name, filter_name=None,
                  open_func=VOID_CB, close_func=VOID_CB, block_size=page_size):

    def write_cb_internal(archive_p, context, buffer_, length):
        data = cast(buffer_, POINTER(c_char * length))[0]
        return write_func(data)

    open_cb = OPEN_CALLBACK(open_func)
    write_cb = WRITE_CALLBACK(write_cb_internal)
    close_cb = CLOSE_CALLBACK(close_func)

    with new_archive_write(format_name, filter_name) as archive_p:
        ffi.write_set_bytes_in_last_block(archive_p, 1)
        ffi.write_set_bytes_per_block(archive_p, block_size)
        ffi.write_open(archive_p, None, open_cb, write_cb, close_cb)
        yield ArchiveWrite(archive_p)


@contextmanager
def fd_writer(fd, format_name, filter_name=None):
    with new_archive_write(format_name, filter_name) as archive_p:
        ffi.write_open_fd(archive_p, fd)
        yield ArchiveWrite(archive_p)


@contextmanager
def file_writer(filepath, format_name, filter_name=None):
    with new_archive_write(format_name, filter_name) as archive_p:
        ffi.write_open_filename_w(archive_p, filepath)
        yield ArchiveWrite(archive_p)


@contextmanager
def memory_writer(buf, format_name, filter_name=None):
    with new_archive_write(format_name, filter_name) as archive_p:
        used = byref(c_size_t())
        buf_p = cast(buf, c_void_p)
        ffi.write_open_memory(archive_p, buf_p, len(buf), used)
        yield ArchiveWrite(archive_p)
