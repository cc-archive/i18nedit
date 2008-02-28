#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A simple wrapper class for the matplotlib chart module."""

# Copyright 2002, 2003 St James Software
# 
# This file is part of jToolkit.
#
# jToolkit is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# jToolkit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with jToolkit; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import cStringIO, tempfile, os, math
from jToolkit.widgets import widgets
from jToolkit.data import dates
from jToolkit import errors
import random, os, time
import sys

sys.stderr = sys.stdout   #Solve a problem with the font manager
if not hasattr(sys, "argv"):
  # matplotlib expects an argv...
  sys.argv = []
matplotlib_import_error = None
matplotlib_import_traceback = None

# TODO: improve error handling here...
try:
  # TODO: change to from matplotlib import matlab...
  os.environ['MATPLOTLIBDATA'] = os.path.join(sys.prefix, 'share', 'matplotlib')
  import matplotlib
  matplotlib.use('Agg')
  import matplotlib.pylab as matlab
  from matplotlib import ticker
  from matplotlib import dates as matdates
except Exception, e:
  # not importing these functions will cause charts to fail...
  errorhandler = errors.ConsoleErrorHandler()
  matplotlib_import_error = str(e)
  matplotlib_import_traceback = errorhandler.traceback_str()
  # print "error importing matplotlib. jToolkit.widgets.chart functions will fail later."
  raise

#We need this lock for gdchart, as it's not thread-safe
#from threading import Lock
#gdchartLock = Lock()

#Graph type constants
LINE_CHART = 0
BAR_CHART = 1

class jMajorDateLocator(matdates.DayLocator):
  def __call__(self):
    self.verify_intervals()
    vmin, vmax = self.viewInterval.get_bounds()

    ret = [vmin]
    ret.extend(matdates.DayLocator.__call__(self))
    ret.append(vmax)
    return ret

class jMinorLinearLocator(ticker.LinearLocator):
  """The purpose of this class is to create a LinearLocator that does not return vmin or vmax"""
  def __init__(self, numticks=None, presets=None):
    if numticks is not None:
      numticks += 2     # We strip these out in __call__
    ticker.LinearLocator.__init__(self, numticks, presets)

  def __call__(self):
    self.verify_intervals()
    vmin, vmax = self.viewInterval.get_bounds()

    ret = ticker.LinearLocator.__call__(self)[1:-1]
    return ret
    
class jMinuteLocator(matdates.MinuteLocator):
  """The purpose of this class is to ignore the change of day tick, so it doesn't overlap and look ugly"""
  def __call__(self):
    dates = matdates.MinuteLocator.__call__(self)
    days = matdates.DayLocator()
    days.set_view_interval(self.viewInterval)
    days.set_data_interval(self.dataInterval)
    daychanges = days()
    realdates = []
    for date in dates:
      if date not in daychanges:
        realdates.append(date)
    return realdates

class jSecondLocator(matdates.SecondLocator):
  """The purpose of this class is to ignore the change of day tick, so it doesn't overlap and look ugly"""
  def __call__(self):
    dates = matdates.SecondLocator.__call__(self)
    days = matdates.DayLocator()
    days.set_view_interval(self.viewInterval)
    days.set_data_interval(self.dataInterval)
    daychanges = days()
    realdates = []
    for date in dates:
      if date not in daychanges:
        realdates.append(date)
    return realdates

class Chart(widgets.ContentWidget):
  def __init__(self, charttable, newattribs={}):
    self.charttable = charttable
    if not newattribs.has_key('chartType'):
      newattribs['chartType'] = LINE_CHART
    if not newattribs.has_key('dpi'):
      newattribs['dpi'] = 80

    self.content_type = 'image/png'
    widgets.ContentWidget.__init__(self, "", [], newattribs)
    self.getdata()
    self.sizeimage()
    self.figure = matlab.new_figure_manager(1,(self.im_width,self.im_height),self.attribs['dpi'])

  def getdata(self):
    """Subclasses of this should implement this uniquely"""
    self.xdata = []
    self.ydata = []

  def getimage(self):
    """Subclasses of this should implement this uniquely"""
    return ''

  def sizeimage(self):  
    """Subclasses of this should implement this uniquely"""
    self.im_width = 8.75
    self.im_height = 5.6

  def getimagefromtempfile(self):
    #Save temporary file
