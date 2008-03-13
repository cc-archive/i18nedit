#!/usr/bin/env python

import tidy

def tidyhtml(html):
    """simply tidies up html code, returning xhtml"""
    if isinstance(html, unicode):
        html = html.encode("utf-8")
    html = tidy.parseString(html, output_xhtml=1, tidy_mark=0, input_encoding="utf8", output_encoding="utf8")
    html = str(html)
    return html

def tidywidget(widget):
    """gets clean xhtml source for the widget by passing through tidy"""
    divstart = "<div id='tidywidget'>"
    divend = '</div>'
    html = "<html><body>" + divstart + widget.gethtml() + divend + "</body></html>"
    html = tidyhtml(html)
    divpos = html.find(divstart)
    if divpos == -1:
      divpos = html.find(divstart.replace("'", '"'))
    if divpos == -1:
      raise ValueError("Error finding div in tidied html")
    divendpos = html.rfind(divend)
    if divendpos == -1:
      raise ValueError("Error finding div end in tidied html")
    return html[divpos+len(divstart):divendpos]

def htmlresult(widgetfunction):
    """decorator that calls widget.gethtml() on the results of its function"""
    def tidyfunction(*args, **kwargs):
      result = widgetfunction(*args, **kwargs)
      return result
    return tidyfunction

def tidyresult(widgetfunction):
    """decorator that calls tidy(widget.gethtml()) on the results of its function"""
    def tidyfunction(*args, **kwargs):
      result = widgetfunction(*args, **kwargs)
      cleanhtml = tidywidget(result)
      return cleanhtml
    return tidyfunction

