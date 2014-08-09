A Python interface to libarchive. It uses the standard ctypes_ module to
dynamically load and access the C library.

.. _ctypes: https://docs.python.org/3/library/ctypes.html

Installation
============

    pip install libarchive-c

python-libarchive-c is compatible with python 2 and 3.

Usage
=====

Import::

    import libarchive

To extract an archive to the current directory::

    libarchive.extract_file('test.zip')

Use ``libarchive.extract_memory`` if you want to extract from a buffer instead.

To read an archive::

    with libarchive.file_reader('test.7z') as archive:
        for entry in archive:
            for block in entry.get_blocks():
                ...

Use ``libarchive.memory_reader`` if you want to read from a buffer instead.

To create an archive::

    with libarchive.file_writer('test.tar.gz', 'ustar', 'gzip') as archive:
        archive.add_files('libarchive/', 'README.rst')

Use ``libarchive.fd_writer`` if you want to write to a file descriptor instead.