#    tempfilename = os.path.join(tempfile.gettempdir(),'temp.png')
    retrieved = 0
    while not retrieved:
      try:
        tempfilename = str(random.randint(100000,999999)) + '.png'
        if hasattr(self.figure,'figure'):
          self.figure.figure.print_figure(tempfilename,self.attribs['dpi'])
        else: # matplotlib 0.50
          self.figure.canvas.print_figure(tempfilename,self.attribs['dpi'])

        #Read and report
        f = open(tempfilename,'rb')
        img = f.read()
        f.close()
        retrieved = 1
        os.remove(tempfilename)
      except:
        (etype, evalue, trace) = sys.exc_info()
#        print "Temp file error:",etype,evalue
#        import traceback
#        traceback.print_tb(trace)
    return img

  def gethtml(self):
#    gdchartLock.acquire()
    try:
      self.drawimage()
    except:
      raise
      print "Unexpected Error:"
      print errors.ConsoleErrorHandler().traceback_str()
#      gdchartLock.release()
      # return None
#    gdchartLock.release()
    img = self.getimagefromtempfile()
    return img

standardColours = [(0.0, 0.0, 1.0), # blue
                   (0.0, 0.5, 0.0), # green
                   (1.0, 0.0, 0.0), # red
                   (0.0, 0.75, 0.75),  # cyan
                   (0.75, 0, 0.75),  # magenta
                   (0.75, 0.75, 0),  # yellow
                   (0.0, 0.0, 0.0),  # black
                   '#4682B4',   # Steelblue
                   '#7FFF00',   # Chartreuse
                   '#FF7F50',   # Coral
                   '#808000',   # Olive
                   '#FF4500',   # Orangered
                  ]


