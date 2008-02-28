#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""does error handling in a way that works for a web server"""

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

import sys
import traceback
import time
try:
  import threading
except ImportError:
  import dummy_threading as threading
try:
  from jToolkit import mailer
except ImportError:
  mailer = None

class ErrorHandler:
  """a class that handles error logging etc"""
  def __init__(self, instance):
    self.instance = instance

  def traceback_str(self):
    exc_info = sys.exc_info()
    return "".join(traceback.format_exception(exc_info[0], exc_info[1], exc_info[2]))

  def exception_str(self):
    exc_info = sys.exc_info()
    return "".join(traceback.format_exception_only(exc_info[0], exc_info[1]))

  def writelog(self, filename, message):
    # Append a log to a field
    f = open(filename,'a')
    #f.write(time.asctime()+': ')
    f.write(time.strftime('%Y-%m-%d %H:%M:%S')+': ')
    if isinstance(message, unicode):
      f.write(message.encode('utf8'))
    else:
      f.write(message)
    f.write('\n')
    f.close()

  def logerror(self, msg):
    if getattr(self.instance, "errorfile", None):
      self.writelog(self.instance.errorfile, msg)

  def logtrace(self, msg):
    if getattr(self.instance, "tracefile", None):
      self.writelog(self.instance.tracefile, msg)

  def logtracewithtime(self, msg):
    t = time.time()
    ms = int((t - int(t))*1000.0)
    self.logtrace(".%03d: %s" % (ms, msg))

  def getauditstr(self, recorddict=None):
    def tounicode(value):
      if isinstance(value, str): return value.decode('utf8')
      else:
        try:
          return unicode(value)
        except ValueError:
          return unicode(repr(value))
    if recorddict is not None:
      return ', '.join([key + ':' + tounicode(value) for key, value in recorddict.iteritems()])
    return ''

  def logaudit(self, msg, recorddict=None):
    if not getattr(self.instance, "auditfile", None):
      return
    msg += self.getauditstr(recorddict)
    self.writelog(self.instance.auditfile,msg)

class NullErrorHandler(ErrorHandler):
  """a class that handles error logging etc, but does absolutely nothing"""
  def __init__(self):
    pass

  def logerror(self, msg):
    pass

  def logtrace(self, msg):
    pass

  def logaudit(self, msg, recorddict=None):
    pass

class ConsoleErrorHandler(ErrorHandler):
  def __init__(self, errorfile=sys.stderr, tracefile=sys.stdout):
    self.errorfile = errorfile
    self.tracefile = tracefile

  def writelog(self, f, message):
    f.write(time.strftime('%Y-%m-%d %H:%M:%S')+': ')
    if isinstance(message, unicode):
      f.write(message.encode('utf8'))
    else:
      f.write(message)
    f.write('\n')
    f.flush()

  def logerror(self, message):
    self.writelog(self.errorfile, message)

  def logtrace(self, message):
    if self.tracefile is not None:
      self.writelog(self.tracefile, message)

  def logaudit(self, msg, recorddict=None):
    self.logtrace(msg + self.getauditstr(recorddict))

  def logtracewithtime(self, msg):
    t = time.time()
    ms = int((t - int(t))*1000.0)
    self.logtrace(".%03d: %s" % (ms, msg))

class TeeErrorHandler(ErrorHandler):
    """An error handler that tees the errors to multiple secondary handlers"""
    def __init__(self, *errorhandlers):
        """constructs the error handler"""
        self.errorhandlers = errorhandlers

    def logerror(self, message):
        """logs an error"""
        for errorhandler in self.errorhandlers:
            errorhandler.logerror(message)

    def logtrace(self, message):
        """logs a trace"""
        for errorhandler in self.errorhandlers:
            errorhandler.logtrace(message)

    def logaudit(self, message, recorddict=None):
        """logs an audit"""
        for errorhandler in self.errorhandlers:
            errorhandler.logaudit(message, recorddict)

