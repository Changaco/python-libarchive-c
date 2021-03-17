"""
This is a modified version of Victor Stinner's pure-Python implementation of
PEP 383: the "surrogateescape" error handler of Python 3.

This code is released under the Python license and the BSD 2-clause license

Source: misc/python/surrogateescape.py in https://bitbucket.org/haypo/misc
"""

from __future__ import division, print_function, unicode_literals

import codecs


chr = __builtins__.get('unichr', chr)


def surrogateescape(exc):
    if isinstance(exc, UnicodeDecodeError):
        decoded = []
        for code in exc.object[exc.start:exc.end]:
            if not isinstance(code, int):
                code = ord(code)
            if 0x80 <= code <= 0xFF:
                decoded.append(chr(0xDC00 + code))
            elif code <= 0x7F:
                decoded.append(chr(code))
            else:
                raise exc
        return (''.join(decoded), exc.end)
    elif isinstance(exc, UnicodeEncodeError):
        encoded = []
        for ch in exc.object[exc.start:exc.end]:
            code = ord(ch)
            if not 0xDC80 <= code <= 0xDCFF:
                raise exc
            encoded.append(chr(code - 0xDC00))
        return (''.join(encoded), exc.end)
    else:
        raise exc


def register():
    """Register the surrogateescape error handler if it doesn't exist
    """
    try:
        codecs.lookup_error('surrogateescape')
    except LookupError:
        codecs.register_error('surrogateescape', surrogateescape)
