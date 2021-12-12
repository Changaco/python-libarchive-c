A Python interface to libarchive. It uses the standard ctypes_ module to
dynamically load and access the C library.

.. _ctypes: https://docs.python.org/3/library/ctypes.html

Installation
============

    pip install libarchive-c

Compatibility
=============

python
------

python-libarchive-c is currently tested with python 3.7, 3.8, and 3.9.

If you find an incompatibility with older versions you can send us a small patch,
but we won't accept big changes.

libarchive
----------

python-libarchive-c may not work properly with obsolete versions of libarchive such as the ones included in MacOS. In that case you can install a recent version of libarchive (e.g. with ``brew install libarchive`` on MacOS) and use the ``LIBARCHIVE`` environment variable to point python-libarchive-c to it::

    export LIBARCHIVE=/usr/local/Cellar/libarchive/3.3.3/lib/libarchive.13.dylib

Usage
=====

Import::

    import libarchive

Extracting archives
-------------------

To extract an archive, use the ``extract_file`` function::

    os.chdir('/path/to/target/directory')
    libarchive.extract_file('test.zip')

Alternatively, the ``extract_memory`` function can be used to extract from a buffer,
and ``extract_fd`` from a file descriptor.

The ``extract_*`` functions all have an integer ``flags`` argument which is passed
directly to the C function ``archive_write_disk_set_options()``. You can import
the ``EXTRACT_*`` constants from the ``libarchive.extract`` module and see the
official description of each flag in the ``archive_write_disk(3)`` man page.

By default, when the ``flags`` argument is ``None``, the ``SECURE_NODOTDOT``,
``SECURE_NOABSOLUTEPATHS`` and ``SECURE_SYMLINKS`` flags are passed to
libarchive, unless the current directory is the root (``/``).

Reading archives
----------------

To read an archive, use the ``file_reader`` function::

    with libarchive.file_reader('test.7z') as archive:
        for entry in archive:
            for block in entry.get_blocks():
                ...

Alternatively, the ``memory_reader`` function can be used to read from a buffer,
``fd_reader`` from a file descriptor, ``stream_reader`` from a stream object
(which must support the standard ``readinto`` method), and ``custom_reader``
from anywhere using callbacks.

To learn about the attributes of the ``entry`` object, see the ``libarchive/entry.py``
source code or run ``help(libarchive.entry.ArchiveEntry)`` in a Python shell.

Displaying progress
~~~~~~~~~~~~~~~~~~~

If your program processes large archives, you can keep track of its progress
with the ``bytes_read`` attribute. Here's an example of a progress bar using
`tqdm <https://pypi.org/project/tqdm/>`_::

    with tqdm(total=os.stat(archive_path).st_size, unit='bytes') as pbar, \
         libarchive.file_reader(archive_path) as archive:
        for entry in archive:
            ...
            pbar.update(archive.bytes_read - pbar.n)

Creating archives
-----------------

To create an archive, use the ``file_writer`` function::

    from libarchive.entry import FileType

    with libarchive.file_writer('test.tar.gz', 'ustar', 'gzip') as archive:
        # Add the `libarchive/` directory and everything in it (recursively),
        # then the `README.rst` file.
        archive.add_files('libarchive/', 'README.rst')
        # Add a regular file defined from scratch.
        data = b'foobar'
        archive.add_file_from_memory('../escape-test', len(data), data)
        # Add a directory defined from scratch.
        early_epoch = (42, 42)  # 1970-01-01 00:00:42.000000042
        archive.add_file_from_memory(
            'metadata-test', 0, b'',
            filetype=FileType.DIRECTORY, permission=0o755, uid=4242, gid=4242,
            atime=early_epoch, mtime=early_epoch, ctime=early_epoch, birthtime=early_epoch,
        )

Alternatively, the ``memory_writer`` function can be used to write to a memory buffer,
``fd_writer`` to a file descriptor, and ``custom_writer`` to a callback function.

For each of those functions, the mandatory second argument is the archive format,
and the optional third argument is the compression format (called “filter” in
libarchive). The acceptable values are listed in ``libarchive.ffi.WRITE_FORMATS``
and ``libarchive.ffi.WRITE_FILTERS``.

License
=======

`CC0 Public Domain Dedication <http://creativecommons.org/publicdomain/zero/1.0/>`_
