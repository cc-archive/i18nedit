#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Allows recording of all http traffic in a way that can (hopefully) be replayed later
"""      

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

from jToolkit import errors
from jToolkit import timecache
import urllib
import random
import os

# the req.parsed_uri from the apache module
URI_SCHEME = 0
URI_HOSTINFO = 1
URI_USER = 2
URI_PASSWORD = 3
URI_HOSTNAME = 4
URI_PORT = 5
URI_PATH = 6
URI_QUERY = 7
URI_FRAGMENT = 8

# TODO: add docs
# TODO: add error message logging
# TODO: add session logging
# TODO: improve argument logging

class HTTPRecorder(errors.ErrorHandler):
  def __init__(self, instance):
    errors.ErrorHandler.__init__(self, instance)
    self.pathcache = {}
    self.duppaths = {}
    self.reqtimes = {}
    self.basedir = instance.logrecord

  def getresponsefile(self, pathwords):
    return os.path.join(self.basedir, *pathwords)

  def getresponseurl(self, pathwords):
    pathwords = pathwords[:]
    pathwords[-1] = urllib.quote_plus(pathwords[-1])
    return "." + '/'.join(pathwords)

  def getresponsepath(self, req):
    uri = req.parsed_uri
    if uri[URI_HOSTNAME]:
      pathwords = '/'.join((uri[URI_HOSTNAME], uri[URI_PATH]))
    else:
      pathwords = uri[URI_PATH]
    pathwords = pathwords.split('/')
    if pathwords[-1] == '':
      pathwords[-1] = 'index.htm'
    if uri[URI_QUERY]:
      querypart = uri[URI_QUERY]
      querypart = urllib.unquote_plus(querypart)
      querypart = urllib.quote_plus("?"+querypart)
      pathwords[-1] += querypart
    return pathwords

  def openrequest(self, req):
    req.logresponse = self.logresponse
    req.allowetag = False
    pathwords = self.getresponsepath(req)
    pathkey = tuple(pathwords)
    if hasattr(req, "record_timestamp"):
      self.logrequestmessage("request processed again: %s, %s<br/>\n" % (req.uri, req.record_timestamp))
    else:
      req.record_timestamp = "%x%04x" % (req.request_time, random.randint(0,65535))
    if pathkey in self.pathcache or os.path.isfile(self.getresponsefile(pathwords)):
      pathwords[-1] += urllib.quote_plus("&record_time=%s" % (req.record_timestamp))
      if pathkey not in self.duppaths:
        self.duppaths[pathkey] = {}
        if not pathkey in self.pathcache:
          self.pathcache[pathkey] = pathwords
        if pathkey in self.reqtimes:
          self.duppaths[pathkey][self.reqtimes[pathkey]] = self.pathcache[pathkey]
      self.duppaths[pathkey][req.record_timestamp] = pathwords
      return pathwords
    else:
      self.pathcache[pathkey] = pathwords
      self.reqtimes[pathkey] = req.record_timestamp
      return pathwords

  def closerequest(self, req):
    pathwords = self.getresponsepath(req)
    pathkey = tuple(pathwords)
    if pathkey not in self.pathcache or not hasattr(req, "record_timestamp"):
      pathwords[-1] += urllib.quote_plus("&record_error=notfound")
      return pathwords
    if pathkey in self.duppaths:
      return self.duppaths[pathkey][req.record_timestamp]
    else:
      return self.pathcache[pathkey]

  def logrequest(self, req):
    pathwords = self.openrequest(req)
    responseurl = self.getresponseurl(pathwords)
    self.logrequestmessage("request <a href='%s'>%s</a><br/>\n" % (responseurl, req.the_request))

  def logrequestmessage(self, logmessage):
    requestslog = os.path.join(self.basedir, "requests.htm")
    self.writelog(requestslog, logmessage)

  def logresponse(self, req, response):
    pathwords = self.closerequest(req)
    responseurl = self.getresponseurl(pathwords)
    self.logrequestmessage("response <a href='%s'>%s</a><br/>\n" % (responseurl, req.unparsed_uri))
    responsefilename = self.getresponsefile(pathwords)
    responsedir = os.path.abspath(os.path.dirname(responsefilename))
    if not os.path.isdir(responsedir):
      baseparts = os.path.abspath(self.basedir).split(os.path.sep)
      subparts = responsedir.split(os.path.sep)[len(baseparts):]
      currentpath = self.basedir
      for part in subparts:
        currentpath = os.path.join(currentpath, part)
        if not os.path.isdir(currentpath):
          os.mkdir(currentpath)
    try:
      responsefile = open(responsefilename,'w')
    except IOError, e:
      # TODO: handle filenames that are too long...
      self.logrequestmessage("IOError opening response filename %s: %s\n" % (responsefilename, e))
      return
    if isinstance(response, unicode):
      responsefile.write(response.encode('utf8'))
    else:
      responsefile.write(response)
    responsefile.close()