#This class now assumes a text storage format for x values.  See below for subclass which handles dates
class LineChart(Chart):
  def __init__(self, charttable, xcolumn, ycolumns, ylabels=None, newattribs={}):
    if not newattribs.has_key('datalimits'):
      newattribs['datalimits'] = {}
    if not newattribs.has_key('numticks'):
      newattribs['numticks'] = 10
    if not newattribs.has_key('chartcolours'):
      newattribs['chartcolours'] = standardColours
    self.ylabels = ylabels
    self.normalisedValues = len(newattribs['datalimits']) > 0
    self.xcolumn = xcolumn
    self.ycolumns = ycolumns
    self.xMajorLocator = None
    self.xMajorFormatter = None
    self.xMinorLocator = None
    self.xMinorFormatter = None
    Chart.__init__(self, charttable, newattribs)

  def sizeimage(self):  
    self.im_width = self.attribs['width']/self.attribs['dpi']
    if self.attribs.has_key('height'):
      self.im_height = self.attribs['height']/self.attribs['dpi']
    else:
      self.im_height = 5.6

  def mapfromNone(self, value):
    if value == None or value == '':
      return 0
    else:
      return value

  def getdata(self):
    chartdata = self.charttable.gettablerows(self.attribs.get('filter',None))
    xlabels = [str(row[self.xcolumn]) for row in chartdata]
    self.ydata = [[self.mapfromNone(row[ycolumn]) for row in chartdata] for ycolumn in self.ycolumns]
    self.legendlabels = [str(ycolumn) for ycolumn in self.ycolumns]

    #x axis tick labels should be uniformly distributed in this case
    startVal = self.attribs.get('startval', 0)
    endVal = self.attribs.get('endval', len(self.xdata))
    self.xvalues = matlab.arange(startVal, endVal, float(endVal - startVal)/len(xlabels))
    self.xMajorLocator = ticker.LinearLocator(self.attribs.get('numticks',10))
    self.xMajorFormatter = ticker.FixedFormatter(xlabels)

  def normaliseValue(self, val, min, max, ymin, ymax):
    """Adjust value between min and max to be between ymin and ymax"""
    temp = (val - min)/(max - min)
    return temp*(ymax - ymin) + ymin

  def normaliseData(self, ymin, ymax):
    """If limits are provided for y values, normalise to between those limits"""
    newData = []
    for i, dataset in enumerate(self.ydata):
      #Don't factor limited data into ymin, ymax
      if self.legendlabels is not None and len(self.legendlabels) > i and self.attribs['datalimits'].get(self.legendlabels[i],None) is not None:
        min, max = self.attribs['datalimits'][self.legendlabels[i]]
        newSet = [self.normaliseValue(val,min,max,ymin,ymax) for val in dataset]
        newData.append(newSet)
      else:
        newData.append(dataset[:])

    self.ydata = newData        

  def getAxisMap(self, rangelimits):
    # Override this function for better management of axes
    # This version returns one set of axes
    minEU = None
    maxEU = None
    for plotname in rangelimits.keys():
      ymin, ymax = rangelimits[plotname]
      if maxEU is None or ymax > maxEU:
        maxEU = ymax
      if minEU is None or ymin > minEU:
        minEU = ymin

    axismap = [((minEU, maxEU), rangelimits.keys())]
    return axismap

  def drawimage(self):
    #Set the min/max of each axis
    plotnametodata = {}
    for i, dataset in enumerate(self.ydata):
      #Don't factor limited data into ymin, ymax
      datalimits = self.attribs['datalimits'].get(self.legendlabels[i],None)
      # Remember to check that the limits themselves have not been set to None
      if self.legendlabels is not None and len(self.legendlabels) > i and datalimits is not None and datalimits[0] is not None and datalimits[1] is not None and datalimits[0] != datalimits[1]:
        ymax, ymin = datalimits
      else:
        ymin = None
        ymax = None
        for value in dataset:
          if ymin is None or value < ymin:
            ymin = value
          if ymax is None or value > ymax:
            ymax = value
        self.attribs['datalimits'][self.legendlabels[i]] = [ymax, ymin]
      plotnametodata[self.legendlabels[i]] = dataset

    # Create the mapping the right way round
    tagtolimitmap = {}
    for plotname in self.attribs['datalimits'].keys():
      ymax, ymin = self.attribs['datalimits'][plotname]
      tagtolimitmap[plotname] = (ymin, ymax)
    #Set the size of the subplot big enough to handle times
    #[left, bottom, width, height] out of 1
    axismap = {}
    axismap = self.getAxisMap(tagtolimitmap)
    axes = []
    subplotTotal = len(axismap)
    if (subplotTotal != 0):
      plotSize = .85 / subplotTotal
    for i, (axis, tags) in enumerate(axismap):
      axes.append(self.figure.canvas.figure.add_subplot(subplotTotal,1,i+1,axisbg='w'))
      axes[-1].set_position([.08,i*plotSize+.15,.9,plotSize-.02])

    self.figure.canvas.figure.set_figsize_inches(self.im_width, self.im_height)

    #Plot each dataset
    plots = []
    for i, (axis, tags) in enumerate(axismap):
      for plotname in tags:
        if not self.attribs.get('plotdate',0):
          plots.append(axes[i].plot(self.xvalues, plotnametodata[plotname]))
        else:
          plots.append(axes[i].plot_date(self.xvalues,plotnametodata[plotname],fmt="-"))

    #Set the min/max of each axis
    for i, (axis, tags) in enumerate(axismap):
      ymin, ymax = axis
      if ymin == ymax:
        ymax += 1
        ymin -= 1
      axes[i].set_ylim([math.floor(ymin),math.ceil(ymax)])

    # We can set the colour of the lines here
    # with the variable plots
    chartColours = self.attribs.get('chartcolours',standardColours)
    plotNum = 0
    for lines in plots:
      for line in lines:
        line.set_color(chartColours[plotNum % len(chartColours)])
      plotNum += 1

    for ax in axes:
      ax.set_xlim([self.attribs.get('startval',None), self.attribs.get('endval',None)])

    if (len(axes) > 0):
      if self.xMajorLocator:
        for ax in axes:
          ax.xaxis.set_major_locator(self.xMajorLocator)
      if self.xMajorFormatter:
        axes[0].xaxis.set_major_formatter(self.xMajorFormatter)
      if self.xMinorLocator:
        for ax in axes:
          ax.xaxis.set_minor_locator(self.xMinorLocator)
      if self.xMinorFormatter:
        axes[0].xaxis.set_minor_formatter(self.xMinorFormatter)

    for ax in axes:
      ax.set_xlim([self.attribs.get('startval',None), self.attribs.get('endval',None)])

    for ax in axes[1:]:
      labels = ax.get_xticklabels()
      labels.extend([tick.label1 for tick in ax.xaxis.get_minor_ticks()])
      for label in labels:
        label.set_alpha(0)
        label.set_color('w')

    if (len(axes) > 0):
      labels = axes[0].get_xticklabels()
      labels.extend([tick.label1 for tick in axes[0].xaxis.get_minor_ticks()])
      for label in labels:
        label.set_rotation('vertical')

    #Draw a legend, but only if there are any plots to draw
    if self.legendlabels:
      for i, (axis, tags) in enumerate(axismap):
        axes[i].legend(tags,2)
        leg = axes[i].get_legend()
        leg.get_frame().set_fill(False)

    # ax.autoscale_view()
    
