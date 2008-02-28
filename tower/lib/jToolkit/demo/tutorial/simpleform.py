#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from jToolkit.web import templateserver

class ColorFormRequestHandler(templateserver.RequestHandler):
  def __init__(self, req):
    templateserver.RequestHandler.__init__(self, req)
    self.favorite = None
    self.handleaction("dosave")
    self.templatevars.update(self.getvars())
  def dosave(self):
    self.favorite = self.argdict["color"]
    print "saving color", self.favorite
    return {"message": "saved favorite color somewhere", "color": self.favorite}
  def getvars(self):
    colors = ["red", "green", "blue"]
    colors = [color for color in colors if color != self.favorite]
    return {"colors": colors}
