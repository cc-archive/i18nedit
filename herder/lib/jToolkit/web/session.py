# -*- coding: utf-8 -*-
"""this is a module which handles login sessions using cookies"""

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

from jToolkit.data import dates
from jToolkit import prefs
import md5
import Cookie
import warnings

def md5hexdigest(text):
  if isinstance(text, unicode): text = text.encode('utf8')
  return md5.md5(text).hexdigest()

class SessionCache(dict):
  def __init__(self, sessionclass = None, sessioncookiename = None):
    """constructs a SessionCache that uses the given sessionclass for session objects"""
    if sessionclass is None:
      sessionclass = Session
    self.sessionclass = sessionclass
    if sessioncookiename is None:
      sessioncookiename = 'session'
    self.sessioncookiename = sessioncookiename
    self.invalidsessionstrings = {}

  def createsession(self, server, sessionstring = None):
    """creates a new session object"""
    return self.sessionclass(self, server, sessionstring)

  def purgestalesessions(self):
    """takes any sessions that haven't been used for a while out of the cache"""
    stalekeys = []
    for key, session in self.iteritems():
      if not session.isfresh():
        # only remove it later otherwise we confuse the loop
        stalekeys.append(key)
    for key in stalekeys:
      # we don't close the session as it is still valid and might be reused
      del self[key]
  
  def newsession(self, req, argdict, server):
    """returns a new session from the login parameters"""
    # gets the old session, if there is one
    oldsessionstring = self.getsessioncookie(req, argdict, server)
    oldsession = self.get(oldsessionstring)
    # get the username and password from the form
    username = argdict.get('username','')
    password = argdict.get('password','')
    # TODO: add language in other similar functions...
    # print "accept-language", req.headers_in.getheader('Accept-Language')
    language = argdict.get('language','')
    # create a new session
    timestamp = dates.formatdate(dates.currentdate(), '%Y%m%d%H%M%S')
    session = self.createsession(server)
    session.create(username,password,timestamp,language)
    if session.isopen:
      if oldsession is not None:
        oldsession.close(req)
      session.updatecookie(req, server)
    return session
  
  def confirmsession(self, req, argdict, server):
    """confirms login for the current session with new username & password"""
    # get the username and password from the form
    username = argdict.get('username','')
    password = argdict.get('password','')
    session = self.getsession(req, argdict, server)
    timestamp = dates.formatdate(dates.currentdate(), '%Y%m%d%H%M%S')
    session.confirmlogin(req, username, password, timestamp)
    return session
  
  def closesession(self, req, argdict, server):
    """closes the current session"""
    # remove the session from the list of open sessions
    session = self.getsession(req, argdict, server)
    session.close(req)
    return session
  
  def getsession(self, req, argdict, server):
    """gets the current session"""
    # retrieve current session info
    sessionstring = self.getsessioncookie(req, argdict, server)
    if sessionstring in self.invalidsessionstrings:
      session = self.createsession(server, "-")
    else:
      session = self.get(sessionstring)
      if session is None:
        session = self.createsession(server, sessionstring)
    session.checkstatus(req, argdict)
    return session

  def getcookie(self, req):
    """Reads in any cookie info from the request"""
    try:
      cookiestring = req.headers_in["Cookie"]
    except:
      cookiestring = {}
    cookie = Cookie.SimpleCookie()
    cookie.load(cookiestring)
    cookiedict = {}
    for key, morsel in cookie.iteritems():
      cookiedict[key] = morsel.value.decode('utf8')
    return cookiedict
  
  def setcookie(self, req, cookiedict):
    """Puts the bits from the cookiedict into Morsels, sets the req cookie"""
    # construct the cookie from the cookiedict
    cookie = Cookie.SimpleCookie()
    for key, value in cookiedict.iteritems():
      if isinstance(value, unicode): value = value.encode('utf8')
      if isinstance(key, unicode): key = key.encode('utf8')
      cookie[key] = value
    # add the cookie headers to req.headers_out
    for key, morsel in cookie.iteritems():
      req.headers_out.add('Set-Cookie', morsel.OutputString())

  def getsessioncookiename(self, server):
    """returns the actual name used for the session cookie for the given server"""
    return server.name + '-' + self.sessioncookiename

  def getsessioncookie(self, req, argdict, server):
    """returns the session cookie value"""
    cookiedict = self.getcookie(req)
    sessioncookiename = self.getsessioncookiename(server)
    sessionparam = argdict.get(sessioncookiename, None)
    sessioncookie = cookiedict.get(sessioncookiename, None)
    if sessionparam and not sessioncookie:
      sessioncookie = sessionparam
      self.setsessioncookie(req, server, sessioncookie)
    if not sessioncookie:
      sessioncookie = "-"
    return sessioncookie

  def setsessioncookie(self, req, server, sessionstring):
    """sets the session cookie value"""
    cookiedict = {self.getsessioncookiename(server): sessionstring}
    self.setcookie(req, cookiedict)

