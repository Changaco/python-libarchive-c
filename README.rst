.. image:: https://travis-ci.org/Changaco/python-libarchive-c.svg
  :target: https://travis-ci.org/Changaco/python-libarchive-c

A Python interface to libarchive. It uses the standard ctypes_ module to
dynamically load and access the C library.

.. _ctypes: https://docs.python.org/3/library/ctypes.html

Installation
============

    pip install libarchive-c

Compatibility
=============

python-libarchive-c is currently tested with python 2.7 and 3.5.

If you find an incompatibility with older versions you can send us a small patch, but we won't accept big changes.

Usage
=====

Import::

    import libarchive

To extract an archive to the current directory::

    libarchive.extract_file('test.zip')

``extract_memory`` extracts from a buffer instead, and ``extract_fd`` extracts
from a file descriptor.

To read an archive::

    with libarchive.file_reader('test.7z') as archive:
        for entry in archive:
            for block in entry.get_blocks():
                ...

``memory_reader`` reads from a memory buffer instead, and ``fd_reader`` reads
from a file descriptor.

To create an archive::

    with libarchive.file_writer('test.tar.gz', 'ustar', 'gzip') as archive:
        archive.add_files('libarchive/', 'README.rst')

``memory_writer`` writes to a memory buffer instead, ``fd_writer`` writes to a
file descriptor, and ``custom_writer`` sends the data to a callback function.

You can also find more thorough examples in the ``tests/`` directory.

License
=======

`CC0 Public Domain Dedication <http://creativecommons.org/publicdomain/zero/1.0/>`_