NUM_TIME_LABELS = 10

def pottime2date(tm):
  """Converts an object from a time object to a date object safely"""
  if not type(tm).__name__ == "time":
    return tm

  return dates.WinPyTimeToDate(tm)

class DateLineChart(LineChart):
  def __init__(self, charttable, xcolumn, ycolumns, ylabels=None, newattribs={}):
    newattribs['plotDate'] = 1
    LineChart.__init__(self, charttable, xcolumn, ycolumns, ylabels=ylabels, newattribs=newattribs)

  def getdata(self):
    filter = self.attribs.get('filter',None)
    chartdata = self.charttable.gettablerows(filter)

    startDate = self.attribs.get('startdate',None)
    endDate = self.attribs.get('enddate',None)
    if startDate == None:
      if chartdata:
        startDate = matdates.date2num(chartdata[0][self.xcolumn])
      else:
        startDate = matdates.date2num(dates.currentdate())
    else:
      startDate = matdates.date2num(startDate)
    if endDate == None:
      if chartdata:
        endDate = matdates.date2num(chartdata[-1][self.xcolumn])
      else:
        endDate = matdates.date2num(dates.currentdate() - dates.days(1))
    else:
      endDate = matdates.date2num(endDate)
    self.attribs['startval'] = startDate
    self.attribs['endval'] = endDate

    if chartdata == []:   #No data
      self.xvalues = [startDate, endDate]
      self.ydata = [[0 for xvalue in self.xvalues] for ycolumn in self.ycolumns]
    else:
      self.xvalues = [matdates.date2num(pottime2date(row[self.xcolumn])) for row in chartdata]
      self.ydata = [[self.mapfromNone(row[ycolumn]) for row in chartdata] for ycolumn in self.ycolumns]
    self.legendlabels = [str(ycolumn) for ycolumn in self.ycolumns]

    gradationUnits = self.attribs.get('gradationunits',None)
    numOfGradations = self.attribs.get('numofgradations',None)
    gradationSize = self.attribs.get('gradationsize',None)

    if gradationUnits is None or numOfGradations is None or gradationSize is None:
      self.xMajorLocator = jMajorDateLocator(time.timezone/3600)
      # self.xMajorLocator = matdates.DayLocator(100)
      self.xMajorFormatter = matdates.DateFormatter(self.attribs.get('xMajorFormat','%y-%m-%d'))
      self.xMinorLocator = jMinorLinearLocator(10)
      self.xMinorFormatter = matdates.DateFormatter(self.attribs.get('xMinorFormat','%H:%M:%S'))
    elif gradationUnits == 'days':
      self.xMajorLocator = matdates.MonthLocator()
      self.xMajorFormatter = matdates.DateFormatter('%y-%m-%d')
      self.xMinorLocator = matdates.DayLocator(interval=gradationSize)
      self.xMinorFormatter = matdates.DateFormatter('%m-%d')
    elif gradationUnits == 'hours':
      self.xMajorLocator = matdates.DayLocator()
      self.xMajorFormatter = matdates.DateFormatter('%y-%m-%d')
      self.xMinorLocator = matdates.HourLocator(byhour=range(1,24),interval=gradationSize)
      self.xMinorFormatter = matdates.DateFormatter('%H:%M')
    else:
      self.xMajorLocator = matdates.DayLocator()
      self.xMajorFormatter = matdates.DateFormatter('%y-%m-%d')
      if gradationUnits == 'minutes':
        self.xMinorLocator = jMinuteLocator(interval=gradationSize)
      else:
        self.xMinorLocator = jSecondLocator(interval=gradationSize)
      self.xMinorFormatter = matdates.DateFormatter('%H:%M:%S')

