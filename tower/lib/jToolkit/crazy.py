#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jToolkit import prefs

if __name__ == "__main__":
  import sys
  parser = prefs.PrefsParser()
  originalsource = sys.stdin.read()
  parser.parse(originalsource)
  recreatedsource = parser.getsource()
  if recreatedsource != originalsource:
    print >>sys.stderr, "recreatedsource != originalsource"
  setattr(parser.test, "test-me", "newvalue")
  setattr(parser.test, "test-crazy", "newvalue")
  newtest = getattr(getattr(parser, "new-test", None), "test-crazy", "")
  setattr(parser, "new-test.test-crazy", newtest + "newvalue")
  recreatedsource = parser.getsource()
  sys.stdout.write(recreatedsource)


