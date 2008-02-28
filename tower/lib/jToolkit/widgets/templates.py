#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This is a match from HTMLTemplate to our widget structure"""

import HTMLTemplate
from jToolkit.widgets import widgets

class TemplateWidget(widgets.Widget, HTMLTemplate.Template):
  """A widget that generates its code using templates"""
  def __init__(self, htmltemplate, **kwargs):
    HTMLTemplate.Template.__init__(self, self.render, htmltemplate)
    self.kwargs = kwargs
    widgets.Widget.__init__(self, "template")

  def gethtml(self):
    """actually render the template"""
    return HTMLTemplate.Template.render(self)

class TestTemplate(TemplateWidget):
  def render(self, clone):
    clone.title.content = clone.kwargs["title"]

if __name__ == "__main__":
  t = TestTemplate("<h1 node='con:title'>title</h1>", title="Test")
  print t.gethtml("This title")
  print t.gethtml("That title")

