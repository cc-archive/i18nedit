#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jToolkit.web import templateserver

class RequestHandler(templateserver.RequestHandler):
  def __init__(self, req):
    templateserver.RequestHandler.__init__(self, req)
    self.templatevars.update(self.getvars())

  def getvars(self):
    talattrs = self.template.findtalattrs()
    talattrs = ["%s %s %s" % (nodetype, attrname, attrvalue) for (nodetype, attrname, attrvalue) in talattrs]
    talvars = self.template.findtalvarnames()
    return {"colors": ["red", "green", "blue"], "number": 42.1415926, "talattrs": talattrs, "talvars": talvars}

