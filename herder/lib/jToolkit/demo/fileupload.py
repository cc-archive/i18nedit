#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""this is a Hello World-style demonstration program of jToolkit"""

from jToolkit.web import server
from jToolkit.widgets import widgets
import os
import datetime

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

uploadhtml = """
<html>
<head>
 <title>Upload files</title>
</head>
<body>
 <p>
 <form enctype="multipart/form-data" action="" method="post">
  <input type="file" name="upload"/>
  <input type="submit" value = "Upload"/>
 </form>
 </p>
 <p id='message'/>
 <pre id='filelist'/>
</body>
</html>
"""

class FileUploadServer(server.AppServer):
  """the Server that serves the File Upload Pages"""
  def getpage(self, pathwords, session, argdict):
    """return a page that will be sent to the user"""
    if pathwords:
      top = pathwords[0]
    else:
      top = ''
    if top in ('', 'index.html'):
      uploadcontents = uploadhtml
      if argdict.has_key("upload"):
        upload = argdict["upload"]
        if upload.filename:
          upload.savecontents(upload.filename)
          uploadcontents = uploadcontents.replace("<p id='message'/>", "<p id='message'>saved %s</>" % upload.filename)
      filelist = ["<span style='color:blue'>%s %s  %s  %s</span>" % ('filename'.ljust(32), 'size'.rjust(10), 'created'.ljust(20), 'modified'.ljust(20))]
      try:
        filenames = os.listdir(self.instance.attachmentsdir)
        self.errorhandler.logtrace("%r %r" % (self.instance.attachmentsdir, filenames))
      except OSError, e:
        filelist = ["<span style='color:red'>Error reading directory: %s</span>" % e]
        filenames = []
      for filename in filenames:
        pathname = os.path.join(self.instance.attachmentsdir, filename)
        if not os.path.isfile(pathname) or filename.startswith("."):
          continue
        filestat = os.stat(pathname)
        ctime = datetime.datetime.fromtimestamp(filestat.st_ctime)
        mtime = datetime.datetime.fromtimestamp(filestat.st_mtime)
        filedescr = "%s %10d  %s  %s" % (filename.ljust(32), filestat.st_size, str(ctime).ljust(20), str(mtime).ljust(20))
        filelist.append(filedescr)
      filelist = "\n".join(filelist)
      uploadcontents = uploadcontents.replace("<pre id='filelist'/>", "<pre id='filelist'>%s</pre>" % filelist)
      page = widgets.PlainContents(uploadcontents)
      return page
    else:
      return None

if __name__ == '__main__':
  # run the web server
  from jToolkit.web import simplewebserver
  parser = simplewebserver.WebOptionParser()
  parser.set_default('prefsfile', 'fileupload.prefs')
  parser.set_default('instance', 'FileUploadConfig')
  parser.set_default('htmldir', "html")
  options, args = parser.parse_args()
  server = parser.getserver(options)
  simplewebserver.run(server, options)

