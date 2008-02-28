#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Receives requests from the clients via Apache and responds with html strings
   Typically, the response will include html that represents a toolbar, a form and a grid
   May also (later) include pop up windows and error messages.
"""      

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

from jToolkit.data import database
from jToolkit.web import httpcodes
from jToolkit.web import session
from jToolkit.web import record
from jToolkit import errors
from jToolkit import localize
from jToolkit import attachments
from jToolkit import prefs
from jToolkit.widgets import widgets
from jToolkit.widgets import table
import types
import sys

rptcrash = None

# TODO: add detection of time zone to login page...
class LoginPage(widgets.Page):
  """this is a page asking the user to login"""
  def __init__(self, session, extraargs={}, confirmlogin=0, specialmessage=None, languagenames=None):
    title = self.gettitle(session)
    widgets.Page.__init__(self, title, contents=[])
    self.confirmlogin = confirmlogin
    self.handleextraargs(extraargs)
    self.specialmessage = specialmessage
    self.languagenames = languagenames
    self.makepage(session)

  def getinstancename(self, instance):
    """returns the instance name"""
    return getattr(instance, "title", getattr(instance, "__name__", str(instance)))

  def gettitle(self, session):
    """returns the title for the login page"""
    return session.localize("Login for %s") % self.getinstancename(session.instance)

  def handleextraargs(self, extraargs):
    """process the arguments given, and add neccessary args to a hidden widgets list"""
    self.action = ''
    self.hiddenwidgets = []
    for key, value in extraargs.iteritems():
      key = key.lower()
      # if there are multiple arguments stored in a list, just use the first one...
      if isinstance(value, list):
        value = value[0]
      if key == 'islogout':
        # if logging out, get rid of any parameters in the URL
        self.action = '?'
      if key == 'confirmlogin':
        self.confirmlogin = value
      if key not in ['username','password','login','islogin','islogout']:
        hiddenwidget = widgets.Input({'type':'hidden','name':key,'value':value})
        self.hiddenwidgets.append(hiddenwidget)
    if self.confirmlogin:
      logintype = widgets.Input({'type':'hidden','name':'confirmlogin','value':'true'})
    else:
      logintype = widgets.Input({'type':'hidden','name':'islogin','value':'true'})
    self.hiddenwidgets.append(logintype)

  def makepage(self, session):
    """builds up the page out of the component parts"""
    loginform = self.getloginform(session)
    loginform.addcontents(self.hiddenwidgets)
    self.addcontents(loginform)
    loginstatus = widgets.Paragraph(self.getstatustext(session))
    self.addcontents(loginstatus)
    if self.confirmlogin:
      newsessionlink = widgets.Link('index.htm?islogout=true', \
        session.localize('Cancel this action and start a new session'), \
        {'target':'_top', 'title':session.localize('Instead of confirming this action, log out and start from scratch')})
      newsessiontext = widgets.Paragraph([newsessionlink])
      self.addcontents(newsessiontext)
    if hasattr(session.server, 'parent'):
      exitapplink = widgets.Link('../index.htm', \
        session.localize('Exit application'), \
        {'target':'_top', 'title':session.localize('Exit this application and return to the parent application')})
      self.addcontents(widgets.Paragraph(exitapplink))

  def getstatustext(self, session):
    """returns the current session status"""
    statustext = session.getstatus()
    if self.confirmlogin:
      statustext += session.localize(", please confirm login")
    return statustext

  def getloginform(self, session):
    """returns the actual Form"""
    submitbutton = widgets.Input({'type':'submit', 'name':'Login', 'value':session.localize('Login')})
    formwidgets = [self.getlogintable(session), submitbutton]
    # by default, otherwise go back to the given place...
    loginform = widgets.Form(newattribs={'name':'loginform','action':self.action}, contents=formwidgets)
    return loginform

  def getlogintable(self, session):
    username = ''
    if hasattr(session,'username'):
      username = session.username
    usernameinput = widgets.Input({'name':'username','value':username}, readonly=self.confirmlogin)
    passwordinput = widgets.Input({'type':'password','name':'password'})
    logintable = table.TableLayout()
    logintable.setcell(1,1,table.TableCell(session.localize('Username:')))
    logintable.setcell(1,2,table.TableCell(usernameinput))
    logintable.setcell(2,1,table.TableCell(session.localize('Password:')))
    logintable.setcell(2,2,table.TableCell(passwordinput))
    languageselect = self.getlanguageselect(session)
    if languageselect:
      logintable.setcell(3,1,table.TableCell(session.localize('Language:')))
      logintable.setcell(3,2,table.TableCell(languageselect))
    return logintable

  def getlanguageselect(self, session):
    """returns language selector widget"""
    if self.languagenames and not self.confirmlogin:
      # TODO: work out how we handle localization of language names...
      languageoptions = self.languagenames.items()
      languageselect = widgets.Select({'name':'language','value':session.language}, options=languageoptions)
    else:
      return None

class Redirect:
  """an object that instructs the server to redirect the client to another page..."""
  def __init__(self, location, ispermanent=False, withpage=False, withtemplate=False):
    """location is the new URL. ispermanent is the type of redirect
    withpage is a widgets Page to use for the redirect, if desired
    withtemplate is a tuple of (templatename, templatevars) to be used with TemplateServer)"""
    self.location = location
    self.ispermanent = ispermanent
    self.withpage = withpage
    self.withtemplate = withtemplate

  def sendredirect(self, req):
    """sends the redirect instruction or page back to the request"""
    if self.withpage:
      req.content_type = "text/html; charset=UTF-8"
      self.withpage.attribs['refresh'] = 0
      self.withpage.attribs['refreshurl'] = self.location
      response = self.withpage.gethtml()
      if isinstance(response, unicode):
        # TODO: get encoding from http request...
        response = response.encode('utf8')
      # return the html response (whether customized or standard)
      req.send_http_header()
      req.write(response)
      return httpcodes.OK
    else:
      req.headers_out.add('Location', self.location)
      if self.ispermanent:
        return httpcodes.MOVED_PERMANENTLY
      else:
        return httpcodes.MOVED_TEMPORARILY

class ResponseCleanup:
  """an object that performs cleanup after the response has been sent..."""
  def __init__(self, response, cleanup, data=None):
    self.response = response
    self.cleanup = cleanup
    self.data = data

class AppServer(object):
  """base class for AppServers... handles requests. need to define getpage in subclass"""
  def __init__(self, instance, webserver=None, sessioncache=None, errorhandler=None):
    """constructs a Server for a given instance, using the given session cache and error handler"""
    self.rptcrash = rptcrash
    self.instance = instance
    if getattr(self.instance, "logrecord", None):
      self.logrecord = record.HTTPRecorder(self.instance)
      self.allowcaching = False
      self.allowetag = False
    else:
      self.logrecord = None
    if sessioncache is None:
      self.sessioncache = session.SessionCache()
    else:
      self.sessioncache = sessioncache
    self.setwebserver(webserver, errorhandler)
    self.inittranslation()

  def setwebserver(self, webserver, errorhandler=None):
    """sets the webserver (and errorhandler if given) to the given values"""
    self.webserver = webserver
    if errorhandler is None:
      if self.webserver is None:
        self.errorhandler = errors.ErrorHandler(self.instance)
      else:
        self.errorhandler = self.webserver.createerrorhandler(self.instance)
    else:
      self.errorhandler = errorhandler

  def createlock(self):
    """creates a lock using the webserver"""
    if getattr(self, "webserver", None) is None:
      raise AttributeError("Server needs webserver to create lock")
    return self.webserver.createlock()
    
  def inittranslation(self, localedir=None, localedomains=None, defaultlanguage=None):
    """initialize self.translation from the localedir, localedomains and defaultlanguage
    if any parameter is not given it is searched first on self.instance, then on self"""
    def getlangattr(langattr, value, default):
      """retrieves the right value of the attribute if not supplied"""
      if value is None:
        return getattr(self.instance, langattr, getattr(self, langattr, default))
      return value
    # set the right values for localedir and localedomains
    self.localedir = getlangattr('localedir', localedir, None)
    self.localedomains = getlangattr('localedomains', localedomains, [])
    if self.localedomains:
      if isinstance(self.localedomains, basestring):
        self.localedomains = self.localedomains.split(',')
    # set languagelist and languagenames
    if self.localedir is not None:
      self.languagelist = localize.getinstalledlanguages(self.localedir)
      self.languagenames = localize.getlanguagenames(self.languagelist)
    else:
      self.languagelist = []
      self.languagenames = {}
    # construct the actual translation object
    self.translation = localize.translation(self.localedomains, self.localedir, self.languagelist)
    self.defaultlanguage = getlangattr('defaultlanguage', defaultlanguage, None)
    if self.defaultlanguage is None:
      self.defaultlanguage = localize.getdefaultlanguage(self.languagelist)

  def getclassattr(self, attrname, default=None, instance=None):
    """return an attribute on the instance, resolving it if neccessary, and using default if not present
    in addition, if the attribute refers a function, it will be called with any child items as named parameters"""
    if instance is None:
      instance = self.instance
    if default is not None:
      classnode = getattr(instance, attrname, default)
    else:
      classnode = getattr(instance, attrname)
    specifiedclass = classnode
    if hasattr(specifiedclass, "resolve"):
      specifiedclass = specifiedclass.resolve()
    if hasattr(specifiedclass, "template"):
      template = self.getclassattr("template", instance=specifiedclass)
      templateargs = {}
      for key, value in getattr(specifiedclass, "templateargs", {}).iteritems():
        if hasattr(value, "resolve"):
          value = value.resolve()
        templateargs[key] = value
      specifiedclass = template(**templateargs)
    return specifiedclass

  def getinstancename(self, instance):
    """returns the instance name"""
    return getattr(instance, "title", getattr(instance, "__name__", str(instance)))

  def getremoteip(self, req):
    """gets the remote IP address of the client"""
    if hasattr(req.connection, 'remote_ip'):
      return req.connection.remote_ip
    else:
      return req.client_address[0]

  def getlocaladdr(self, req):
    if hasattr(req.connection, 'remote_ip'):
      localaddr = req.connection.local_addr
    else:
      localaddr = req.server.server_address
    if localaddr[0] == '':
      localaddr = ('127.0.0.1',localaddr[1])
    return localaddr

  def handle(self, req, pathwords, argdict):
    """handles the request and returns a page object in response"""
    argdict = self.processargs(argdict)
    session = self.getsession(req, argdict)
    session.pagecount += 1
    session.remote_ip = self.getremoteip(req)
    session.localaddr = self.getlocaladdr(req)
    return self.getpage(pathwords, session, argdict)

  def getsession(self, req, argdict):
    """gets the session for the request"""
    session = self.sessioncache.getsession(req, argdict, self)
    # let the request know the session (for logging purposes)
    req.session = session
    return session

  def sendpage(self, req, thepage):
    """returns the page to the user"""
    if isinstance(thepage, ResponseCleanup):
      req.register_cleanup(thepage.cleanup, thepage.data)
      thepage = thepage.response
    # disallow caching unless the user explicitly overrides this (per-server or per-page)
    if not (getattr(self, 'allowcaching', False) or getattr(thepage, 'allowcaching', False) or getattr(req, 'allowcaching', False)):
      req.headers_out.add('Cache-Control', 'no-cache')
      req.headers_out.add('Pragma', 'no-cache')
    if getattr(thepage, 'etag', None) and getattr(self, 'allowetag', True) and getattr(req, 'allowetag', True):
      req.headers_out.add('Etag', thepage.etag)
      # TODO: remove this when support for mod_python 2.x is no longer required
      # it could use req.headers_in.get in mod_python 3.x
      if req.headers_in.has_key('If-None-Match'):
        reqetag = req.headers_in['If-None-Match']
        if reqetag == thepage.etag:
          return httpcodes.NOT_MODIFIED
    if isinstance(thepage, (str, unicode)):
      contents = widgets.PlainContents(thepage)
      return self.sendpage(req, contents)
    elif isinstance(thepage, widgets.Widget):
      # get the content type...
      if hasattr(thepage,'content_type'):
        req.content_type = thepage.content_type
      else:
        req.content_type = "text/html; charset=UTF-8"
      if hasattr(thepage, 'sendfile_path'):
        req.send_http_header()
        req.sendfile(thepage.sendfile_path)
        return httpcodes.OK
      response = thepage.gethtml()
      if self.logrecord:
        self.logrecord.logresponse(req, response)
      elif getattr(req, "logresponse", None):
        # this lets another server set logresponse
        req.logresponse(req, response)
      # return the html response (whether customized or standard)
      if isinstance(response, unicode):
        # TODO: get encoding from http request...
        response = response.encode('utf8')
      try:
        req.send_http_header()
        req.write(response)
      except getattr(self.webserver, "errorclass", Exception), e:
        self.errorhandler.logerror("Error writing response: %s" % e)
      return httpcodes.OK
    elif isinstance(thepage, Redirect):
      return thepage.sendredirect(req)
    elif thepage is None:
      # return None to indicate we didn't produce a page (usually means Apache/webserver will handle it)
      return None
    elif isinstance(thepage, int):
      # an integer means a return code... not a page
      return thepage
    else:
      raise ValueError("Unexpected page type: %s" % type(thepage))

  def processargs(self, argdict):
    """return a dictionary of the set of arguments in a request..."""
    newdict = {}
    if "allowmultikey" in argdict:
      allowmultikeys = self.processarg("allowmultikey", argdict["allowmultikey"], True)
      if isinstance(allowmultikeys, (str, unicode)):
        allowmultikeys = [allowmultikeys]
      # put all the keys into a list, make sure they are unique
      allowmultikeysdict = {}
      for key in allowmultikeys:
        lowerkey = key
        if isinstance(lowerkey, str):
          lowerkey = lowerkey.decode("utf-8")
        lowerkey = lowerkey.lower()
        allowmultikeysdict[lowerkey] = None
      allowmultikeys = allowmultikeysdict.keys()
    else:
      allowmultikeys = []
    for key in argdict.keys():
      if key == "allowmultikey":
        newdict["allowmultikey"] = allowmultikeys
      elif key is not None:
        lowerkey = key
        if isinstance(lowerkey, str):
          lowerkey = lowerkey.decode("utf-8")
        lowerkey = lowerkey.lower()
        allowmultikey = (lowerkey in allowmultikeys)
        newdict[key] = self.processarg(key, argdict[key], allowmultikey)
    return newdict

  def processarg(self, key, value, allowmultikey=False):
    """process the given key and value and return the processed value"""
    if type(value) == types.InstanceType:
      if hasattr(value, 'filename') and value.filename != None:
        # this is for an attachment upload...
        try:
          return attachments.Attachment(self.instance, field=value)
        except attachments.AttachmentError, attachmenterror:
          return attachmenterror
    if isinstance(value, list):
      # this only happens with multiple arguments, which we don't want
      # TODO: check whether we really need to do this or could just prevent multiple argument submissions...
      if allowmultikey:
        return [self.processarg(key, subvalue) for subvalue in value]
      else:
        value = value[0]
    if hasattr(value, 'value'):
      # this is for a StringField from mod_python 3...
      value = value.value
    if isinstance(value, str):
      try:
        return value.decode('utf8')
      except UnicodeDecodeError:
        self.errorhandler.logerror("Error decoding string in utf-8: %s" % self.errorhandler.exception_str())
        self.errorhandler.logerror("We will ignore the characters we cannot decode")
        return value.decode('utf8','ignore')
    return value

  def gettranslation(self, language):
    """returns a translation object for the given language (or default if language is None)"""
    if language is None:
      return self.translation
    else:
      languagelist = [language] + self.languagelist
      return localize.translation(self.localedomains, self.localedir, languagelist)

  def localize(self, message, *variables):
    """returns the localized form of a message, falls back to original if failure with variables"""
    # this is used when no session is available
    if variables:
      # TODO: this is a hack to handle the old-style passing of a list of variables
      # remove below after the next jToolkit release
      if len(variables) == 1 and isinstance(variables[0], (tuple, list)):
        variables = variables[0]
      # remove above after the next jToolkit release
      try:
        return self.translation.ugettext(message) % variables
      except:
        return message % variables
    else:
      return self.translation.ugettext(message)

  def nlocalize(self, singular, plural, n, *variables):
    """returns the localized form of a plural message, falls back to original if failure with variables"""
    # this is used when no session is available
    # TODO: change variables to a *arglist?
    if variables:
      # TODO: this is a hack to handle the old-style passing of a list of variables
      # remove below after the next jToolkit release
      if len(variables) == 1 and isinstance(variables[0], (tuple, list)):
        variables = variables[0]
      # remove above after the next jToolkit release
      try:
        return self.translation.ungettext(singular, plural, n) % variables
      except:
        if n != 1:
          return plural % variables
        else:
          return singular % variables
    else:
      return self.translation.ungettext(singular, plural, n)

  def initsession(self, session):
    """takes a new session and adds attributes we need"""
    pass

class LoginAppServer(AppServer):
  """AppServer that includes a login facility"""
  def __init__(self, instance, webserver=None, sessioncache=None, errorhandler=None, loginpageclass=LoginPage):
    """constructs a Server for a given instance, using the given session cache and error handler"""
    if sessioncache is None:
      sessioncache = session.SessionCache(sessionclass=session.LoginSession)
    super(LoginAppServer, self).__init__(instance, webserver, sessioncache, errorhandler)
    self.loginpageclass = loginpageclass

  def handle(self, req, pathwords, argdict):
    """handles the request and returns a page object in response"""
    argdict = self.processargs(argdict)
    session = self.getsession(req, argdict)
    if session.isopen:
      session.pagecount += 1
      session.remote_ip = self.getremoteip(req)
      session.localaddr = self.getlocaladdr(req)
      return self.getpage(pathwords, session, argdict)
    else:
      if self.isloginpage(pathwords):
        return self.getloginpage(session, argdict, languagenames=self.languagenames)

  def getloginpage(self, session, argdict, languagenames=None, **kwargs):
    if languagenames is None:
      languagenames = self.languagenames
    template = getattr(session.instance,'logintemplate',None)
    if template:
        import kid
        title = getattr(session.instance,'title',getattr(session.instance,"__name__",str(session.instance)))
        context = {'languagenames':languagenames,
                   'extraargs':argdict,
                   'title':title,
                   'session':session}
        try:
            import tidy
            tidyoptions = dict(output_xhtml=1,add_xml_decl=1,indent=1,tidy_mark=0)
            source = str(tidy.parse(template,**tidyoptions))
        except:
            source = open(template, "r").read()
        serializer = kid.Template(source=source,**context)
        html = serializer.serialize(output="xhtml")
        return widgets.PlainContents(html)
    return self.loginpageclass(session, argdict, languagenames=languagenames, **kwargs)

  def isloginpage(self, pathwords):
    """returns whether this page should be returned as a login page if not logged in"""
    if len(pathwords):
      urlpart = pathwords[-1]
      if "." in urlpart:
        if urlpart[urlpart.rfind(".")+1:].lower() not in ("htm", "html"):
          return False
    return True

  def getsession(self, req, argdict):
    """checks login. if valid, return the requested page, otherwise return the login page"""
    islogin = argdict.get("islogin",0)
    confirmlogin = argdict.get("confirmlogin",0)
    islogout = argdict.get("islogout",0)
    # handle login, logout, normal authorization
    if islogin:
      session = self.sessioncache.newsession(req,argdict,self)
    elif confirmlogin:
      session = self.sessioncache.confirmsession(req,argdict,self)
    elif islogout:
      session = self.sessioncache.closesession(req,argdict,self)
    else:
      session = self.sessioncache.getsession(req,argdict,self)
    # let the request know the session (for logging purposes)
    req.session = session
    return session

class DBAppServer(AppServer):
  """basic App Server that also handles connection to the database..."""
  def __init__(self, instance, webserver=None, sessioncache=None, errorhandler=None, cachetables=None):
    """constructs a Server for a given instance, using the given session cache and error handler"""
    super(DBAppServer, self).__init__(instance, webserver, sessioncache, errorhandler)
    self.instance = instance
    switchfrozen, tempfrozen = False, None
    self.initdb(cachetables)

  def initdb(self, cachetables=None):
    """initialises the database connection"""
    if not hasattr(self, 'db'):
      for attr in dir(self.instance):
        if attr.startswith("DB"):
          value = getattr(self.instance, attr)
          if isinstance(value, prefs.UnresolvedPref):
            setattr(self.instance, attr, value.resolve())
      self.db = database.dbwrapper(self.instance, self.errorhandler, cachetables)

class DBLoginAppServer(DBAppServer, LoginAppServer):
  """AppServer that includes a login facility"""
  def __init__(self, instance, webserver=None, sessioncache=None, errorhandler=None, loginpageclass=LoginPage, cachetables=None):
    """constructs a Server for a given instance, using the given session cache and error handler"""
    if sessioncache is None:
      sessioncache = session.SessionCache(sessionclass=session.DBLoginSession)
    super(DBLoginAppServer, self).__init__(instance, webserver, sessioncache, errorhandler, cachetables)

# TODO: work out how to separate out DB stuff so we don't have to have a separate class structure
class MultiAppServer(DBLoginAppServer):
  """serves multiple instances in subdirectories..."""
  def __init__(self, instance, webserver=None, sessioncache=None, errorhandler=None, loginpageclass=LoginPage, cachetables=None):
    """constructs the multi-app server"""
    if sessioncache is None:
      # we don't need a sessioncache as we don't do login...
      sessioncache = {}
    super(MultiAppServer, self).__init__(instance, webserver, sessioncache, errorhandler, loginpageclass, cachetables)
    if isinstance(self.instance.instances, dict):
      self.instances = self.instance.instances
    else:
      self.instances = dict(self.instance.instances.iteritems())
    self.servers = {}

  def getserver(self, pathwords):
    """gets a server given the path"""
    top = pathwords[0]
    # get the instance and server...
    if top not in self.servers:
      if top not in self.instances:
        return None
      instance = self.instances[top]
      serverclass = self.getclassattr("serverclass", instance=instance)
      # TODO: Implement a better way of giving locks to child servers (locks should depend on directory, not MultiServer)
      server = serverclass(instance, self.webserver)
      server.name = top
      server.webserver = self.webserver
      server.parent = self
      self.servers[top] = server
    return self.servers[top]

  def shoulddefer(self, pathwords):
    """decides whether this request is for us or someone else"""
    if len(pathwords) > 0:
      top = pathwords[0]
      if top not in ('', 'index.htm', 'index.html'):
        return 1
    return 0

  def handledefer(self, req, pathwords, argdict):
    """handles deferring the request to another server"""
    server = self.getserver(pathwords)
    if server is None:
      return None
    if server.logrecord:
      server.logrecord.logrequest(req)
    return server.handle(req, pathwords[1:], argdict)

  def handle(self, req, pathwords, argdict):
    """handles the request and returns a page object in response"""
    if self.shoulddefer(pathwords):
      if pathwords[0] in self.instances:
        return self.handledefer(req, pathwords, argdict)
      else:
        return None
    else:
      argdict = self.processargs(argdict)
      return self.getpage(pathwords, None, argdict)

  def getpage(self, pathwords, session, argdict):
    """returns the page to be sent to the user"""
    if len(pathwords) > 0:
      top = pathwords[0]
    else:
      top = ''
    if top in ('', 'index.htm', 'index.html'):
      return self.getindexpage(session)
    else:
      return None

  def getindexpage(self, session):
    """returns a page for the index..."""
    links = [widgets.Paragraph(widgets.Link(instance+"/", instance)) for instance in self.instances]
    return widgets.Page(session.localize("Select Application"), links)

class SharedLoginAppServer(DBLoginAppServer):
  """allows instance to be passed a shared session..."""
  def handle(self, req, pathwords, argdict, sharedsession=None):
    """handles the request and returns a page object in response"""
    argdict = self.processargs(argdict)
    exitapp = argdict.get('exitapp', 0)
    session = self.getsession(req, argdict, sharedsession)
    if exitapp:
      if 'Set-Cookie' in req.headers_out:
        redirectpage = widgets.Page("Redirecting to index...")
        return Redirect("../index.html", withpage=redirectpage)
      return Redirect("../index.html")
    if session.isopen:
      session.pagecount += 1
      session.remote_ip = self.getremoteip(req)
      session.localaddr = self.getlocaladdr(req)
      return self.getpage(pathwords, session, argdict)
    else:
      if self.isloginpage(pathwords):
        return self.getloginpage(session, argdict, languagenames=self.languagenames)

  def getsession(self, req, argdict, sharedsession):
    """checks login. if valid, return the requested page, otherwise return the login page"""
    islogin = argdict.get("islogin",0)
    confirmlogin = argdict.get("confirmlogin",0)
    islogout = argdict.get("islogout",0)
    manualmode = islogin or confirmlogin or islogout
    session = super(SharedLoginAppServer, self).getsession(req, argdict)
    if not (manualmode or session.isopen) and sharedsession is not None and sharedsession.isopen:
      sharedsession.sharelogindetails(req, session)
      argdict["islogin"] = 1
    # let the request know the session (for logging purposes)
    req.session = session
    return session

class SharedLoginMultiAppServer(MultiAppServer):
  """allows multiple instance to share login credentials..."""
  def __init__(self, instance, webserver, sessioncache=None, errorhandler=None, loginpageclass=LoginPage, cachetables=None):
    """constructs the multi-app server"""
    if sessioncache is None:
      sessioncache = session.SessionCache(sessionclass=session.LoginSession,sessioncookiename=self.getinstancename(instance)+'session')
    super(SharedLoginMultiAppServer, self).__init__(instance, webserver, sessioncache, errorhandler, loginpageclass, cachetables)
    if isinstance(self.instance.instances, dict):
      self.instances = self.instance.instances
    else:
      self.instances = dict(self.instance.instances.iteritems())
    self.servers = {}

  def handledefer(self, req, pathwords, argdict, session=None):
    """handles deferring the request to another server"""
    server = self.getserver(pathwords)
    if server is None:
      return None
    if server.logrecord:
      server.logrecord.logrequest(req)
    if isinstance(server, SharedLoginAppServer):
      return server.handle(req, pathwords[1:], argdict, sharedsession=session)
    else:
      return server.handle(req, pathwords[1:], argdict)

  def handle(self, req, pathwords, argdict):
    """handles the request and returns a page object in response"""
    if self.shoulddefer(pathwords):
      if pathwords[0] in self.instances:
        session = self.sessioncache.getsession(req, argdict, self)
        if session.isopen:
          return self.handledefer(req, pathwords, session, argdict)
      else:
        return None
    else:
      argdict = self.processargs(argdict)
      session = self.getsession(req, argdict)
      if session.isopen:
        session.pagecount += 1
        session.remote_ip = self.getremoteip(req)
        session.localaddr = self.getlocaladdr(req)
        return self.getpage(pathwords, session, argdict)
      else:
        if self.ishtmlpage(pathwords):
          return self.getloginpage(session, argdict, languagenames=self.languagenames)

  def getindexpage(self, session):
    """returns a page for the index..."""
    if session.parentsessionname == "":
      logout = widgets.Link('index.htm?islogout=true', session.localize('Logout'))
    else:
      logout = widgets.Link('index.htm?islogout=true&exitapp=true', session.localize('Exit'))
    status = widgets.Paragraph([logout, " ", session.status])
    links = [widgets.Paragraph(widgets.Link(instance+"/", instance)) for instance in self.instances]
    return widgets.Page(session.localize("Select Application"), [status, links])

  def getsession(self, req, argdict):
    """checks login. if valid, return the requested page, otherwise return the login page"""
    islogin = argdict.get("islogin",0)
    session = super(SharedLoginMultiAppServer, self).getsession(req, argdict)
    # remember the password so we can give it to other sessions...
    if islogin and session.isopen:
      session.password = argdict.get("password","")
    elif not hasattr(session, 'password'):
      session.password = ""
    # let the request know the session (for logging purposes)
    req.session = session
    return session

class SharedLoginMiddleAppServer(SharedLoginAppServer, SharedLoginMultiAppServer):
  """a server that can be a parent *and* a child"""
  def handle(self, req, pathwords, argdict, sharedsession=None):
    """handles the request and returns a page object in response"""
    if self.shoulddefer(pathwords):
      # can't do self.processargs otherwise the other server won't be able to...
      if pathwords[0] in self.instances:
        session = self.sessioncache.getsession(req, argdict, self)
        return self.handledefer(req, pathwords, argdict, session)
      else:
        return None
    else:
      argdict = self.processargs(argdict)
      exitapp = argdict.get('exitapp', 0)
      session = self.getsession(req, argdict, sharedsession)
      if exitapp:
        if 'Set-Cookie' in req.headers_out:
          redirectpage = widgets.Page("Redirecting to index...")
          return Redirect("../index.html", withpage=redirectpage)
        return Redirect("../index.html")
      if session.isopen:
        session.pagecount += 1
        session.remote_ip = self.getremoteip(req)
        session.localaddr = self.getlocaladdr(req)
        return self.getpage(pathwords, session, argdict)
      else:
        if self.isloginpage(pathwords):
          return self.getloginpage(session, argdict, languagenames=self.languagenames)

