#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""utilities for logging errors in windows services"""

from jToolkit import errors
from jToolkit import mailer
try:
  import servicemanager
except ImportError:
  class servicemanagerstub:
    pass
  servicemanager = servicemanagerstub()

class ForwardMailErrorHandler(errors.MailErrorHandler):
    """mail error handler that can also forward it over a transferAgent"""
    def __init__(self, mailoptions, errorhandler=None, transferAgent=None):
        errors.MailErrorHandler.__init__(self, mailoptions, errorhandler)
        self.transferAgent = transferAgent

    def dosend(self, message, subject):
        """send off any messages waiting in the queue (via chosen transport)"""
        if hasattr(self.mailoptions, 'useImportServer') and str(self.mailoptions.useImportServer) == 'True':
            self.doserversend(message, subject)
        else:
            errors.MailErrorHandler.dosend(self, message, subject)

    def doserversend(self, message, subject):
        """send off any messages waiting in the queue to the server, to be emailed off from there"""
        if self.transferAgent == None:
            return
        # If we have an error handler, likelihood is it's an email error handler
        # If sending an email up to the server fails, we don't want the failure to generate another
        # call to this function.
        if not self.transferAgent.sendEmail(message, subject, self.errorhandler == None):
            if self.errorhandler:
                self.errorhandler.logerror("Failed sending error message to server")

class ServiceErrorHandler(errors.ErrorHandler):
    def __init__(self):
        """constructs the service error handler"""
        pass

    def logerror(self, message):
        """logs an error"""
        servicemanager.LogErrorMsg(message)

    def logtrace(self, message):
        """logs an info message"""
        servicemanager.LogInfoMsg(message)

