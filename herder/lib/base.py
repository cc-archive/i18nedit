"""The base Controller API

Provides the BaseController class for subclassing, and other objects
utilized by Controllers.
"""
from pylons import c, cache, config, g, request, response, session
from pylons.controllers import WSGIController
from pylons.controllers.util import abort, etag_cache, redirect_to
from pylons.decorators import jsonify, validate
from pylons.i18n import _, ungettext, N_
from pylons.templating import render

from herder.lib.decorators import with_user_info

import herder.lib.helpers as h
import herder.model as model

class BaseController(WSGIController):

    def _get_roles(self, environ):
        """Return a list of roles for the current context."""

        authkit = environ.get('authkit.users')
        user = environ.get('REMOTE_USER', None)
        
        if user is None:
            # not logged in, no roles
            return []

        return authkit.user_roles(user)

    def _actions(self, environ):
        """Return a sequence of two-tuples describing the actions for this
        view (taking into account the logged in user, roles, etc)."""

        actions = [
            ('/domain/all/list', 'Translation Domains'),
            ]

        if 'administrator' in self._get_roles(environ):
            actions.append( ('/admin', 'Administration') )

        return actions

    @with_user_info
    def __call__(self, environ, start_response):
        """Invoke the Controller"""

        # bind the actions method into the context
        c.roles = self._get_roles(environ)
        c.actions = self._actions(environ)

        # add actions
        if c.remote_user:
            c.actions.insert(0, ('/account/profile', c.remote_user))
            c.actions.append( ('/account/logout', 'Logout') )
        else:
            c.actions.append( ('/account/login', 'Login') )


        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        return WSGIController.__call__(self, environ, start_response)

# Include the '_' function in the public names
__all__ = [__name for __name in locals().keys() if not __name.startswith('_') \
           or __name == '_']
