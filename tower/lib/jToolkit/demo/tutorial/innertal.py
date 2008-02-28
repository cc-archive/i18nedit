#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from jToolkit.web import templateserver

class RequestHandler(templateserver.RequestHandler):
  def __init__(self, req):
    templateserver.RequestHandler.__init__(self, req)
    self.templatevars.update(self.getvars())

  def getvars(self):
    todaysdate = datetime.datetime.now()
    # return {"today": todaysdate.strftime("%d/%m/%Y %H:%M:%S")}
    return {"today": str(todaysdate)}
    # return {"today": "Monday"}