class Session(object):
  """represents a user session"""
  def __init__(self, sessioncache, server, sessionstring = None):
    self.sessioncache = sessioncache
    self.server = server
    self.instance = server.instance
    self.parentsessionname = ""
    self.childsessions = {}
    self.isvalid = 0
    self.markedinvalid = 0
    self.isopen = 0
    self.pagecount = 0
    self.userdict = {}
    self.updatelastused()
    self.status = ""
    self.setlanguage(None)
    self.username = None
    # allow the server to add any attributes it requires
    server.initsession(self)
    self.setsessionstring(sessionstring)

  def md5hexdigest(self, text):
    """allows the md5hexdigest function to be access through the session"""
    return md5hexdigest(text)

  def getstatus(self):
    """get a string describing the status of the session"""
    return self.status

  def open(self):
    """tries to open the given session, returns success"""
    self.isopen = 0
    if self.isvalid:
      self.sessioncache.purgestalesessions()
      sessionstring = self.getsessionstring()
      self.sessioncache[sessionstring] = self
      self.isopen = sessionstring in self.sessioncache
      if self.isopen:
        self.status = self.localize("logged in as <b>%s</b>") % self.username
      else:
        self.status = self.localize("couldn't add new session")
    return self.isopen

  def isfresh(self):
    """returns whether this session has been used relatively recently"""
    # session is fresh if it's been used in the last ten minutes...
    freshinterval = dates.seconds(10*60)
    delay = dates.currentdate() - self.lastused
    return delay <= freshinterval

  def close(self, req):
    """removes the current session from the list of valid sessions..."""
    # note: if somebody sneakily remembers the session cookie it is still valid after logout
    # (though it is reset on the user's browser)
    if self.isopen:
      sessionstring = self.getsessionstring()
      if sessionstring in self.sessioncache:
        del self.sessioncache[sessionstring] 
      self.isopen = 0
    # set the session cookie to expired, fail authorization
    self.updatecookie(req, self.server)
    self.status = self.localize("logged out")
    # invalidate child sessions...
    # note that if Apache is restarted, the cookies will still be around, and the invalidation will be forgotten...
    # alternative would be to store cookies in the root path
    for childname in self.childsessions:
      self.invalidatechild(childname)

  def invalidatechild(self, childname):
    """logs out of a child session"""
    childsession = self.childsessions.get(childname, 0)
    if childsession:
      childsession.markinvalid()

  def updatelastused(self):
    """updates that the session has been used"""
    self.lastused = dates.currentdate()

  def checkstatus(self, req, argdict):
    """check the login status (auto logoff etc)"""
    if self.isopen:
      self.status = self.localize("connected")
      self.updatelastused()

  def getlogintime(self):
    """returns the login time based on the timestamp"""
    return dates.nosepdateparser.parse(self.timestamp)

  def getsessionstring(self):
    """creates the full session string using the sessionid"""
    sessionstring = self.timestamp+':'+self.sessionid
    return sessionstring

  def setsessionstring(self, sessionstring):
    """sets the session string for this session"""
    if sessionstring is not None:
      # split up the sessionstring into components
      if sessionstring.count(':') >= 1:
        self.timestamp,self.sessionid = sessionstring.split(':',1)
        # make sure this is valid, and open it...
        self.validate()
        self.open()

  def updatecookie(self, req, server):
    """update session string in cookie in req to reflect whether session is open"""
    if self.isopen:
      self.sessioncache.setsessioncookie(req, server, self.getsessionstring())
    else:
      self.sessioncache.setsessioncookie(req, server, '-')

  def markinvalid(self):
    """marks a session as invalid"""
    sessionstring = self.getsessionstring()
    if sessionstring in self.sessioncache:
      del self.sessioncache[sessionstring]
    self.sessioncache.invalidsessionstrings[self.getsessionstring()] = 1
    self.markedinvalid = self.localize("exited parent session")
    self.isopen = 0

  def validate(self):
    """checks if this session is valid"""
    self.isvalid = 1
    return 1

  def checksessionid(self):
    """returns the hex sessionid for the session, using the password"""
    correctsessionid = self.timestamp+':'+md5hexdigest(self.timestamp)
    return correctsessionid == self.sessionid

  def setlanguage(self, language):
    """sets the language for the session"""
    if language is None:
      self.language = self.server.defaultlanguage
    else:
      self.language = language
    self.translation = self.server.gettranslation(self.language)

  def localize(self, message, *variables):
    """returns the localized form of a message, falls back to original if failure with variables"""
    # this is used when no session is available
    if variables:
      # TODO: this is a hack to handle the old-style passing of a list of variables
      # remove below after the next jToolkit release after 0.7.7
      if len(variables) == 1 and isinstance(variables[0], (tuple, list)):
        warnings.warn("list/tuple of variables passed into localize - deprecated, rather pass arguments")
        variables = variables[0]
      # remove above after the next jToolkit release after 0.7.7
      try:
        return self.translation.ugettext(message) % variables
      except:
        return message % variables
    else:
      return self.translation.ugettext(message)

  def nlocalize(self, singular, plural, n, *variables):
    """returns the localized form of a plural message, falls back to original if failure with variables"""
    # this is used when no session is available
    if variables:
      # TODO: this is a hack to handle the old-style passing of a list of variables
      # remove below after the next jToolkit release after 0.7.7
      if len(variables) == 1 and isinstance(variables[0], (tuple, list)):
        warnings.warn("list/tuple of variables passed into nlocalize - deprecated, rather pass arguments")
        variables = variables[0]
      # remove above after the next jToolkit release after 0.7.7
      try:
        return self.translation.ungettext(singular, plural, n) % variables
      except:
        if n != 1:
          return plural % variables
        else:
          return singular % variables
    else:
      return self.translation.ungettext(singular, plural, n)

