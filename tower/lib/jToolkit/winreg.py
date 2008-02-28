#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""this is a simple wrapper class for the windows registry"""

# Copyright 2004 St James Software
# 
# This file is part of jToolkit.
#
# jToolkit is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# jToolkit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with jToolkit; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import win32api

class nullregkey:
    """
    a registry key that doesn't exist...
    """
    def childkey(self, subkeyname):
        return nullregkey()

    def subkeynames(self):
        return []

    def getvalue(self, valuename):
        raise AttributeError("Cannot access registry value %r: key does not exist" % (valuename))

class regkey:
    """
    simple wrapper for registry functions that closes keys nicely...
    """
    def __init__(self, parent, subkeyname):
       self.key = win32api.RegOpenKey(parent, subkeyname)

    def childkey(self, subkeyname):
       try:
           return regkey(self.key, subkeyname)
       except win32api.error:
           return nullregkey()

    def subkeynames(self):
       numsubkeys = win32api.RegQueryInfoKey(self.key)[0]
       return [win32api.RegEnumKey(self.key, index) for index in range(numsubkeys)]

    def getvalue(self, valuename):
       try:
           return win32api.RegQueryValueEx(self.key, valuename)
       except win32api.error:
           raise AttributeError("Cannot access registry value %r" % (valuename))

    def __del__(self):
       if hasattr(self, "key"):
           win32api.RegCloseKey(self.key)

