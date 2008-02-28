#!/usr/bin/python
# -*- coding: utf-8 -*-

"""constants for HTTP status codes"""

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

CONTINUE                     = 100
SWITCHING_PROTOCOLS          = 101
PROCESSING                   = 102
OK                           = 200
CREATED                      = 201
ACCEPTED                     = 202
NON_AUTHORITATIVE            = 203
NO_CONTENT                   = 204
RESET_CONTENT                = 205
PARTIAL_CONTENT              = 206
MULTI_STATUS                 = 207
MULTIPLE_CHOICES             = 300
MOVED_PERMANENTLY            = 301
MOVED_TEMPORARILY            = 302
SEE_OTHER                    = 303
NOT_MODIFIED                 = 304
USE_PROXY                    = 305
TEMPORARY_REDIRECT           = 307
BAD_REQUEST                  = 400
UNAUTHORIZED                 = 401
PAYMENT_REQUIRED             = 402
FORBIDDEN                    = 403
NOT_FOUND                    = 404
METHOD_NOT_ALLOWED           = 405
NOT_ACCEPTABLE               = 406
PROXY_AUTHENTICATION_REQUIRED= 407
REQUEST_TIME_OUT             = 408
CONFLICT                     = 409
GONE                         = 410
LENGTH_REQUIRED              = 411
PRECONDITION_FAILED          = 412
REQUEST_ENTITY_TOO_LARGE     = 413
REQUEST_URI_TOO_LARGE        = 414
UNSUPPORTED_MEDIA_TYPE       = 415
RANGE_NOT_SATISFIABLE        = 416
EXPECTATION_FAILED           = 417
UNPROCESSABLE_ENTITY         = 422
LOCKED                       = 423
FAILED_DEPENDENCY            = 424
INTERNAL_SERVER_ERROR        = 500
NOT_IMPLEMENTED              = 501
BAD_GATEWAY                  = 502
SERVICE_UNAVAILABLE          = 503
GATEWAY_TIME_OUT             = 504
VERSION_NOT_SUPPORTED        = 505
VARIANT_ALSO_VARIES          = 506
INSUFFICIENT_STORAGE         = 507
NOT_EXTENDED                 = 510
