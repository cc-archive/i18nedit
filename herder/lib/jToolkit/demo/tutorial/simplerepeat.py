#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jToolkit.web import templateserver

class RequestHandler(templateserver.RequestHandler):
  def __init__(self, req):
    templateserver.RequestHandler.__init__(self, req)
    self.templatevars.update(self.getvars())

  def getvars(self):
    return {"colors": ["red", "green", "blue"]}

