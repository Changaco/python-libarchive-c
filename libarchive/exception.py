# This file is part of a program licensed under the terms of the GNU Lesser
# General Public License version 2 (or at your option any later version)
# as published by the Free Software Foundation: http://www.gnu.org/licenses/


from __future__ import division, print_function, unicode_literals


class ArchiveError(Exception):

    def __init__(self, msg, errno=None, retcode=None, archive_p=None):
        self.msg = msg
        self.errno = errno
        self.retcode = retcode
        self.archive_p = archive_p

    def __str__(self):
        p = '%s (errno=%s, retcode=%s, archive_p=%s)'
        return p % (self.msg, self.errno, self.retcode, self.archive_p)
