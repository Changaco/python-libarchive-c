# This file is part of a program licensed under the terms of the GNU Lesser
# General Public License version 2 (or at your option any later version)
# as published by the Free Software Foundation: http://www.gnu.org/licenses/


from __future__ import division, print_function, unicode_literals

import pytest

from libarchive import ArchiveError, ffi, memory_writer


def test_add_files_nonexistent():
    with memory_writer(bytes(bytearray(4096)), 'zip') as archive:
        with pytest.raises(ArchiveError) as e:
            archive.add_files('nonexistent')
        assert e.value.msg
        assert e.value.errno == 2
        assert e.value.retcode == -25


def test_check_int_logs_warnings(monkeypatch):
    calls = []
    monkeypatch.setattr(ffi.logger, 'warning', lambda *_: calls.append(1))
    archive_p = ffi.write_new()
    ffi.check_int(ffi.ARCHIVE_WARN, print, [archive_p])
    assert calls == [1]


def test_check_null():
    with pytest.raises(ArchiveError) as e:
        ffi.check_null(None, print, [])
    assert str(e)