class CurrentValueLegendChart(Chart):
  """This class creates a bar chart which acts as a legend and a current value reporter"""
  def __init__(self, charttable, xcolumns, colours, newattribs={}):
    self.xcolumns = xcolumns
    newattribs['chartType'] = BAR_CHART
    Chart.__init__(self, charttable, newattribs)

    #Turn colours into an array exactly len(self.xcolumns) long
    repeatcolours = len(self.xcolumns) / len(colours)
    endcolours = len(self.xcolumns) % len(colours)
    self.colours = colours*repeatcolours + colours[:endcolours]

  def getdata(self):
    self.xdata = [str(xcolumn) for xcolumn in self.xcolumns]
    chartdata = self.charttable.gettablerows(self.attribs.get('filter',None))
    finalrow = chartdata[len(chartdata)-1]
    self.ydata = [[finalrow[xcolumn] for xcolumn in self.xcolumns]]

  def drawimage(self):
    #Find the longest text on the x axis
    maxtextlen = 0
    for text in self.xdata:
      if len(text) > maxtextlen:
        maxtextlen = len(text)

    #Convert it to a proportion of the image
    bottomProportion = .1 + maxtextlen*.013
    heightProportion = .99 - bottomProportion

    #Set the size of the subplot big enough to handle times
    #[left, bottom, width, height] out of 1
    self.figure.add_axes([.125,bottomProportion,.825,heightProportion],'w')

    #Set the min/max of each axis
    ymin = sys.maxint
    ymax = -sys.maxint+1
    for value in self.ydata[0]:
      if value < ymin:
        ymin = value
      if value > ymax:
        ymax = value
          
    self.figure.get_current_axis().set_xlim([0,len(self.xdata)+1])
    self.figure.get_current_axis().set_ylim([math.floor(ymin),math.ceil(ymax)])
    self.figure.get_current_axis().set_xticks(matlab.arange(len(self.xdata))+0.25)
    self.figure.get_current_axis().set_xticklabels(self.xdata,rotation='vertical')

    originY = None
    if ymin < 0 and ymax > 0:
      originY = 0
    self.figure.get_current_axis().bar(matlab.arange(len(self.xdata)),self.ydata[0],0.5,color=self.colours,originY=originY)

  def sizeimage(self):
    self.im_width = 3
    self.im_height = 4  #This should take tagname length into account


def test():
  """tests using some values that were giving problems"""
  import datetime
  startDate = datetime.datetime(2004, 12, 8, 14, 9, 34, 6000)
  endDate = datetime.datetime(2004, 12, 8, 15, 9, 34, 6000)
  newattribs = {"startDate": startDate, "endDate": endDate, 'width': 775, 'height': 550, 'dpi': 80}
  ylabels = ['MinEU', 'MaxEU']
  xcolumn = 'logtime'
  ycolumns = ['asd']
  class charttabletest:
    def gettablerows(self, filter):
      return [{'logtime':startDate, 'asd':20}, {'logtime':endDate, 'asd':40}]
  charttable = charttabletest()
  chart = DateLineChart(charttable, xcolumn, ycolumns, ylabels, newattribs)
  open("test.png", "wb").write(chart.gethtml())

if __name__ == "__main__":
  test()

