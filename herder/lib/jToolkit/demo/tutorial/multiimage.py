#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from jToolkit.web import templateserver

class RequestHandler(templateserver.RequestHandler):
  def __init__(self, req):
    templateserver.RequestHandler.__init__(self, req)
    self.templatevars.update(self.getvars())

  def getvars(self):
    directory = "/share/photos/brazil/thumb/a/"
    images = []
    for filename in os.listdir(directory):
      if filename.endswith(".jpg"):
        images.append({"src": "/photos/" + filename})
    return {"images": images}

