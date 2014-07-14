# This file is part of a program licensed under the terms of the GNU Lesser
# General Public License version 2 (or at your option any later version)
# as published by the Free Software Foundation: http://www.gnu.org/licenses/


class ArchiveError(Exception):
    def __init__(self, msg, **kw):
        Exception.__init__(self, msg)
        self.__dict__.update(kw)
