#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from jToolkit.xml import taldom
from jToolkit.web import templateserver

class RequestHandler(templateserver.RequestHandler):
  def __init__(self, req):
    templateserver.RequestHandler.__init__(self, req)
    self.templatevars.update(self.getvars())

  def getvars(self):
    if "usetal" in self.argdict:
      newtalimp = self.argdict["usetal"]
      if newtalimp == "simpleTAL":
        taldom.usesimpleTAL()
      elif newtalimp == "jToolkitTAL":
        taldom.usejToolkitTAL()
      else:
        raise KeyError("Unknown TAL implementation requested")
    todaysdate = datetime.datetime.now()
    return {"today": str(todaysdate), "taldom": str(taldom.implementation)}

