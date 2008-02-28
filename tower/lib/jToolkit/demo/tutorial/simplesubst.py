#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from jToolkit.web import templateserver

class RequestHandler(templateserver.RequestHandler):
  def __init__(self, req):
    templateserver.RequestHandler.__init__(self, req)
    self.templatevars.update(self.getvars())

  def getvars(self):
    todaysdate = str(datetime.datetime.now())
    return {"today": todaysdate,
            "number": 42,
            "pi": 3.14159265}

