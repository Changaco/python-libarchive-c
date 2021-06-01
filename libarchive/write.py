from contextlib import contextmanager
from ctypes import byref, cast, c_char, c_size_t, c_void_p, POINTER
import warnings

from . import ffi
from .entry import ArchiveEntry, new_archive_entry
from .ffi import (
    OPEN_CALLBACK, WRITE_CALLBACK, CLOSE_CALLBACK, NO_OPEN_CB, NO_CLOSE_CB,
    REGULAR_FILE, DEFAULT_UNIX_PERMISSION, ARCHIVE_EOF,
    page_size, entry_sourcepath, entry_clear, read_disk_new, read_disk_open_w,
    read_next_header2, read_disk_descend, read_free, write_header, write_data,
    write_finish_entry, entry_set_size, entry_set_filetype, entry_set_perm,
    read_disk_set_behavior
)


@contextmanager
def new_archive_read_disk(path, flags=0, lookup=False):
    archive_p = read_disk_new()
    read_disk_set_behavior(archive_p, flags)
    if lookup:
        ffi.read_disk_set_standard_lookup(archive_p)
    read_disk_open_w(archive_p, path)
    try:
        yield archive_p
    finally:
        read_free(archive_p)


class ArchiveWrite:

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

    def add_files(self, *paths, **kw):
        """Read the given paths from disk and add them to the archive.

        The keyword arguments (`**kw`) are passed to `new_archive_read_disk`.
        """
        write_p = self._pointer

        block_size = ffi.write_get_bytes_per_block(write_p)
        if block_size <= 0:
            block_size = 10240  # pragma: no cover

        with new_archive_entry() as entry_p:
            entry = ArchiveEntry(None, entry_p)
            for path in paths:
                with new_archive_read_disk(path, **kw) as read_p:
                    while 1:
                        r = read_next_header2(read_p, entry_p)
                        if r == ARCHIVE_EOF:
                            break
                        entry.pathname = entry.pathname.lstrip('/')
                        read_disk_descend(read_p)
                        write_header(write_p, entry_p)
                        if entry.isreg:
                            with open(entry_sourcepath(entry_p), 'rb') as f:
                                while 1:
                                    data = f.read(block_size)
                                    if not data:
                                        break
                                    write_data(write_p, data, len(data))
                        write_finish_entry(write_p)
                        entry_clear(entry_p)

    def add_file_from_memory(
        self, entry_path, entry_size, entry_data,
        filetype=REGULAR_FILE, permission=DEFAULT_UNIX_PERMISSION,
        atime=None, mtime=None, ctime=None, birthtime=None,
    ):
        """"Add file from memory to archive.

        :param entry_path: where entry should be places in archive
        :type entry_path: str
        :param entry_size: entire size of entry in bytes
        :type entry_size: int
        :param entry_data: content of entry
        :type entry_data: bytes or Iterable[bytes]
        :param filetype: which type of file: normal, symlink etc.
        should entry be created as
        :type filetype: octal number
        :param permission: with which permission should entry be created
        :type permission: octal number
        :param atime: Last access time
        :type atime: int seconds or tuple (int seconds, int nanoseconds)
        :param mtime: Last modified time
        :type mtime: int seconds or tuple (int seconds, int nanoseconds)
        :param ctime: Creation time
        :type ctime: int seconds or tuple (int seconds, int nanoseconds)
        :param birthtime: Birth time (for archive formats that support it)
        :type birthtime: int seconds or tuple (int seconds, int nanoseconds)
        """
        archive_pointer = self._pointer

        if isinstance(entry_data, bytes):
            entry_data = (entry_data,)
        elif isinstance(entry_data, str):
            raise TypeError(
                "entry_data: expected bytes, got %r" % type(entry_data)
            )

        with new_archive_entry() as archive_entry_pointer:
            archive_entry = ArchiveEntry(None, archive_entry_pointer)

            archive_entry.pathname = entry_path
            entry_set_size(archive_entry_pointer, entry_size)
            entry_set_filetype(archive_entry_pointer, filetype)
            entry_set_perm(archive_entry_pointer, permission)

            if atime is not None:
                if not isinstance(atime, tuple):
                    atime = (atime, 0)
                archive_entry.set_atime(*atime)
            if mtime is not None:
                if not isinstance(mtime, tuple):
                    mtime = (mtime, 0)
                archive_entry.set_mtime(*mtime)
            if ctime is not None:
                if not isinstance(ctime, tuple):
                    ctime = (ctime, 0)
                archive_entry.set_ctime(*ctime)
            if birthtime is not None:
                if not isinstance(birthtime, tuple):
                    birthtime = (birthtime, 0)
                archive_entry.set_birthtime(*birthtime)
            write_header(archive_pointer, archive_entry_pointer)

            for chunk in entry_data:
                if not chunk:
                    break
                write_data(archive_pointer, chunk, len(chunk))

            write_finish_entry(archive_pointer)
            entry_clear(archive_entry_pointer)


