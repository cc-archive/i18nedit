#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from xml.dom import minidom
from jToolkit.web import templateserver

class TutorialRequestHandler(templateserver.RequestHandler):
  def __init__(self, req):
    templateserver.RequestHandler.__init__(self, req)
    self.templatevars.update(self.getvars())
  
  def getvars(self):
    directory = os.path.dirname(os.path.abspath(__file__))
    pages = []
    for filename in os.listdir(directory):
      if filename.endswith(".html"):
        contents = open(filename, 'r').read()
        sourcedom = minidom.parseString(contents)
        titles = sourcedom.getElementsByTagName("title")
        title = ""
        for titlenode in titles:
          for node in titlenode.childNodes:
            if node.nodeType == node.TEXT_NODE:
               title += " " + node.data
        title = title.strip()
        basename = os.path.basename(filename)
        if not title:
          title = basename[:-len(".html")]
        page = {"href": basename, "title": title, "htmlsrc": "src/"+basename}
        pyname = filename[:-len(".html")]+".py"
        if os.path.exists(pyname):
          page["pysrc"] = "src/" + os.path.basename(pyname)
        pages.append(page)
    return {"pages": pages}

