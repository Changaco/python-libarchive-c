from errno import ENOENT

import pytest

from libarchive import ArchiveError, ffi, memory_writer


def test_add_files_nonexistent():
    with memory_writer(bytes(bytearray(4096)), 'zip') as archive:
        with pytest.raises(ArchiveError) as e:
            archive.add_files('nonexistent')
        assert e.value.msg
        assert e.value.errno == ENOENT
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


def test_error_string_decoding(monkeypatch):
    monkeypatch.setattr(ffi, 'error_string', lambda *_: None)
    r = ffi._error_string(None)
    assert r is None
    monkeypatch.setattr(ffi, 'error_string', lambda *_: b'a')
    r = ffi._error_string(None)
    assert isinstance(r, type(''))
    monkeypatch.setattr(ffi, 'error_string', lambda *_: '\xe9'.encode('utf8'))
    r = ffi._error_string(None)
    assert isinstance(r, bytes)
