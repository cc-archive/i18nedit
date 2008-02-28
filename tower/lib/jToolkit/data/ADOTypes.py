# -*- coding: utf-8 -*-
"""This module contains the enum definitions for ADO type constants taken from VC++ ADOINT.H
used by PyADO.py"""

# Copyright 2002, 2003 St James Software
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

# array/vector/byref types
# couldn't find this in adoint.h so
# these are currently set to 0 which means they'll be ignored
adArray = 0
adByRef = 0
adVector = 0

# DataTypeEnum
# actual standard types
adEmpty = 0
adTinyInt = 16
adSmallInt = 2
adInteger = 3
adBigInt = 20
adUnsignedTinyInt = 17
adUnsignedSmallInt = 18
adUnsignedInt = 19
adUnsignedBigInt = 21
adSingle = 4
adDouble = 5
adCurrency = 6
adDecimal = 14
adNumeric = 131
adBoolean = 11
adError = 10
adUserDefined = 132
adVariant = 12
adIDispatch = 9
adIUnknown = 13
adGUID = 72
adDate = 7
adDBDate = 133
adDBTime = 134
adDBTimeStamp = 135
adBSTR = 8
adChar = 129
adVarChar = 200
adLongVarChar = 201
adWChar = 130
adVarWChar = 202
adLongVarWChar = 203
adBinary = 128
adVarBinary = 204
adLongVarBinary = 205
adChapter = 136
adFileTime = 64
adDBFileTime = 137
adPropVariant = 138
adVarNumeric = 139

# FieldAttributesEnum
# at the moment we just use adFldMayBeNull
adFldUnspecified = -1
adFldMayDefer = 0x2
adFldUpdatable = 0x4
adFldUnknownUpdatable = 0x8
adFldFixed = 0x10
adFldIsNullable = 0x20
adFldMayBeNull = 0x40
adFldLong = 0x80
adFldRowID = 0x100
adFldRowVersion = 0x200
adFldCacheDeferred = 0x1000
adFldNegativeScale = 0x4000
adFldKeyColumn = 0x8000

