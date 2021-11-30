from contextlib import contextmanager
from ctypes import byref, cast, c_char, c_size_t, c_void_p, POINTER
from posixpath import join
import warnings

from . import ffi
from .entry import ArchiveEntry, FileType
from .ffi import (
    OPEN_CALLBACK, WRITE_CALLBACK, CLOSE_CALLBACK, NO_OPEN_CB, NO_CLOSE_CB,
    ARCHIVE_EOF,
    page_size, entry_sourcepath, entry_clear, read_disk_new, read_disk_open_w,
    read_next_header2, read_disk_descend, read_free, write_header, write_data,
    write_finish_entry,
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

    def add_files(
        self, *paths, flags=0, lookup=False, pathname=None, **attributes
    ):
        """Read files through the OS and add them to the archive.

        Args:
            paths (str): the paths of the files to add to the archive
            flags (int):
                passed to the C function `archive_read_disk_set_behavior`;
                use the `libarchive.flags.READDISK_*` constants
            lookup (bool):
                when True, the C function `archive_read_disk_set_standard_lookup`
                is called to enable the lookup of user and group names
            pathname (str | None):
                the path of the file in the archive, defaults to the source path
            attributes (dict): passed to `ArchiveEntry.modify()`

        Raises:
            ArchiveError: if a file doesn't exist or can't be accessed, or if
                          adding it to the archive fails
        """
        write_p = self._pointer

        block_size = ffi.write_get_bytes_per_block(write_p)
        if block_size <= 0:
            block_size = 10240  # pragma: no cover

        entry = ArchiveEntry()
        entry_p = entry._entry_p
        destination_path = attributes.pop('pathname', None)
        for path in paths:
            with new_archive_read_disk(path, flags, lookup) as read_p:
                while 1:
                    r = read_next_header2(read_p, entry_p)
                    if r == ARCHIVE_EOF:
                        break
                    entry_path = entry.pathname
                    if destination_path:
                        if entry_path == path:
                            entry_path = destination_path
                        else:
                            assert entry_path.startswith(path)
                            entry_path = join(
                                destination_path,
                                entry_path[len(path):].lstrip('/')
                            )
                    entry.pathname = entry_path.lstrip('/')
                    if attributes:
                        entry.modify(**attributes)
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

    def add_file(self, path, **kw):
        "Single-path alias of `add_files()`"
        return self.add_files(path, **kw)

    def add_file_from_memory(
        self, entry_path, entry_size, entry_data,
        filetype=FileType.REGULAR_FILE, permission=0o664,
        **other_attributes
    ):
        """"Add file from memory to archive.

        Args:
            entry_path (str): the file's path
            entry_size (int): the file's size, in bytes
            entry_data (bytes | Iterable[bytes]): the file's content
            filetype (int): see `libarchive.entry.ArchiveEntry.modify()`
            permission (int): see `libarchive.entry.ArchiveEntry.modify()`
            other_attributes: see `libarchive.entry.ArchiveEntry.modify()`
        """
        archive_pointer = self._pointer

        if isinstance(entry_data, bytes):
            entry_data = (entry_data,)
        elif isinstance(entry_data, str):
            raise TypeError(
                "entry_data: expected bytes, got %r" % type(entry_data)
            )

        entry = ArchiveEntry(
            pathname=entry_path, size=entry_size, filetype=filetype,
            perm=permission, **other_attributes
        )
        write_header(archive_pointer, entry._entry_p)

        for chunk in entry_data:
            if not chunk:
                break
            write_data(archive_pointer, chunk, len(chunk))

        write_finish_entry(archive_pointer)


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

    @property
    def bytes_written(self):
        return ffi.filter_bytes(self._pointer, -1)


@contextmanager
def custom_writer(
    write_func, format_name, filter_name=None,
    open_func=None, close_func=None, block_size=page_size,
    archive_write_class=ArchiveWrite, options='', passphrase=None,
):
    """Create an archive and send it in chunks to the `write_func` function.

    For formats and filters, see `WRITE_FORMATS` and `WRITE_FILTERS` in the
    `libarchive.ffi` module.
    """

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
    """Create an archive and write it into a file descriptor.

    For formats and filters, see `WRITE_FORMATS` and `WRITE_FILTERS` in the
    `libarchive.ffi` module.
    """
    with new_archive_write(format_name, filter_name, options,
                           passphrase) as archive_p:
        ffi.write_open_fd(archive_p, fd)
        yield archive_write_class(archive_p)


@contextmanager
def file_writer(
    filepath, format_name, filter_name=None,
    archive_write_class=ArchiveWrite, options='', passphrase=None,
):
    """Create an archive and write it into a file.

    For formats and filters, see `WRITE_FORMATS` and `WRITE_FILTERS` in the
    `libarchive.ffi` module.
    """
    with new_archive_write(format_name, filter_name, options,
                           passphrase) as archive_p:
        ffi.write_open_filename_w(archive_p, filepath)
        yield archive_write_class(archive_p)


@contextmanager
def memory_writer(
    buf, format_name, filter_name=None,
    archive_write_class=ArchiveWrite, options='', passphrase=None,
):
    """Create an archive and write it into a buffer.

    For formats and filters, see `WRITE_FORMATS` and `WRITE_FILTERS` in the
    `libarchive.ffi` module.
    """
    with new_archive_write(format_name, filter_name, options,
                           passphrase) as archive_p:
        used = byref(c_size_t())
        buf_p = cast(buf, c_void_p)
        ffi.write_open_memory(archive_p, buf_p, len(buf), used)
        yield archive_write_class(archive_p)