class MailErrorHandler(ErrorHandler):
    def __init__(self, mailoptions, errorhandler=None):
        """constructs the emailing error handler"""
        if mailer is None:
          raise ImportError("Error importing jToolkit.mailer, so mailer not available")
        self.mailoptions = mailoptions
        self.waitingmail = []
        self.oldestmember = None
        self.sleepperiod = getattr(self.mailoptions, "sleepperiod", 10)
        self.gatherperiod = getattr(self.mailoptions, "gatherperiod", 60)
        self.logmailerrors = getattr(self.mailoptions, "logmailerrors", 1)
        self.logmailinfo = getattr(self.mailoptions, "logmailinfo", 0)
        self.errorhandler = errorhandler
        self.sendloopwaiting = 0
        self.shuttingdown = threading.Event()
        self.waitingLock = threading.Lock()

    def logerror(self, message):
        """logs an error"""
        if getattr(self.mailoptions, "senderrors", 1):
            self.mailmessage(message, "Error")

    def logtrace(self, message):
        """logs a trace"""
        if getattr(self.mailoptions, "sendtraces", 0):
            self.mailmessage(message, "Trace")

    def mailmessage(self, message, subject):
        """emails a message"""
        self.addmessage("%s\n%s\n\n%s" % (subject, "-"*len(subject), message))

    def shutdown(self):
        """shut down now ... no more waiting"""
        self.waitingLock.acquire()
        self.shuttingdown.set()
        self.waitingLock.release()

    def addmessage(self, message):
        """add the message to the queue"""
        self.waitingLock.acquire()
        if self.oldestmember is None:
            self.oldestmember = time.time()
        self.waitingmail.append(message)
        if not self.sendloopwaiting:
            self.sendloopwaiting = 1
            sendloopthread = threading.Thread(target=self.sendloop)
            sendloopthread.start()
        self.waitingLock.release()

    def sendloop(self):
        """wait around until we have gathered some other messages, then send them all together"""
        while 1:
            self.shuttingdown.wait(self.sleepperiod)
            self.waitingLock.acquire()
            expired = (self.oldestmember is not None and time.time() - self.oldestmember >= self.gatherperiod)
            if expired or self.shuttingdown.isSet():
                message = "\n\n".join(self.waitingmail)
                messagecount = len(self.waitingmail)
                self.waitingmail = []
                self.oldestmember = None
                self.sendloopwaiting = 0
            else:
                messagecount =  0
            self.waitingLock.release()
            if messagecount:
                self.dosend(message, "(%d messages)" % messagecount)
                return

    def dosend(self, message, subject):
        """send off any messages waiting in the queue (via chosen transport)"""
        mailengine = getattr(self.mailoptions, 'mailengine', '').lower()
        if not mailengine:
            if hasattr(self.mailoptions, 'smtpserver'):
                mailengine = 'smtp'
            elif hasattr(self.mailoptions, 'mapiprofile'):
                mailengine = 'mapi'
        if mailengine == 'smtp':
            self.dosmtpsend(message, subject)
        elif mailengine == 'simplemapi':
            self.dosimplemapisend(message, subject)
        elif mailengine == 'mapi':
            self.domapisend(message, subject)
        else:
            self.errorhandler.logerror("mailengine not specified or invalid mailengine: %r" % mailengine)

    def dosmtpsend(self, message, subject):
        """send off any messages waiting in the queue (via SMTP)"""
        toaddresses = self.mailoptions.toaddresses
        smtpserver = self.mailoptions.smtpserver
        subject = self.mailoptions.subject + " " + subject
        fromlabel = self.mailoptions.fromlabel
        fromaddress = self.mailoptions.fromaddress
        sendfrom = (fromlabel, fromaddress)
        if self.errorhandler is not None and self.logmailinfo:
            self.errorhandler.logtrace("sending message from %s to %r, length %d" % (fromaddress, toaddresses, len(message)))
        try:
            if self.errorhandler is not None and self.logmailerrors:
              mailererrorhandler = self.errorhandler
            else:
              mailererrorhandler = None
            mailer.SendSMTPMail(subject, message, SendTo=toaddresses, SendFrom=sendfrom, 
                                SMTPServer=smtpserver, errorhandler=mailererrorhandler)
        except:
            if self.errorhandler is not None and self.logmailerrors:
                self.errorhandler.logerror("error sending message over SMTP: %r" % ((fromaddress, toaddresses, message, self.mailoptions.smtpserver),))
                self.errorhandler.logerror(self.errorhandler.traceback_str())

    def dosimplemapisend(self, message, subject):
        """send off any messages waiting in the queue (via MAPI)"""
        toaddresses = self.mailoptions.toaddresses
        profile = getattr(self.mailoptions, "mapiprofile", None)
        subject = self.mailoptions.subject + " " + subject
        if self.errorhandler is not None and self.logmailinfo:
            self.errorhandler.logtrace("sending message with profile %r to %r, length %d" % (profile, toaddresses, len(message)))
        try:
            # TODO: alter mapi in mailer to be able to log its own error messages...
            mailer.SendMAPIMail(Subject=subject, Message=message, SendTo=toaddresses, MAPIProfile=profile)
        except:
            if self.errorhandler is not None and self.logmailerrors:
                self.errorhandler.logerror("error sending message over simple MAPI: %r" % ((profile, toaddresses, message),))
                self.errorhandler.logerror(self.errorhandler.traceback_str())

    def domapisend(self, message, subject):
        """send off any messages waiting in the queue (via MAPI)"""
        toaddresses = self.mailoptions.toaddresses
        profile = getattr(self.mailoptions, "mapiprofile", None)
        subject = self.mailoptions.subject + " " + subject
        if self.errorhandler is not None and self.logmailinfo:
            self.errorhandler.logtrace("sending message with profile %r to %r, length %d" % (profile, toaddresses, len(message)))
        try:
            # TODO: alter mapi in mailer to be able to log its own error messages...a
            mailer.SendEMAPIMail(Subject=subject, Message=message, SendTo=toaddresses, MAPIProfile=profile)
        except:
            if self.errorhandler is not None and self.logmailerrors:
                self.errorhandler.logerror("error sending message over MAPI: %r" % ((profile, toaddresses, message),))
                self.errorhandler.logerror(self.errorhandler.traceback_str())