userprefsfiles = {}

class LoginChecker:
  """An interface that allows checking of login details (using prefs file)"""
  def __init__(self, session, instance):
    self.session = session
    if hasattr(instance, "userprefs"):
      if instance.userprefs in userprefsfiles:
        self.users = userprefsfiles[instance.userprefs]
      else:
        self.users = prefs.PrefsParser()
        self.users.parsefile(instance.userprefs)
        userprefsfiles[instance.userprefs] = self.users
    elif hasattr(instance, "users"):
      self.users = instance.users
    else:
      raise IndexError, self.session.localize("need to define the users or userprefs entry on the server config")

  def getmd5password(self, username=None):
    """retrieves the md5 hash of the password for this user, or another if another is given..."""
    if username is None:
      username = self.session.username
    if not self.userexists(username):
      raise IndexError, self.session.localize("user does not exist (%r)") % username
    md5password = self.users.__getattr__(username).passwdhash
    return md5password

  def userexists(self, username=None):
    """checks whether user username exists"""
    if username is None:
      username = self.session.username
    return self.users.__hasattr__(username)
  
class LoginSession(Session):
  """A session that allows login"""
  def __init__(self, sessioncache, server, sessionstring = None, loginchecker = None):
    if loginchecker is None:
      loginchecker = LoginChecker(self, server.instance)
    self.loginchecker = loginchecker
    super(LoginSession, self).__init__(sessioncache, server, sessionstring)

  def open(self):
    """tries to open the given session, returns success"""
    self.isopen = 0
    super(LoginSession, self).open()
    if self.isopen:
      self.status = self.localize("logged in as <b>%s</b>") % self.username
    return self.isopen

  def checkstatus(self, req, argdict):
    """check the login status (auto logoff etc)"""
    if self.isopen:
      self.status = self.localize("logged in as <b>%s</b>") % (self.username)
      self.updatelastused()

  def validate(self):
    """checks if this session is valid"""
    self.isvalid = 0
    if self.markedinvalid:
      self.status = self.markedinvalid
      return self.isvalid
    if self.loginchecker.userexists():
      self.isvalid = self.checksessionid()
    if not self.isvalid:
      self.status = self.localize("invalid username and/or password")
    return self.isvalid

  def getsessionid(self, password):
    """returns the hex sessionid for the session, using the password"""
    md5password = md5hexdigest(password)
    return md5hexdigest(self.username+':'+self.timestamp+':'+md5password+':'+self.instance.sessionkey+':'+self.server.name)

  def checksessionid(self):
    """returns the hex sessionid for the session, using the password"""
    correctmd5password = self.loginchecker.getmd5password()
    sessiontest = self.username+':'+self.timestamp+':'+correctmd5password+':'+self.instance.sessionkey+':'+self.server.name
    correctsessionid = md5hexdigest(sessiontest)
    return correctsessionid == self.sessionid

  def getsessionstring(self):
    """creates the full session string using the sessionid"""
    sessionstring = self.username+':'+self.timestamp+':'+self.sessionid+':'+self.parentsessionname
    return sessionstring

  def setsessionstring(self, sessionstring):
    """sets the session string for this session"""
    # split up the sessionstring into components
    if sessionstring is not None:
      # split up the sessionstring into components
      if sessionstring.count(':') >= 3:
        self.username,self.timestamp,self.sessionid,self.parentsessionname = sessionstring.split(':',3)
        # make sure this is valid, and open it...
        self.validate()
        self.open()

  def create(self,username,password,timestamp,language):
    """initializes the session with the parameters"""
    self.username, password, self.timestamp = username, password, timestamp
    self.setlanguage(language)
    self.sessionid = self.getsessionid(password)
    self.validate()
    self.open()

  def sharelogindetails(self, req, othersession):
    """shares this session's login details with othersession"""
    username = self.username
    # this expects that self.password exist ... see SharedLoginMultiAppServer.checklogin...
    password = getattr(self, 'password', '')
    language = self.language
    timestamp = dates.formatdate(dates.currentdate(), '%Y%m%d%H%M%S')
    # currently assumes we do not need to close the other session
    otherusername = getattr(othersession, 'username', '')
    othersession.parentsessionname = self.server.name
    othersession.create(username, password, timestamp, language)
    if othersession.isopen:
      othersession.updatecookie(req, othersession.server)
      self.childsessions[othersession.server.name] = othersession
    else:
      othersession.close(req)
      othersession.parentsessionname = ""
      othersession.username = otherusername
      othersession.status = ""

  def confirmlogin(self, req, username, password, timestamp):
    """validates a username and password for an already-established session"""
    username, password = username, password
    if not self.isvalid:
      # create a new session
      self.create(username, password, timestamp, self.language)
      if self.isopen:
        self.updatecookie(req, self.server)
    else:
      # validate the old session...
      if username != self.username:
        self.close(req)
        self.status = self.localize("failed login confirmation")
      self.sessionid = self.getsessionid(password)
      if not self.validate():
        self.close(req)
        self.status = self.localize("failed login confirmation")

class DBLoginChecker:
  """An interface that allows checking of login details (using a database)"""
  # note that usernames are case insensitive for this checker
  def __init__(self, session, db):
    self.session = session
    self.db = db

  def getmd5password(self, username=None):
    """retrieves the md5 hash of the password for this user, or another if another is given..."""
    if username is None:
      username = self.session.username.lower()
    else:
      username = username.lower()
    if not self.userexists(username):
      raise IndexError, self.session.localize("user does not exist (%r)") % username
    sql = "select passwdhash from users where %s(username)='%s'" % (self.db.dblowerfn(), username)
    return self.db.singlevalue(sql)

  def userexists(self, username=None):
    """checks whether user username exists"""
    if username is None:
      username = self.session.username
    sql = "select count(*) from users where %s(username)='%s'" % \
      (self.db.dblowerfn(), username.lower())
    count = self.db.singlevalue(sql)
    return count > 0

class DBLoginSession(LoginSession):
  """A session that allows login based on a database"""
  def __init__(self, sessioncache, server, sessionstring = None):
    loginchecker = DBLoginChecker(self, server.db)
    super(DBLoginSession, self).__init__(sessioncache, server, sessionstring, loginchecker)

