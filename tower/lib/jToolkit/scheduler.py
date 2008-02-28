#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""simple scheduler class that scheduler programs can use"""

# Copyright 2004 St James Software
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

import datetime
import threading
import time
from jToolkit import errors
from jToolkit import prefs
from jToolkit import tail

class Scheduler:
    WEEKDAYS = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday"]    

    def __init__(self, errorhandler=None):
        if errorhandler is None:
            self.errorhandler = errors.ConsoleErrorHandler()
        else:
            self.errorhandler = errorhandler

        self.runLock = threading.Lock()        
        
    def MainLoop(self):
        # runLock is acquired means the scheduler should keep running
        # if it is released the scheduler should stop running
        try:
            self.runLock.acquire()
            instartup = True
            while not self.runLock.acquire(False):
                try:
                    time.sleep(1)
                except KeyboardInterrupt:
                    self.errorhandler.logtrace(self.name+" manually stopped at following traceback...")
                    self.errorhandler.logtrace(self.errorhandler.traceback_str())
                    self.errorhandler.logtrace(self.name+" shutting down...")
                    self.runLock.release()
                    continue
                except Exception:
                    # this will make it restart...
                    continue
                # run any events that are scheduled for now...
                if not self.RunScheduledEvent(instartup):
                  print "RunScheduledEvent returned a False value!"
                  break
                instartup = False
            print "finished loop..."
        finally:
            print "in finally", self.runLock.locked()
            if self.runLock.locked():
                self.runLock.release()
            if hasattr(self, "mailerrorhandler"):
                self.mailerrorhandler.shutdown()

    def RunScheduledEvent(self, instartup=False):
        raise NotImplementedError("RunScheduledEvent in jToolkit/Scheduler")

    def MaintainLogfiles(self, logmaintainConfig, avgcharsperline=75):
        logfiles = logmaintainConfig.LogfilesWatched.split(',')
        lineskept = logmaintainConfig.LinesKept
        tail.reduce_files_to_tail(logfiles, lineskept, avgcharsperline)

    def GetNextScheduledTime(self, timeConfig, instartup=False):
        """gets the next time at which an event should run"""
        frequency = timeConfig.frequency.lower()

        nextSchedule = datetime.datetime.now()
        # sets a skip rate, only works up to days...
        nrate = int(getattr(timeConfig, 'nrate', 1))

        if instartup:
            onstartup = prefs.evaluateboolean(getattr(timeConfig, "onstartup", None), False)
            if onstartup:
                return nextSchedule

        snaptime = prefs.evaluateboolean(getattr(timeConfig, "snaptime", None), False)
        if frequency == 'minutely':
            if snaptime and nextSchedule.minute > 0:
                nextHour = (nextSchedule + datetime.timedelta(hours=1)).hour
                nextTime = nextSchedule + datetime.timedelta(minutes=nrate)
                if nextTime.hour == nextHour and nextTime.minute > 0:
                  nextSchedule = nextSchedule.replace(hour=nextHour, minute=0, second=0, microsecond=0)
                  return nextSchedule
            if nextSchedule.second >= 0:
                nextSchedule += datetime.timedelta(minutes=nrate)
            return nextSchedule.replace(second=0)

        ScheduleHour, ScheduleMinute = map(int, getattr(timeConfig, "time", "12:00").split(':'))
        if frequency == 'hourly':
            if nextSchedule.minute >= ScheduleMinute:
                nextSchedule += datetime.timedelta(hours=nrate)
            return nextSchedule.replace(minute=ScheduleMinute, second=0)
        elif frequency == 'daily':
            if nextSchedule.hour > ScheduleHour or \
               (nextSchedule.hour == ScheduleHour and nextSchedule.minute >= ScheduleMinute):
                nextSchedule += datetime.timedelta(days=nrate)
        elif frequency == 'weekly':
            ScheduleDay = self.WEEKDAYS.index(timeConfig.day)
            if nextSchedule.weekday() > ScheduleDay or \
               (nextSchedule.weekday() == ScheduleDay and \
                (nextSchedule.hour > ScheduleHour or \
                 (nextSchedule.hour == ScheduleHour and nextSchedule.minute >= ScheduleMinute))):
                nextSchedule += datetime.timedelta(days = 7 - (nextSchedule.weekday() - ScheduleDay))
        elif frequency == 'monthly':
            ScheduleDay = int(timeConfig.date)
            if nextSchedule.day > ScheduleDay or \
               (nextSchedule.day == ScheduleDay and \
                (nextSchedule.hour > ScheduleHour or \
                 (nextSchedule.hour == ScheduleHour and nextSchedule.minute >= ScheduleMinute))):
                if nextSchedule.month < 12:
                    nextSchedule = nextSchedule.replace(month = nextSchedule.month + 1)
                else:
                    nextSchedule = nextSchedule.replace(month = 1, year = nextSchedule.year + 1)
            nextSchedule = nextSchedule.replace(day = ScheduleDay)
        else:
            raise ValueError("Unknown frequency type %s" % frequency)

        return nextSchedule.replace(hour=ScheduleHour, minute=ScheduleMinute)