@contextmanager
def new_archive_write(format_name, filter_name=None, options='', passphrase=None):
    archive_p = ffi.write_new()
    try:
        ffi.get_write_format_function(format_name)(archive_p)
        if filter_name:
            ffi.get_write_filter_function(filter_name)(archive_p)
        if passphrase and 'encryption' not in options:
            if format_name == 'zip':
                warnings.warn(
                    "The default encryption scheme of zip archives is weak. "
                    "Use `options='encryption=$type'` to specify the encryption "
                    "type you want to use. The supported values are 'zipcrypt' "
                    "(the weak default), 'aes128' and 'aes256'."
                )
            options += ',encryption' if options else 'encryption'
        if options:
            if not isinstance(options, bytes):
                options = options.encode('utf-8')
            ffi.write_set_options(archive_p, options)
        if passphrase:
            if not isinstance(passphrase, bytes):
                passphrase = passphrase.encode('utf-8')
            try:
                ffi.write_set_passphrase(archive_p, passphrase)
            except AttributeError:
                raise NotImplementedError(
                    f"the libarchive being used (version {ffi.version_number()}, "
                    f"path {ffi.libarchive_path}) doesn't support encryption"
                )
        yield archive_p
        ffi.write_close(archive_p)
        ffi.write_free(archive_p)
    except Exception:
        ffi.write_fail(archive_p)
        ffi.write_free(archive_p)
        raise


@contextmanager
def custom_writer(
    write_func, format_name, filter_name=None,
    open_func=None, close_func=None, block_size=page_size,
    archive_write_class=ArchiveWrite, options='', passphrase=None,
):

    def write_cb_internal(archive_p, context, buffer_, length):
        data = cast(buffer_, POINTER(c_char * length))[0]
        return write_func(data)

    open_cb = OPEN_CALLBACK(open_func) if open_func else NO_OPEN_CB
    write_cb = WRITE_CALLBACK(write_cb_internal)
    close_cb = CLOSE_CALLBACK(close_func) if close_func else NO_CLOSE_CB

    with new_archive_write(format_name, filter_name, options,
                           passphrase) as archive_p:
        ffi.write_set_bytes_in_last_block(archive_p, 1)
        ffi.write_set_bytes_per_block(archive_p, block_size)
        ffi.write_open(archive_p, None, open_cb, write_cb, close_cb)
        yield archive_write_class(archive_p)


@contextmanager
def fd_writer(
    fd, format_name, filter_name=None,
    archive_write_class=ArchiveWrite, options='', passphrase=None,
):
    with new_archive_write(format_name, filter_name, options,
                           passphrase) as archive_p:
        ffi.write_open_fd(archive_p, fd)
        yield archive_write_class(archive_p)


@contextmanager
def file_writer(
    filepath, format_name, filter_name=None,
    archive_write_class=ArchiveWrite, options='', passphrase=None,
):
    with new_archive_write(format_name, filter_name, options,
                           passphrase) as archive_p:
        ffi.write_open_filename_w(archive_p, filepath)
        yield archive_write_class(archive_p)


@contextmanager
def memory_writer(
    buf, format_name, filter_name=None,
    archive_write_class=ArchiveWrite, options='', passphrase=None,
):
    with new_archive_write(format_name, filter_name, options,
                           passphrase) as archive_p:
        used = byref(c_size_t())
        buf_p = cast(buf, c_void_p)
        ffi.write_open_memory(archive_p, buf_p, len(buf), used)
        yield archive_write_class(archive_p)
